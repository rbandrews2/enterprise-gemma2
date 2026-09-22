"""Local timekeeping workflow; storage isolated from any Supabase account."""
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from fastapi import HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

TASKS = {"job_site": "Job Site", "setup": "Setup", "teardown": "Teardown", "travel": "Travel Time", "other": "Other"}

class ClockCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: UUID
    action: Literal["clock_in", "clock_out", "break_start", "break_end", "switch_task"]
    shift_id: str | None = Field(default=None, max_length=100)
    expected_version: int = Field(default=0, ge=0, strict=True)
    task: Literal["job_site", "setup", "teardown", "travel", "other"] = "job_site"
    order_id: str | None = Field(default=None, max_length=100)
    note: str = Field(default="", max_length=1000)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def duration(start, end):
    return max(0, int((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()))


def present(row, now):
    shift = json.loads(row["payload"])
    end = shift["clock_out"] or now
    total = duration(shift["clock_in"], end)
    breaks = sum(duration(b["start"], b["end"] or end) for b in shift["breaks"])
    return {**shift, "id": row["id"], "employee_id": row["employee_id"], "version": row["version"],
            "status": "closed" if shift["clock_out"] else "on_break" if shift["breaks"] and not shift["breaks"][-1]["end"] else "working",
            "elapsed_seconds": total, "break_seconds": breaks, "work_seconds": max(0, total-breaks),
            "payroll_calculated": False}


def initialize(connect):
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS preview_shifts (
            id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, employee_id TEXT NOT NULL,
            version INTEGER NOT NULL, active INTEGER NOT NULL, payload TEXT NOT NULL)""")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_active_shift ON preview_shifts(organization_id,employee_id) WHERE active=1")
        conn.execute("""CREATE TABLE IF NOT EXISTS preview_clock_events (
            organization_id TEXT NOT NULL, employee_id TEXT NOT NULL, request_id TEXT NOT NULL,
            shift_id TEXT NOT NULL, occurred_at TEXT NOT NULL, command TEXT NOT NULL, response TEXT NOT NULL,
            PRIMARY KEY(organization_id,employee_id,request_id))""")


def summary(connect, selected):
    now = utc_now()
    with connect() as conn:
        row = conn.execute("SELECT * FROM preview_shifts WHERE organization_id=? AND employee_id=? AND active=1",
                           (selected["organization_id"], selected["id"])).fetchone()
    item = present(row, now) if row else None
    return {"status": item["status"] if item else "off_clock", "shift_id": item["id"] if item else None,
            "version": item["version"] if item else None, "work_seconds": item["work_seconds"] if item else 0,
            "break_seconds": item["break_seconds"] if item else 0,
            "task": item["task"] if item else None, "as_of": now, "payroll_calculated": False}


def register(app, connect, actor, permitted_order):
    initialize(connect)

    @app.get("/api/time/status")
    def status(request: Request):
        selected = actor(request)
        now = utc_now()
        with connect() as conn:
            row = conn.execute("SELECT * FROM preview_shifts WHERE organization_id=? AND employee_id=? AND active=1",
                               (selected["organization_id"], selected["id"])).fetchone()
        return {"active": present(row, now) if row else None, "server_time": now, "tasks": TASKS}

    @app.get("/api/time/entries")
    def entries(request: Request, team: bool = False, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50)):
        selected = actor(request)
        if team and selected["role"] != "admin":
            raise HTTPException(403, "Team time history requires admin access")
        where = "organization_id=?"
        values = [selected["organization_id"]]
        if not team:
            where += " AND employee_id=?"
            values.append(selected["id"])
        now = utc_now()
        with connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM preview_shifts WHERE " + where, values).fetchone()[0]
            rows = conn.execute("SELECT * FROM preview_shifts WHERE " + where + " ORDER BY json_extract(payload,'$.clock_in') DESC,id DESC LIMIT ? OFFSET ?", [*values,limit,offset]).fetchall()
        return {"items": [present(row, now) for row in rows], "total": count, "offset": offset, "limit": limit, "server_time": now}

    @app.post("/api/time/commands")
    def command(payload: ClockCommand, request: Request):
        selected = actor(request)
        org, employee = selected["organization_id"], selected["id"]
        packed = json.dumps(payload.model_dump(mode="json"), sort_keys=True)
        with connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            prior = conn.execute("SELECT command,response FROM preview_clock_events WHERE organization_id=? AND employee_id=? AND request_id=?", (org,employee,str(payload.request_id))).fetchone()
            if prior:
                if prior["command"] != packed:
                    raise HTTPException(409, "Retry ID was already used for a different clock action")
                return json.loads(prior["response"])
            row = conn.execute("SELECT * FROM preview_shifts WHERE organization_id=? AND employee_id=? AND active=1", (org,employee)).fetchone()
            now = utc_now()
            if payload.action == "clock_in":
                if row or payload.shift_id or payload.expected_version != 0:
                    raise HTTPException(409, "An active shift already exists or the starting state is invalid. Refresh the clock.")
                order_title = None
                if payload.order_id:
                    order = permitted_order(conn,payload.order_id,selected)
                    order_title = json.loads(order["payload"])["title"]
                shift_id, version = str(uuid4()), 1
                shift = {"clock_in": now, "clock_out": None, "task": payload.task, "order_id": payload.order_id,
                         "order_title": order_title, "note": payload.note, "breaks": [],
                         "segments": [{"task": payload.task, "start": now, "end": None}]}
                conn.execute("INSERT INTO preview_shifts VALUES (?,?,?,?,?,?)", (shift_id,org,employee,version,1,json.dumps(shift)))
            else:
                if not row or row["id"] != payload.shift_id or row["version"] != payload.expected_version:
                    raise HTTPException(409, "Clock changed. Refresh before trying again.")
                shift_id, version = row["id"], row["version"]+1
                shift = json.loads(row["payload"])
                last_time = conn.execute("SELECT MAX(occurred_at) FROM preview_clock_events WHERE shift_id=?", (shift_id,)).fetchone()[0]
                if last_time and now < last_time:
                    raise HTTPException(409, "Server clock moved backwards. Retry after the clock is corrected.")
                on_break = bool(shift["breaks"] and shift["breaks"][-1]["end"] is None)
                if payload.action == "break_start":
                    if on_break: raise HTTPException(409, "Already on break")
                    shift["segments"][-1]["end"] = now
                    shift["breaks"].append({"start":now,"end":None})
                elif payload.action == "break_end":
                    if not on_break: raise HTTPException(409, "No break is active")
                    shift["breaks"][-1]["end"] = now
                    shift["segments"].append({"task":shift["task"],"start":now,"end":None})
                elif payload.action == "switch_task":
                    if on_break: raise HTTPException(409, "End your break before switching tasks")
                    if payload.task == shift["task"]: raise HTTPException(409, "Choose a different task")
                    shift["segments"][-1]["end"] = now
                    shift["task"] = payload.task
                    shift["segments"].append({"task":payload.task,"start":now,"end":None})
                else:
                    shift["clock_out"] = now
                    if on_break: shift["breaks"][-1]["end"] = now
                    else: shift["segments"][-1]["end"] = now
                conn.execute("UPDATE preview_shifts SET version=?,active=?,payload=? WHERE id=?", (version,int(shift["clock_out"] is None),json.dumps(shift),shift_id))
            saved = conn.execute("SELECT * FROM preview_shifts WHERE id=?", (shift_id,)).fetchone()
            response = {"entry":present(saved,now),"server_time":now,"saved":True}
            conn.execute("INSERT INTO preview_clock_events VALUES (?,?,?,?,?,?,?)", (org,employee,str(payload.request_id),shift_id,now,packed,json.dumps(response)))
            return response
