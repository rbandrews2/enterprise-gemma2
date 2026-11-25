"""Organization-wide, manually reported equipment placements."""
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

DDL = """CREATE TABLE IF NOT EXISTS equipment_placements (
    organization_id TEXT NOT NULL, id TEXT NOT NULL, payload TEXT NOT NULL,
    placed_by TEXT NOT NULL, placed_at TEXT NOT NULL, retrieved_by TEXT, retrieved_at TEXT,
    PRIMARY KEY (organization_id, id))"""

class Address(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    street: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    region: str = Field(min_length=1, max_length=100)

class Placement(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    equipment_type: Literal["Pickup truck", "TMA", "Message board", "Arrow board", "Custom"]
    custom_name: str | None = Field(default=None, min_length=1, max_length=100)
    quantity: int = Field(strict=True, ge=1, le=9007199254740991)
    location_method: Literal["address", "coordinates"]
    latitude: float = Field(strict=True, ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(strict=True, ge=-180, le=180, allow_inf_nan=False)
    address: Address | None = None

    @model_validator(mode="after")
    def required_details(self):
        if (self.equipment_type == "Custom") != (self.custom_name is not None):
            raise ValueError("Enter a name for custom equipment.")
        if (self.location_method == "address") != (self.address is not None):
            raise ValueError("Enter the complete address or select coordinates.")
        return self


def register(app, connect, actor):
    with connect() as db:
        db.execute(DDL)

    def enterprise(request):
        user = actor(request)
        if user["edition"] != "enterprise":
            raise HTTPException(403, "Equipment Locator requires Enterprise.")
        return user

    path = "/api/equipment-locator"

    @app.get(path)
    def outstanding(request: Request):
        user = enterprise(request)
        with connect() as db:
            rows = db.execute("""SELECT id,payload FROM equipment_placements
                WHERE organization_id=? AND retrieved_at IS NULL ORDER BY placed_at,id""",
                (user["organization_id"],)).fetchall()
        return {"items": [{"id": row["id"], **json.loads(row["payload"])} for row in rows]}

    @app.put(path + "/{placement_id}")
    def place(placement_id: UUID, body: Placement, request: Request):
        user = enterprise(request)
        key = (user["organization_id"], str(placement_id))
        payload = json.dumps(body.model_dump(), sort_keys=True)
        with connect() as db:
            db.execute("""INSERT INTO equipment_placements
                (organization_id,id,payload,placed_by,placed_at) VALUES (?,?,?,?,?)
                ON CONFLICT DO NOTHING""", (*key,payload,user["id"],datetime.now(timezone.utc).isoformat()))
            row = db.execute("SELECT payload,placed_by FROM equipment_placements WHERE organization_id=? AND id=?", key).fetchone()
            if row["payload"] != payload or row["placed_by"] != user["id"]:
                raise HTTPException(409, "Placement identifier already in use.")
        return {"id": str(placement_id)}

    @app.put(path + "/{placement_id}/retrieved")
    def retrieve(placement_id: UUID, request: Request):
        user = enterprise(request)
        key = (user["organization_id"], str(placement_id))
        with connect() as db:
            row = db.execute("SELECT id FROM equipment_placements WHERE organization_id=? AND id=?",key).fetchone()
            if not row:
                raise HTTPException(404, "Equipment placement not found.")
            db.execute("""UPDATE equipment_placements SET retrieved_at=?,retrieved_by=?
                WHERE organization_id=? AND id=? AND retrieved_at IS NULL""",
                (datetime.now(timezone.utc).isoformat(),user["id"],*key))
        return {"id": str(placement_id)}
