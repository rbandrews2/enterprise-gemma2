"""Shift inspection records and private, size-limited photographic evidence."""
import base64
import binascii
from datetime import date, datetime, timezone
from io import BytesIO
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, Request
from PIL import Image, ImageOps
from pydantic import BaseModel, ConfigDict, Field

DDL = """CREATE TABLE IF NOT EXISTS field_inspections (
    organization_id TEXT NOT NULL, order_id TEXT NOT NULL, id TEXT NOT NULL,
    closure_type TEXT NOT NULL, shift TEXT NOT NULL, due_on TEXT NOT NULL,
    checkpoint TEXT NOT NULL, location TEXT NOT NULL, scheduled_by TEXT NOT NULL,
    status TEXT NOT NULL, finding TEXT NOT NULL DEFAULT '', repair_owner TEXT NOT NULL DEFAULT '',
    inspected_by TEXT, inspected_at TEXT, recheck_note TEXT, rechecked_by TEXT, rechecked_at TEXT,
    recheck_photo TEXT, recheck_thumbnail TEXT, PRIMARY KEY (organization_id,order_id,id))"""


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Schedule(Input):
    closure_type: str = Field(min_length=1, max_length=100)
    shift: Literal["Day", "Night"]
    due_on: date
    checkpoint: str = Field(min_length=1, max_length=160)
    location: str = Field(min_length=1, max_length=200)


class Finding(Input):
    status: Literal["Passed", "Repair needed"]
    finding: str = Field(min_length=1, max_length=800)
    repair_owner: str = Field(default="", max_length=120)


class Recheck(Input):
    note: str = Field(min_length=1, max_length=800)
    photo: str = Field(max_length=1_400_000)


def small_photo(value, longest_side=1280):
    try:
        raw = base64.b64decode(value, validate=True)
        if len(raw) > 1024 * 1024:
            raise ValueError()
        with Image.open(BytesIO(raw), formats=("JPEG", "PNG", "WEBP")) as source:
            if source.width * source.height > 12_000_000:
                raise ValueError()
            picture = ImageOps.exif_transpose(source).convert("RGB")
            picture.thumbnail((longest_side, longest_side))
            out = BytesIO()
            picture.save(out, "JPEG", quality=80)
            return base64.b64encode(out.getvalue()).decode("ascii")
    except (ValueError, OSError, binascii.Error, Image.DecompressionBombError) as error:
        raise HTTPException(422, "Choose a JPEG, PNG or WebP image up to 1 MB and 12 megapixels.") from error


def records(db, org, order, include_photos=False):
    columns = """id, closure_type, shift, due_on, checkpoint, location, scheduled_by,
        status, finding, repair_owner, inspected_by, inspected_at, recheck_note, rechecked_by, rechecked_at"""
    if include_photos:
        columns += ', recheck_thumbnail AS recheck_photo'
    return [dict(row) for row in db.execute(
        f"SELECT {columns} FROM field_inspections WHERE organization_id=? AND order_id=? ORDER BY due_on,shift,id",
        (org, order)).fetchall()]


def register(app, connect, actor, authorize):
    with connect() as db:
        db.execute(DDL)

    def scope(db, request, order_id):
        user = actor(request)
        authorize(db, order_id, user)
        return user, (user["organization_id"], order_id)

    path = "/api/orders/{order_id}/inspections"

    @app.get(path)
    def listing(order_id: str, request: Request):
        with connect() as db:
            _, key = scope(db, request, order_id)
            return {"items": records(db, *key)}

    @app.put(path + "/{item}")
    def schedule(order_id: str, item: UUID, body: Schedule, request: Request):
        with connect() as db:
            user, key = scope(db, request, order_id)
            params = (*key, str(item))
            values = body.model_dump(mode="json")
            db.execute("""INSERT INTO field_inspections
                (organization_id,order_id,id,closure_type,shift,due_on,checkpoint,location,scheduled_by,status)
                VALUES (?,?,?,?,?,?,?,?,?,'Scheduled') ON CONFLICT DO NOTHING""",
                (*params, body.closure_type, body.shift, body.due_on.isoformat(), body.checkpoint, body.location, user["id"]))
            row = db.execute("SELECT * FROM field_inspections WHERE organization_id=? AND order_id=? AND id=?", params).fetchone()
            if row["scheduled_by"] != user["id"] or any(row[k] != v for k,v in values.items()):
                raise HTTPException(409, "This inspection identifier is already in use.")
            return {"id": str(item)}

    def transition(db, key, item, before, updates):
        params = (*key, str(item))
        assignments = ",".join(k+"=?" for k in updates)
        changed = db.execute(f"UPDATE field_inspections SET {assignments} WHERE organization_id=? AND order_id=? AND id=? AND status=?",
                             (*updates.values(), *params, before))
        if changed.rowcount != 1:
            row = db.execute("SELECT * FROM field_inspections WHERE organization_id=? AND order_id=? AND id=?", params).fetchone()
            if not row:
                raise HTTPException(404, "Inspection not found.")
            if any(row[k] != v for k,v in updates.items() if not k.endswith("_at")):
                raise HTTPException(409, "Inspection changed. Reopen it before saving.")
        return {"id": str(item)}

    @app.put(path + "/{item}/finding")
    def inspect(order_id: str, item: UUID, body: Finding, request: Request):
        if body.status == "Repair needed" and not body.repair_owner:
            raise HTTPException(422, "Enter a repair owner.")
        with connect() as db:
            user, key = scope(db, request, order_id)
            return transition(db, key, item, "Scheduled", {
                **body.model_dump(), "inspected_by": user["id"], "inspected_at": datetime.now(timezone.utc).isoformat()})

    @app.put(path + "/{item}/recheck")
    def recheck(order_id: str, item: UUID, body: Recheck, request: Request):
        with connect() as db:
            user, key = scope(db, request, order_id)
            image = small_photo(body.photo)
            return transition(db, key, item, "Repair needed", {
                "status":"Rechecked", "recheck_note":body.note, "recheck_photo":image, "recheck_thumbnail":small_photo(image, 240),
                "rechecked_by":user["id"], "rechecked_at":datetime.now(timezone.utc).isoformat()})

    @app.get(path + "/{item}/photo")
    def photo(order_id: str, item: UUID, request: Request):
        with connect() as db:
            _, key = scope(db, request, order_id)
            row = db.execute("SELECT recheck_photo FROM field_inspections WHERE organization_id=? AND order_id=? AND id=?",
                             (*key, str(item))).fetchone()
            if not row or not row["recheck_photo"]:
                raise HTTPException(404, "Photo not found.")
            return {"photo":row["recheck_photo"]}
