"""Scoped synthetic scheduling and incident drafts adapted from recovered Core fields."""
import json
from datetime import date, datetime, timezone
from typing import Literal
from uuid import UUID
from fastapi import HTTPException, Request, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator

class VehicleInspection(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    vehicle_id: str = Field(min_length=1, max_length=120)
    odometer: int | None = Field(default=None, ge=0, le=10000000, strict=True)
    trip_type: Literal["pre-trip", "post-trip"] = "pre-trip"
    tires: Literal["not_checked", "pass", "fail"] = "not_checked"
    fluids: Literal["not_checked", "pass", "fail"] = "not_checked"
    brakes: Literal["not_checked", "pass", "fail"] = "not_checked"
    ebrake: Literal["not_checked", "pass", "fail"] = "not_checked"
    mirrors: Literal["not_checked", "pass", "fail"] = "not_checked"
    windows: Literal["not_checked", "pass", "fail"] = "not_checked"
    defects: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def defect_details(self):
        if any(getattr(self, key) == "fail" for key in ("tires", "fluids", "brakes", "ebrake", "mirrors", "windows")) and not self.defects:
            raise ValueError("Describe any failed inspection item in Defects")
        return self


class SafetyWorksheet(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    competent_person: str = Field(default="", max_length=200)
    tasks: str = Field(default="", max_length=4000)
    hazards: str = Field(default="", max_length=4000)
    controls: str = Field(default="", max_length=4000)
    emergency_plan: str = Field(default="", max_length=2000)
    ppe: str = Field(default="", max_length=1000)

class ModuleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: UUID
    expected_version: int = Field(default=0, ge=0, strict=True)
    form_type: Literal["incident", "dvir", "jsa"] = "incident"
    inspection: VehicleInspection | None = None
    safety: SafetyWorksheet | None = None
    assignees: list[str] = Field(default_factory=list, max_length=50)
    title: str = Field(min_length=1, max_length=120)
    location: str = Field(default="", max_length=500)
    details: str = Field(default="", max_length=4000)
    order_id: str | None = Field(default=None, max_length=100)
    start: datetime | None = None
    end: datetime | None = None
    status: Literal["draft", "cancelled"] = "draft"

    @model_validator(mode="after")
    def times(self):
        for value in (self.start, self.end):
            if value and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError("Schedule times require a timezone")
        if self.start and self.end and self.end <= self.start:
            raise ValueError("End must be after start")
        return self


def register(app, connect, actor, permitted_row, actors, synthetic=True):
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS module_records (
            id TEXT NOT NULL, kind TEXT NOT NULL, organization_id TEXT NOT NULL,
            owner_id TEXT NOT NULL, version INTEGER NOT NULL, payload TEXT NOT NULL,
            updated_at TEXT NOT NULL, PRIMARY KEY(organization_id, kind, id))""")

        db.execute("""CREATE TABLE IF NOT EXISTS module_revisions (
            organization_id TEXT NOT NULL, kind TEXT NOT NULL, id TEXT NOT NULL,
            version INTEGER NOT NULL, payload TEXT NOT NULL, author_id TEXT NOT NULL,
            saved_at TEXT NOT NULL, PRIMARY KEY(organization_id,kind,id,version))""")

    @app.get("/api/modules/roster")
    def roster(request: Request):
        selected=actor(request)
        return {"items":[{"id":a["id"],"name":a["name"],"role":a["role"]} for a in actors(selected).values() if a["organization_id"]==selected["organization_id"]], "synthetic":synthetic}

    def scope(kind, selected):
        clause = "organization_id=? AND kind=?"
        params = [selected["organization_id"], kind]
        if kind == "forms" and selected["role"] != "admin":
            clause += " AND owner_id=?"
            params.append(selected["id"])
        return clause, params

    def unpack(row):
        return {**json.loads(row["payload"]), "id": row["id"], "version": row["version"],
                "updated_at": row["updated_at"], "owner_id": row["owner_id"]}

    @app.get("/api/modules/{kind}")
    def listing(kind: Literal["forms", "schedule"], request: Request,
                offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=50), day: date | None = None):
        selected = actor(request)
        clause, params = scope(kind, selected)
        if day and kind == "schedule":
            clause += " AND substr(json_extract(payload, '$.start'),1,10)=?"
            params.append(day.isoformat())
        with connect() as db:
            total = db.execute("SELECT COUNT(*) FROM module_records WHERE " + clause, params).fetchone()[0]
            rows = db.execute("SELECT * FROM module_records WHERE " + clause +
                              " ORDER BY updated_at DESC, id LIMIT ? OFFSET ?", [*params, limit, offset]).fetchall()
        return {"items": [unpack(row) for row in rows], "total": total, "offset": offset,
                "can_edit": kind == "forms" or selected["role"] == "admin"}

    @app.put("/api/modules/{kind}/{record_id}")
    def save(kind: Literal["forms", "schedule"], record_id: UUID, payload: ModuleRecord, request: Request):
        selected = actor(request)
        if kind == "schedule":
            if selected["role"] != "admin":
                raise HTTPException(403, "Only admins can edit the team schedule")
            if not payload.start or not payload.end:
                raise HTTPException(422, "Start and end times are required")
        elif payload.form_type == "dvir" and payload.inspection is None:
            raise HTTPException(422, "Vehicle inspection details are required")
        if kind == "forms" and payload.form_type == "jsa" and payload.safety is None:
            raise HTTPException(422, "Safety worksheet fields are required")
        if payload.form_type != "jsa" and payload.safety is not None:
            raise HTTPException(422, "Safety fields belong to the JSA worksheet")
        if payload.form_type != "dvir" and payload.inspection is not None:
            raise HTTPException(422, "Incident drafts cannot contain vehicle inspection fields")
        if kind == "schedule" and (payload.inspection is not None or payload.form_type != "incident"):
            raise HTTPException(422, "Vehicle inspections belong in Forms hub")
        if kind == "forms" and (payload.start or payload.end):
            raise HTTPException(422, "Incident drafts do not use schedule times")
        allowed={a["id"] for a in actors(selected).values() if a["organization_id"]==selected["organization_id"]}
        if len(set(payload.assignees)) != len(payload.assignees) or not set(payload.assignees)<=allowed or (kind=="forms" and payload.assignees):
            raise HTTPException(422, "Assignments must be distinct members of this organization on a schedule")
        packed = payload.model_dump(mode="json", exclude={"expected_version", "request_id"})
        for key in ("start", "end"):
            if getattr(payload, key):
                packed[key] = getattr(payload, key).astimezone(timezone.utc).isoformat()
        serialized = json.dumps(packed, sort_keys=True)
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            clause, params = scope(kind, selected)
            row = db.execute("SELECT * FROM module_records WHERE " + clause + " AND id=?", [*params, str(record_id)]).fetchone()
            existing = db.execute("SELECT 1 FROM module_records WHERE organization_id=? AND kind=? AND id=?",
                                  (selected["organization_id"], kind, str(record_id))).fetchone()
            if existing and not row:
                raise HTTPException(404, "Record not found")
            if row and kind == "forms" and json.loads(row["payload"]).get("form_type", "incident") != payload.form_type:
                raise HTTPException(409, "Create a new draft to use a different form template")
            if payload.order_id:
                permitted_row(db, payload.order_id, selected)
            version = row["version"] if row else 0
            # Retrying the same saved content is safe; stale conflicting edits are not.
            if row and row["payload"] == serialized and payload.expected_version == version - 1:
                return unpack(row)
            if version != payload.expected_version:
                raise HTTPException(409, "Record changed. Reload before editing")
            if kind=="schedule" and payload.status!="cancelled" and payload.assignees:
                others=db.execute("SELECT id,payload FROM module_records WHERE organization_id=? AND kind='schedule' AND id<>?",(selected["organization_id"],str(record_id))).fetchall()
                for other in others:
                    event=json.loads(other["payload"])
                    if event.get("status")!="cancelled" and set(event.get("assignees",[])) & set(payload.assignees) and event.get("start") and event.get("end"):
                        if datetime.fromisoformat(event['start']) < payload.end and datetime.fromisoformat(event['end']) > payload.start:
                            raise HTTPException(409,"An assigned member has an overlapping schedule draft")
            if row:
                db.execute("INSERT INTO module_revisions VALUES (?,?,?,?,?,?,?) ON CONFLICT DO NOTHING",(selected["organization_id"],kind,str(record_id),row['version'],row['payload'],row['owner_id'],row['updated_at']))
            db.execute("INSERT INTO module_revisions VALUES (?,?,?,?,?,?,?)",(selected["organization_id"],kind,str(record_id),version+1,serialized,selected['id'],datetime.now(timezone.utc).isoformat()))
            db.execute("INSERT INTO module_records VALUES (?,?,?,?,?,?,?) ON CONFLICT(organization_id,kind,id) DO UPDATE SET version=excluded.version,payload=excluded.payload,updated_at=excluded.updated_at",
                       (str(record_id), kind, selected["organization_id"], row["owner_id"] if row else selected["id"],
                        version + 1, serialized, datetime.now(timezone.utc).isoformat()))
            return unpack(db.execute("SELECT * FROM module_records WHERE organization_id=? AND kind=? AND id=?",
                                     (selected["organization_id"], kind, str(record_id))).fetchone())

    @app.get('/api/modules/{kind}/{record_id}/history')
    def history(kind: Literal['forms','schedule'], record_id: UUID, request: Request, offset: int=Query(0,ge=0)):
        selected=actor(request);clause,params=scope(kind,selected)
        with connect() as db:
            current=db.execute('SELECT * FROM module_records WHERE '+clause+' AND id=?',(*params,str(record_id))).fetchone()
            if not current: raise HTTPException(404,'Record not found')
            rows=db.execute('SELECT * FROM module_revisions WHERE organization_id=? AND kind=? AND id=? ORDER BY version DESC LIMIT 20 OFFSET ?', (selected['organization_id'],kind,str(record_id),offset)).fetchall()
        return {"items":[{"version":r['version'],"saved_at":r['saved_at'],"author_id":r['author_id'],"record":json.loads(r['payload'])} for r in rows]}
