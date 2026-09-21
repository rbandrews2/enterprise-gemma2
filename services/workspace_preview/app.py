"""Run only via scripts/start_workspace_preview.py; fixture identities are NOT auth."""
import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from services.v2.intake import assess
from shared.intake import IntakeRequest

ROOT = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).with_name("static")
ACTORS = {
    f"{edition}-{role}": {"id": f"{edition}-{role}", "edition": edition,
        "role": role, "organization_id": edition + "-demo",
        "organization": "Tidewater Field Team" if edition == "enterprise" else "Piedmont Road Crew",
        "name": "Jordan Lee" if role == "admin" else "Casey Morgan"}
    for edition in ("core", "enterprise") for role in ("admin", "general")
}


class OrderInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=120)
    work_type: Literal["line_striping", "underground_utility", "road_maintenance", "other"]
    address: str = Field(min_length=1, max_length=500)
    locality: str = Field(min_length=1, max_length=120)
    work_date: date | None = None
    notes: str = Field(default="", max_length=2000)


class NewOrder(OrderInput):
    request_id: UUID


class UpdateOrder(OrderInput):
    expected_version: int = Field(ge=1, strict=True)


def create_app(db_path: Path | None = None):
    if os.getenv("WZOS_WORKSPACE_PREVIEW") != "1" or any(os.getenv(k) for k in ("K_SERVICE", "GAE_ENV", "NETLIFY")):
        raise RuntimeError("Synthetic preview requires explicit local opt-in and refuses cloud runtime markers")
    db_path = db_path or ROOT / ".local-data/workspace-preview/orders.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect():
        conn = sqlite3.connect(db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS preview_orders (
            id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, owner_id TEXT NOT NULL,
            version INTEGER NOT NULL, payload TEXT NOT NULL, updated_at TEXT NOT NULL,
            request_id TEXT NOT NULL, request_hash TEXT NOT NULL,
            UNIQUE(owner_id, request_id))""")
        for edition in ("core", "enterprise"):
            payload = {"title": "Granby Street markings" if edition == "enterprise" else "Morning pavement inspection",
                       "work_type": "line_striping" if edition == "enterprise" else "road_maintenance",
                       "address": "Granby Street, Norfolk, VA" if edition == "enterprise" else "Main Street, Richmond, VA",
                       "locality": "Norfolk" if edition == "enterprise" else "Richmond",
                       "work_date": None, "notes": "Synthetic example. Verify exact site limits before planning."}
            conn.execute("INSERT OR IGNORE INTO preview_orders VALUES (?,?,?,?,?,?,?,?)",
                         (edition + "-sample", edition + "-demo", edition + "-general", 1,
                          json.dumps(payload), datetime.now(timezone.utc).isoformat(), "seed", "seed"))

    app = FastAPI(title="WZOS synthetic workspace preview", docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def local_boundary(request: Request, call_next):
        hosts = {"127.0.0.1:8083", "localhost:8083", "testserver"}
        if (not request.client or request.client.host not in {"127.0.0.1", "::1", "testclient"}
                or request.headers.get("host") not in hosts):
            return JSONResponse({"error": "local_preview_only"}, status_code=403)
        origin = request.headers.get("origin")
        if (origin and origin != f"http://{request.headers['host']}") or request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"error": "same_origin_only"}, status_code=403)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(sqlite3.DatabaseError)
    async def database_error(request, error):
        return JSONResponse({"detail": "Local storage is unavailable. Your unsaved draft remains in the form."}, status_code=503)

    def actor(request):
        selected = ACTORS.get(request.headers.get("X-Preview-Actor"))
        if not selected:
            raise HTTPException(401, "Select a valid synthetic preview identity")
        return selected

    def serialize(row):
        return {"id": row["id"], "owner_id": row["owner_id"], "version": row["version"],
                "updated_at": row["updated_at"], "status": "draft", **json.loads(row["payload"])}

    def permitted_row(conn, order_id, selected):
        row = conn.execute("SELECT * FROM preview_orders WHERE id=? AND organization_id=?",
                           (order_id, selected["organization_id"])).fetchone()
        if not row or (selected["role"] != "admin" and row["owner_id"] != selected["id"]):
            raise HTTPException(404, "Work order not found for this preview identity")
        return row

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/workspace.js")
    def script():
        return FileResponse(STATIC / "workspace.js", media_type="text/javascript")

    @app.get("/workspace.css")
    def styles():
        return FileResponse(STATIC / "workspace.css", media_type="text/css")

    @app.get("/api/identities")
    def identities():
        return {"mode": "synthetic_local_preview", "identities": list(ACTORS.values())}

    @app.get("/api/session")
    def session(request: Request):
        selected = actor(request)
        return {**selected, "can_prepare_atlas": selected["edition"] == "enterprise",
                "can_manage_team": selected["role"] == "admin", "production_authenticated": False}

    @app.get("/api/orders")
    def orders(request: Request):
        selected = actor(request)
        with connect() as conn:
            query = "SELECT * FROM preview_orders WHERE organization_id=?"
            params = [selected["organization_id"]]
            if selected["role"] != "admin":
                query += " AND owner_id=?"
                params.append(selected["id"])
            rows = conn.execute(query + " ORDER BY updated_at DESC, id LIMIT 100", params).fetchall()
        return {"items": [serialize(row) for row in rows], "limit": 100}

    @app.post("/api/orders", status_code=201)
    def create_order(payload: NewOrder, request: Request):
        selected = actor(request)
        body = payload.model_dump(mode="json", exclude={"request_id"})
        packed = json.dumps(body, sort_keys=True)
        digest = hashlib.sha256(packed.encode()).hexdigest()
        with connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            prior = conn.execute("SELECT * FROM preview_orders WHERE owner_id=? AND request_id=?",
                                 (selected["id"], str(payload.request_id))).fetchone()
            if prior:
                if prior["request_hash"] != digest:
                    raise HTTPException(409, "Retry identifier was already used with different content")
                return serialize(prior)
            order_id = str(uuid4())
            conn.execute("INSERT INTO preview_orders VALUES (?,?,?,?,?,?,?,?)",
                         (order_id, selected["organization_id"], selected["id"], 1, packed,
                          datetime.now(timezone.utc).isoformat(), str(payload.request_id), digest))
            return serialize(permitted_row(conn, order_id, selected))

    @app.get("/api/orders/{order_id}")
    def read_order(order_id: str, request: Request):
        with connect() as conn:
            return serialize(permitted_row(conn, order_id, actor(request)))

    @app.put("/api/orders/{order_id}")
    def update_order(order_id: str, payload: UpdateOrder, request: Request):
        selected = actor(request)
        with connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = permitted_row(conn, order_id, selected)
            if row["version"] != payload.expected_version:
                raise HTTPException(409, "This work order changed. Reload the saved version before editing again.")
            packed = json.dumps(payload.model_dump(mode="json", exclude={"expected_version"}), sort_keys=True)
            conn.execute("UPDATE preview_orders SET payload=?,version=version+1,updated_at=? WHERE id=?",
                         (packed, datetime.now(timezone.utc).isoformat(), order_id))
            return serialize(permitted_row(conn, order_id, selected))

    @app.post("/api/orders/{order_id}/preparation")
    def preparation(order_id: str, request: Request, expected_version: int):
        selected = actor(request)
        if selected["edition"] != "enterprise":
            raise HTTPException(403, "Advanced Atlas preparation requires Enterprise in this preview")
        with connect() as conn:
            row = permitted_row(conn, order_id, selected)
            if row["version"] != expected_version:
                raise HTTPException(409, "Work order changed. Reload before preparing recommendations.")
            record = serialize(row)
        intake = IntakeRequest(work_type=record["work_type"], work_description=record["notes"] or record["title"],
                               location={"address": record["address"], "locality": record["locality"]},
                               project_date=record["work_date"],
                               requested_outputs=["work_zone_setup", "required_forms", "annotated_image"])
        assessment = assess(intake)
        return {"order_id": order_id, "version": record["version"], "model_called": False,
                "approved_for_field_use": False, "placements": [],
                "attention_items": [i.model_dump() for i in assessment.attention_items if i.category != "capability_gap"],
                "note": "Intake preparation only. No Gemma call, verified placement, imagery or compliance approval."}

    return app
