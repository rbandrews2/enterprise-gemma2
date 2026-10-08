"""Timekeeping workflow; storage isolated from any Supabase account.

Clock commands are timestamped at server receipt. Admin corrections and manual
entries are audited, idempotent and version-checked. Offline submissions are
device-timestamped evidence held for admin review; they never change a shift
on their own and are never replayed as clock commands.
"""
import json
import csv
import hashlib
import io
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from fastapi import HTTPException, Query, Request
from fastapi.responses import FileResponse, Response
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

TASKS = {"job_site": "Job Site", "setup": "Setup", "teardown": "Teardown", "travel": "Travel Time", "other": "Other"}
Task = Literal["job_site", "setup", "teardown", "travel", "other"]
Action = Literal["clock_in", "clock_out", "break_start", "break_end", "switch_task"]
STATIC = Path(__file__).with_name("static")
MAX_SHIFT = timedelta(hours=48)
FUTURE_TOLERANCE = timedelta(minutes=2)
OFFLINE_WINDOW = timedelta(days=14)
DUPLICATE_WINDOW = timedelta(minutes=15)
EXPORT_LIMIT = 1000

class ClockCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: UUID
    action: Action
    shift_id: str | None = Field(default=None, max_length=100)
    expected_version: int = Field(default=0, ge=0, strict=True)
    task: Task = "job_site"
    order_id: str | None = Field(default=None, max_length=100)
    note: str = Field(default="", max_length=1000)


class Interval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: AwareDatetime
    end: AwareDatetime


class TaskInterval(Interval):
    task: Task


class ShiftTimes(BaseModel):
    """Complete corrected times; the server validates the whole shift, not a diff."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: UUID
    reason: str = Field(min_length=5, max_length=500)
    clock_in: AwareDatetime
    clock_out: AwareDatetime
    breaks: list[Interval] = Field(default_factory=list, max_length=50)
    segments: list[TaskInterval] = Field(min_length=1, max_length=100)
    order_id: str | None = Field(default=None, max_length=100)
    resolves: list[UUID] = Field(default_factory=list, max_length=20)


class Correction(ShiftTimes):
    expected_version: int = Field(ge=1, strict=True)


class ManualEntry(ShiftTimes):
    employee_id: str = Field(min_length=1, max_length=200)


class OfflineDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: UUID
    action: Action
    task: Task | None = None
    order_id: str | None = Field(default=None, max_length=100)
    note: str = Field(default="", max_length=1000)
    captured_at: AwareDatetime  # device clock when the draft was recorded
    stated_at: AwareDatetime | None = None  # optional earlier time stated by the user, device clock
    known_shift_id: str | None = Field(default=None, max_length=100)
    known_version: int | None = Field(default=None, ge=0, strict=True)


class OfflineBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    device_submitted_at: AwareDatetime
    drafts: list[OfflineDraft] = Field(min_length=1, max_length=50)


class Resolution(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    decision: Literal["rejected", "duplicate"]
    reason: str = Field(min_length=3, max_length=500)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def iso(value):
    return value.astimezone(timezone.utc).isoformat()


def parse(value):
    return datetime.fromisoformat(value)


def duration(start, end):
    return max(0, int((parse(end) - parse(start)).total_seconds()))


def basis(shift):
    if shift.get("source") == "admin_entry":
        return "admin_entered"
    return "admin_corrected" if shift.get("correction_count") else "server_recorded"


def totals(shift, now):
    end = shift["clock_out"] or now
    total = duration(shift["clock_in"], end)
    breaks = sum(duration(b["start"], b["end"] or end) for b in shift["breaks"])
    return {"elapsed_seconds": total, "break_seconds": breaks, "work_seconds": max(0, total-breaks)}


def present(row, now):
    shift = json.loads(row["payload"])
    return {**shift, "id": row["id"], "employee_id": row["employee_id"], "version": row["version"],
            "status": "closed" if shift["clock_out"] else "on_break" if shift["breaks"] and not shift["breaks"][-1]["end"] else "working",
            **totals(shift, now), "record_basis": basis(shift), "correction_count": shift.get("correction_count", 0),
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
        # Append-only audit of admin changes; the API never updates or deletes these rows.
        conn.execute("""CREATE TABLE IF NOT EXISTS time_corrections (
            id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, shift_id TEXT NOT NULL, employee_id TEXT NOT NULL,
            admin_id TEXT NOT NULL, request_id TEXT NOT NULL, request_hash TEXT NOT NULL, kind TEXT NOT NULL,
            occurred_at TEXT NOT NULL, reason TEXT NOT NULL, from_version INTEGER NOT NULL, to_version INTEGER NOT NULL,
            before_payload TEXT, after_payload TEXT NOT NULL, resolves TEXT NOT NULL, response TEXT NOT NULL,
            UNIQUE(organization_id,admin_id,request_id))""")
        conn.execute("CREATE INDEX IF NOT EXISTS time_corrections_shift ON time_corrections(organization_id,shift_id)")
        conn.execute("""CREATE TABLE IF NOT EXISTS time_offline_submissions (
            id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, employee_id TEXT NOT NULL,
            request_id TEXT NOT NULL, request_hash TEXT NOT NULL, action TEXT NOT NULL, payload TEXT NOT NULL,
            captured_at TEXT NOT NULL, stated_at TEXT, device_submitted_at TEXT NOT NULL, received_at TEXT NOT NULL,
            device_offset_seconds INTEGER NOT NULL, estimated_at TEXT NOT NULL, status TEXT NOT NULL,
            resolved_by TEXT, resolved_at TEXT, resolution_reason TEXT, resolution_ref TEXT, resolved_shift_id TEXT,
            UNIQUE(organization_id,employee_id,request_id))""")
        conn.execute("CREATE INDEX IF NOT EXISTS time_offline_status ON time_offline_submissions(organization_id,status,estimated_at)")


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


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def require_admin(selected, what):
    if selected["role"] != "admin":
        raise HTTPException(403, what + " requires admin access")


def validate_times(body: ShiftTimes, now):
    """Return normalized clock-in/out, breaks and task intervals, or raise 422 with the specific problem."""
    start, end = body.clock_in, body.clock_out
    if end <= start:
        raise HTTPException(422, "Clock-out must be after clock-in")
    if end - start > MAX_SHIFT:
        raise HTTPException(422, "A shift cannot exceed 48 hours; enter separate shifts")
    if end > parse(now) + FUTURE_TOLERANCE:
        raise HTTPException(422, "Corrected times cannot be in the future")
    def ordered(items, label):
        items = sorted(items, key=lambda i: i.start)
        for item in items:
            if item.end <= item.start:
                raise HTTPException(422, f"Each {label} must end after it starts")
            if item.start < start or item.end > end:
                raise HTTPException(422, f"Each {label} must fall within the shift")
        for before, after in zip(items, items[1:]):
            if after.start < before.end:
                raise HTTPException(422, f"{label.capitalize()}s must not overlap")
        return items
    breaks, segments = ordered(body.breaks, "break"), ordered(body.segments, "task interval")
    for segment in segments:
        if any(segment.start < b.end and b.start < segment.end for b in breaks):
            raise HTTPException(422, "Task intervals must not overlap breaks")
    return (iso(start), iso(end), [{"start": iso(b.start), "end": iso(b.end)} for b in breaks],
            [{"task": s.task, "start": iso(s.start), "end": iso(s.end)} for s in segments])


def register(app, connect, actor, permitted_order, roster=None):
    initialize(connect)

    def members(selected):
        people = roster(selected) if roster else {selected["id"]: selected}
        return {k: v for k, v in people.items() if v.get("organization_id", selected["organization_id"]) == selected["organization_id"]}

    def names(selected):
        return {k: v.get("name") or k for k, v in members(selected).items()}

    def named(item, people):
        return {**item, "employee_name": people.get(item["employee_id"], item["employee_id"])}

    def scope(selected, team, employee_id, start_date, end_date):
        if employee_id and employee_id != selected["id"]:
            require_admin(selected, "Another employee's time history")
        if team:
            require_admin(selected, "Team time history")
        where, values = "organization_id=?", [selected["organization_id"]]
        if employee_id or not team:
            where += " AND employee_id=?"
            values.append(employee_id or selected["id"])
        if start_date and end_date and end_date < start_date:
            raise HTTPException(422, "End date must not precede start date")
        if start_date:
            where += " AND substr(json_extract(payload,'$.clock_in'),1,10)>=?"
            values.append(start_date.isoformat())
        if end_date:
            where += " AND substr(json_extract(payload,'$.clock_in'),1,10)<=?"
            values.append(end_date.isoformat())
        return where, values

    def visible_shift(conn, selected, shift_id):
        row = conn.execute("SELECT * FROM preview_shifts WHERE id=? AND organization_id=?", (shift_id, selected["organization_id"])).fetchone()
        if not row or (selected["role"] != "admin" and row["employee_id"] != selected["id"]):
            raise HTTPException(404, "Time entry not found")
        return row

    def submission(row, people):
        draft = json.loads(row["payload"])
        return {"id": row["id"], "employee_id": row["employee_id"], "employee_name": people.get(row["employee_id"], row["employee_id"]),
                "request_id": row["request_id"], "action": row["action"], "task": draft.get("task"), "order_id": draft.get("order_id"),
                "note": draft.get("note", ""), "captured_at": row["captured_at"], "stated_at": row["stated_at"],
                "device_submitted_at": row["device_submitted_at"], "received_at": row["received_at"],
                "device_offset_seconds": row["device_offset_seconds"], "estimated_at": row["estimated_at"],
                "known_shift_id": draft.get("known_shift_id"), "known_version": draft.get("known_version"),
                "status": row["status"], "resolved_by": row["resolved_by"], "resolved_at": row["resolved_at"],
                "resolution_reason": row["resolution_reason"], "resolved_shift_id": row["resolved_shift_id"],
                "time_basis": "device_estimate_unverified"}

    def duplicates(conn, row):
        """Verified or admin records near the estimated time that may already cover this draft."""
        estimated = parse(row["estimated_at"])
        low, high = iso(estimated - DUPLICATE_WINDOW), iso(estimated + DUPLICATE_WINDOW)
        found = [{"kind": "server_receipt", "occurred_at": e["occurred_at"], "shift_id": e["shift_id"]}
                 for e in conn.execute("SELECT occurred_at,shift_id,command FROM preview_clock_events WHERE organization_id=? AND employee_id=? AND occurred_at>=? AND occurred_at<=?",
                                       (row["organization_id"], row["employee_id"], low, high)).fetchall()
                 if json.loads(e["command"])["action"] == row["action"]]
        if row["action"] in ("clock_in", "clock_out"):
            field = "$." + row["action"]
            for s in conn.execute("SELECT id,payload FROM preview_shifts WHERE organization_id=? AND employee_id=? AND json_extract(payload,?)>=? AND json_extract(payload,?)<=?",
                                  (row["organization_id"], row["employee_id"], field, low, field, high)).fetchall():
                shift = json.loads(s["payload"])
                if basis(shift) != "server_recorded":
                    found.append({"kind": basis(shift), "occurred_at": shift[row["action"]], "shift_id": s["id"]})
        return found

    @app.get("/timeclock-review.js")
    def review_script():
        return FileResponse(STATIC / "timeclock-review.js", media_type="text/javascript")

    @app.get("/timeclock.css")
    def clock_styles():
        return FileResponse(STATIC / "timeclock.css", media_type="text/css")

    @app.get("/api/time/status")
    def status(request: Request):
        selected = actor(request)
        now = utc_now()
        with connect() as conn:
            row = conn.execute("SELECT * FROM preview_shifts WHERE organization_id=? AND employee_id=? AND active=1",
                               (selected["organization_id"], selected["id"])).fetchone()
        return {"active": present(row, now) if row else None, "server_time": now, "tasks": TASKS}

    @app.get("/api/time/members")
    def time_members(request: Request):
        selected = actor(request)
        people = members(selected) if selected["role"] == "admin" else {selected["id"]: selected}
        return {"items": sorted(({"id": k, "name": v.get("name") or k, "role": v.get("role", "member")} for k, v in people.items()),
                                key=lambda p: (p["name"], p["id"]))}

    @app.get("/api/time/entries")
    def entries(request: Request, team: bool = False, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50), start_date: date | None = None, end_date: date | None = None, employee_id: str | None = Query(None, max_length=200)):
        selected = actor(request)
        where, values = scope(selected, team, employee_id, start_date, end_date)
        now = utc_now()
        with connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM preview_shifts WHERE " + where, values).fetchone()[0]
            rows = conn.execute("SELECT * FROM preview_shifts WHERE " + where + " ORDER BY json_extract(payload,'$.clock_in') DESC,id DESC LIMIT ? OFFSET ?", [*values,limit,offset]).fetchall()
        people = names(selected)
        return {"items": [named(present(row, now), people) for row in rows], "total": count, "offset": offset, "limit": limit, "server_time": now}

    @app.get("/api/time/entries/{shift_id}")
    def entry_detail(shift_id: str, request: Request):
        selected = actor(request)
        now = utc_now()
        with connect() as conn:
            row = visible_shift(conn, selected, shift_id)
            corrections = conn.execute("SELECT * FROM time_corrections WHERE organization_id=? AND shift_id=? ORDER BY occurred_at,id",
                                       (selected["organization_id"], shift_id)).fetchall()
            receipts = conn.execute("SELECT occurred_at,command FROM preview_clock_events WHERE organization_id=? AND shift_id=? ORDER BY occurred_at",
                                    (selected["organization_id"], shift_id)).fetchall()
            linked = conn.execute("SELECT * FROM time_offline_submissions WHERE organization_id=? AND resolved_shift_id=? ORDER BY estimated_at",
                                  (selected["organization_id"], shift_id)).fetchall()
        people = names(selected)
        def snapshot(payload):
            if payload is None:
                return None
            shift = json.loads(payload)
            return {"clock_in": shift["clock_in"], "clock_out": shift["clock_out"], "breaks": shift["breaks"],
                    "segments": shift["segments"], "order_title": shift.get("order_title"), **totals(shift, now)}
        return {"entry": named(present(row, now), people), "server_time": now,
                "corrections": [{"id": c["id"], "kind": c["kind"], "occurred_at": c["occurred_at"], "reason": c["reason"],
                                 "admin_id": c["admin_id"], "admin_name": people.get(c["admin_id"], c["admin_id"]),
                                 "from_version": c["from_version"], "to_version": c["to_version"],
                                 "before": snapshot(c["before_payload"]), "after": snapshot(c["after_payload"]),
                                 "resolves": json.loads(c["resolves"])} for c in corrections],
                "receipts": [{"occurred_at": r["occurred_at"], "action": json.loads(r["command"])["action"],
                              "basis": "server_receipt"} for r in receipts],
                "offline_submissions": [submission(s, people) for s in linked]}

    @app.get("/api/time/export")
    def export(request: Request, team: bool=False, start_date: date | None=None, end_date: date | None=None,
               employee_id: str | None = Query(None, max_length=200), detail: Literal["shifts", "intervals"] = "shifts"):
        selected = actor(request)
        where, values = scope(selected, team, employee_id, start_date, end_date)
        now = utc_now()
        with connect() as conn:
            if conn.execute("SELECT COUNT(*) FROM preview_shifts WHERE " + where, values).fetchone()[0] > EXPORT_LIMIT:
                raise HTTPException(422, f"Narrow the date range to {EXPORT_LIMIT} shifts or fewer before export")
            rows = conn.execute("SELECT * FROM preview_shifts WHERE " + where + " ORDER BY json_extract(payload,'$.clock_in'),id", values).fetchall()
        people = names(selected)
        output=io.StringIO(newline='');writer=csv.writer(output)
        def safe(value):
            value=str(value or '')
            return "'"+value if value.lstrip().startswith(('=','+','-','@')) or value[:1] in ('\t','\r') else value
        items = [named(present(row, now), people) for row in rows]
        if detail == "intervals":
            writer.writerow(['Employee ID','Employee','Shift ID','Work order','Interval','Task','Start UTC','End UTC','Seconds','Record basis','Payroll calculated'])
            for item in items:
                spans = [("Task", TASKS[s["task"]], s) for s in item["segments"]] + [("Break", "", b) for b in item["breaks"]]
                for kind, task, span in sorted(spans, key=lambda i: i[2]["start"]):
                    writer.writerow([safe(item['employee_id']),safe(item['employee_name']),item['id'],safe(item.get('order_title')),kind,task,
                                     span['start'],span['end'] or '',duration(span['start'],span['end']) if span['end'] else '',item['record_basis'],'No'])
        else:
            writer.writerow(['Employee ID','Employee','Work order','Clock in UTC','Clock out UTC','Work seconds','Break seconds','Status','Record basis','Corrections','Payroll calculated'])
            for item in items:
                writer.writerow([safe(item['employee_id']),safe(item['employee_name']),safe(item.get('order_title')),item['clock_in'],item['clock_out'] or '',
                                 item['work_seconds'],item['break_seconds'],item['status'],item['record_basis'],item['correction_count'],'No'])
        name = "wzos-time" + (f"-{start_date}" if start_date else "") + (f"-to-{end_date}" if end_date else "") + ("-intervals" if detail == "intervals" else "") + ".csv"
        return Response(output.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="{name}"'})

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

    def write_times(conn, selected, employee_id, row, body, kind, target):
        """Shared correction/manual-entry transaction. Caller holds BEGIN IMMEDIATE."""
        org = selected["organization_id"]
        request_hash = digest({"kind": kind, "target": target, **body.model_dump(mode="json", exclude_unset=True)})
        prior = conn.execute("SELECT request_hash,response FROM time_corrections WHERE organization_id=? AND admin_id=? AND request_id=?",
                             (org, selected["id"], str(body.request_id))).fetchone()
        if prior:
            if prior["request_hash"] != request_hash:
                raise HTTPException(409, "Retry ID was already used for a different correction")
            return json.loads(prior["response"])
        if row and row["version"] != body.expected_version:
            raise HTTPException(409, "This shift changed. Reload it before correcting.")
        now = utc_now()
        clock_in, clock_out, breaks, segments = validate_times(body, now)
        shift_id = row["id"] if row else str(uuid4())
        # Lexical ISO comparison only prefilters; exact datetimes decide below.
        others = conn.execute("""SELECT * FROM preview_shifts WHERE organization_id=? AND employee_id=? AND id<>?
            AND json_extract(payload,'$.clock_in')<? AND (json_extract(payload,'$.clock_out') IS NULL OR json_extract(payload,'$.clock_out')>?)""",
            (org, employee_id, shift_id, clock_out, clock_in)).fetchall()
        for other in others:
            shift = json.loads(other["payload"])
            other_end = parse(shift["clock_out"]) if shift["clock_out"] else datetime.max.replace(tzinfo=timezone.utc)
            if parse(shift["clock_in"]) < parse(clock_out) and parse(clock_in) < other_end:
                raise HTTPException(409, "These times overlap another shift for this employee")
        resolved = []
        for submission_id in dict.fromkeys(str(s) for s in body.resolves):
            item = conn.execute("SELECT status,employee_id FROM time_offline_submissions WHERE id=? AND organization_id=?", (submission_id, org)).fetchone()
            if not item or item["employee_id"] != employee_id:
                raise HTTPException(404, "Offline submission not found for this employee")
            if item["status"] != "pending":
                raise HTTPException(409, "An offline submission was already resolved. Refresh the review queue.")
            resolved.append(submission_id)
        before = json.loads(row["payload"]) if row else None
        shift = dict(before) if before else {"note": "", "source": "admin_entry", "order_id": None, "order_title": None}
        if row is None or "order_id" in body.model_fields_set:
            shift["order_id"], shift["order_title"] = body.order_id, None
            if body.order_id:
                shift["order_title"] = json.loads(permitted_order(conn, body.order_id, selected)["payload"])["title"]
        shift.update(clock_in=clock_in, clock_out=clock_out, breaks=breaks, segments=segments,
                     task=segments[-1]["task"], correction_count=shift.get("correction_count", 0) + (1 if row else 0),
                     last_changed_at=now, last_changed_by=selected["id"])
        version = row["version"] + 1 if row else 1
        # A corrected shift is always closed; an active shift can only be corrected by closing it.
        if row:
            conn.execute("UPDATE preview_shifts SET version=?,active=0,payload=? WHERE id=?", (version, json.dumps(shift), shift_id))
        else:
            conn.execute("INSERT INTO preview_shifts VALUES (?,?,?,?,?,?)", (shift_id, org, employee_id, version, 0, json.dumps(shift)))
        correction_id = str(uuid4())
        for submission_id in resolved:
            conn.execute("""UPDATE time_offline_submissions SET status='applied',resolved_by=?,resolved_at=?,resolution_reason=?,
                resolution_ref=?,resolved_shift_id=? WHERE id=? AND status='pending'""",
                (selected["id"], now, body.reason, correction_id, shift_id, submission_id))
        saved = conn.execute("SELECT * FROM preview_shifts WHERE id=?", (shift_id,)).fetchone()
        response = {"entry": present(saved, now), "correction_id": correction_id, "resolved": resolved, "server_time": now, "saved": True}
        conn.execute("INSERT INTO time_corrections VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (correction_id, org, shift_id, employee_id, selected["id"], str(body.request_id), request_hash, kind, now,
                      body.reason, row["version"] if row else 0, version, json.dumps(before) if before else None,
                      json.dumps(shift), json.dumps(resolved), json.dumps(response)))
        return response

    @app.post("/api/time/entries/{shift_id}/corrections")
    def correct(shift_id: str, body: Correction, request: Request):
        selected = actor(request)
        require_admin(selected, "Time corrections")
        with connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = visible_shift(conn, selected, shift_id)
            return write_times(conn, selected, row["employee_id"], row, body, "correction", shift_id)

    @app.post("/api/time/entries")
    def manual_entry(body: ManualEntry, request: Request):
        selected = actor(request)
        require_admin(selected, "Manual time entries")
        if body.employee_id not in members(selected):
            raise HTTPException(404, "Employee not found in this organization")
        with connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            return write_times(conn, selected, body.employee_id, None, body, "manual_entry", body.employee_id)

    @app.post("/api/time/offline-submissions")
    def submit_offline(body: OfflineBatch, request: Request):
        selected = actor(request)
        org, employee = selected["organization_id"], selected["id"]
        now = utc_now()
        received = parse(now)
        offset = received - body.device_submitted_at
        people = names(selected)
        with connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            saved = []
            for draft in body.drafts:
                if draft.captured_at > body.device_submitted_at + timedelta(minutes=1):
                    raise HTTPException(422, "A draft was captured after it was submitted; check the device clock")
                if draft.stated_at and draft.stated_at > draft.captured_at + timedelta(minutes=1):
                    raise HTTPException(422, "A stated time cannot be later than when the draft was recorded")
                request_hash = digest(draft.model_dump(mode="json"))
                prior = conn.execute("SELECT * FROM time_offline_submissions WHERE organization_id=? AND employee_id=? AND request_id=?",
                                     (org, employee, str(draft.request_id))).fetchone()
                if prior:
                    if prior["request_hash"] != request_hash:
                        raise HTTPException(409, "A draft retry ID was already used for different details")
                    saved.append(prior)
                    continue
                estimated = (draft.stated_at or draft.captured_at) + offset
                if estimated < received - OFFLINE_WINDOW:
                    raise HTTPException(422, "Drafts older than 14 days need an admin manual entry instead")
                if draft.order_id:
                    permitted_order(conn, draft.order_id, selected)
                submission_id = str(uuid4())
                conn.execute("INSERT INTO time_offline_submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL,NULL)",
                             (submission_id, org, employee, str(draft.request_id), request_hash, draft.action,
                              json.dumps(draft.model_dump(mode="json")), iso(draft.captured_at),
                              iso(draft.stated_at) if draft.stated_at else None, iso(body.device_submitted_at), now,
                              int(offset.total_seconds()), iso(min(estimated, received)), "pending"))
                saved.append(conn.execute("SELECT * FROM time_offline_submissions WHERE id=?", (submission_id,)).fetchone())
            return {"items": [submission(r, people) for r in saved], "server_time": now, "attendance_changed": False}

    @app.get("/api/time/offline-submissions")
    def offline_submissions(request: Request, team: bool = False, status: Literal["pending", "all"] = "pending"):
        selected = actor(request)
        where, values = "organization_id=?", [selected["organization_id"]]
        if team:
            require_admin(selected, "The team review queue")
        else:
            where += " AND employee_id=?"
            values.append(selected["id"])
        if status == "pending":
            where += " AND status='pending'"
        people = names(selected)
        with connect() as conn:
            rows = conn.execute("SELECT * FROM time_offline_submissions WHERE " + where + " ORDER BY estimated_at,id LIMIT 100", values).fetchall()
            items = [{**submission(r, people), "possible_duplicates": duplicates(conn, r) if r["status"] == "pending" else []} for r in rows]
        return {"items": items, "server_time": utc_now()}

    @app.post("/api/time/offline-submissions/{submission_id}/resolve")
    def resolve(submission_id: str, body: Resolution, request: Request):
        selected = actor(request)
        require_admin(selected, "Reviewing offline submissions")
        now = utc_now()
        with connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM time_offline_submissions WHERE id=? AND organization_id=?", (submission_id, selected["organization_id"])).fetchone()
            if not row:
                raise HTTPException(404, "Offline submission not found")
            if row["status"] != "pending":
                if row["status"] == body.decision and row["resolution_reason"] == body.reason and row["resolved_by"] == selected["id"]:
                    return {"item": submission(row, names(selected)), "server_time": now}
                raise HTTPException(409, "This submission was already resolved. Refresh the review queue.")
            conn.execute("UPDATE time_offline_submissions SET status=?,resolved_by=?,resolved_at=?,resolution_reason=? WHERE id=? AND status='pending'",
                         (body.decision, selected["id"], now, body.reason, submission_id))
            row = conn.execute("SELECT * FROM time_offline_submissions WHERE id=?", (submission_id,)).fetchone()
            return {"item": submission(row, names(selected)), "server_time": now}
