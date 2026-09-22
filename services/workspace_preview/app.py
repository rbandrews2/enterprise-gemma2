"""Run only via scripts/start_workspace_preview.py; fixture identities are NOT auth."""
import hashlib
import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from shared.intake import SiteContext
from shared.job_geometry import JobGeometry
from services.v2.knowledge.store import Store
from services.workspace_preview.atlas_adapter import prepare_order
from services.workspace_preview.intelligence import ChatInput, ClientDisconnected, LocalIntelligence, ModelUnavailable, navigation_for, reply_until_disconnected

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
    road_authority: str | None = Field(default=None, min_length=1, max_length=200)
    site: SiteContext = Field(default_factory=SiteContext)
    job_geometry: JobGeometry | None = None


class NewOrder(OrderInput):
    request_id: UUID


class UpdateOrder(OrderInput):
    expected_version: int = Field(ge=1, strict=True)


CHECKLIST_ITEMS = {
    "site": "Site details and measured limits",
    "authority": "Governing authority and source references",
    "forms": "Required and recommended forms / permits",
    "crew": "Crew, training and equipment",
    "communication": "Communication, access and coordination",
}


class ChecklistItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    status: Literal["not_reviewed", "needs_attention", "reported_ready", "not_applicable"]
    notes: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def reason_for_exclusion(self):
        if self.status == "not_applicable" and not self.notes:
            raise ValueError("Explain why the item is not applicable")
        return self


class ChecklistInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=0, strict=True)
    expected_order_version: int = Field(ge=1, strict=True)
    items: dict[str, ChecklistItem]

    @model_validator(mode="after")
    def complete_items(self):
        if set(self.items) != set(CHECKLIST_ITEMS):
            raise ValueError("Include exactly the five checklist categories")
        return self


def create_app(db_path: Path | None = None, knowledge_store=None, intelligence=None):
    if os.getenv("WZOS_WORKSPACE_PREVIEW") != "1" or any(os.getenv(k) for k in ("K_SERVICE", "GAE_ENV", "NETLIFY")):
        raise RuntimeError("Synthetic preview requires explicit local opt-in and refuses cloud runtime markers")
    db_path = db_path or ROOT / ".local-data/workspace-preview/orders.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    knowledge_store = knowledge_store if knowledge_store is not None else Store()
    intelligence = intelligence if intelligence is not None else LocalIntelligence()

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
        conn.execute("""CREATE TABLE IF NOT EXISTS preview_checklists (
            order_id TEXT NOT NULL, version INTEGER NOT NULL, order_version INTEGER NOT NULL,
            payload TEXT NOT NULL, author_id TEXT NOT NULL, saved_at TEXT NOT NULL,
            PRIMARY KEY(order_id, version))""")
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

    @app.get("/atlas-assistant.png")
    def assistant_avatar():
        return FileResponse(STATIC / "atlas-assistant.png", media_type="image/png")

    @app.get("/geometry.js")
    def geometry_script():
        return FileResponse(STATIC / "geometry.js", media_type="text/javascript")

    @app.get("/assistant.js")
    def assistant_script():
        return FileResponse(STATIC / "assistant.js", media_type="text/javascript")

    @app.get("/api/identities")
    def identities():
        return {"mode": "synthetic_local_preview", "identities": list(ACTORS.values())}

    @app.get("/api/session")
    def session(request: Request):
        selected = actor(request)
        return {**selected, "can_prepare_atlas": selected["edition"] == "enterprise",
                "can_manage_team": selected["role"] == "admin", "production_authenticated": False}

    @app.get("/api/assistant/status")
    async def assistant_status(request: Request):
        actor(request)
        return {"ready": await intelligence.ready(), "mode": "local", "actions_enabled": False}

    @app.post("/api/assistant/chat")
    async def assistant_chat(payload: ChatInput, request: Request):
        selected = actor(request)
        context = {"edition": selected["edition"], "role": selected["role"], "page": "work_orders"}
        citations = []
        checklist_basis = None
        if payload.order_id:
            with connect() as conn:
                order = serialize(permitted_row(conn, payload.order_id, selected))
                checklist_row = conn.execute(
                    "SELECT * FROM preview_checklists WHERE order_id=? ORDER BY version DESC LIMIT 1",
                    (payload.order_id,),
                ).fetchone()
            if payload.expected_version != order["version"]:
                raise HTTPException(409, "Work order changed. Reload before asking about this job.")
            context["saved_job"] = {k: v for k, v in order.items() if k != "job_geometry"}
            checklist_basis = {"status": "not_saved", "version": None, "order_version": None, "stale": False}
            checklist_context = {**checklist_basis, "items": {}}
            if checklist_row:
                saved_checklist = checklist_record(checklist_row, order["version"])
                checklist_basis = {"status": "saved", **{key: saved_checklist[key] for key in ("version", "order_version", "stale")}}
                checklist_context = {**checklist_basis, "items": {
                    key: {"label": CHECKLIST_ITEMS[key], "status": item["status"],
                          "notes": item["notes"][:300], "notes_truncated": len(item["notes"]) > 300}
                    for key, item in saved_checklist["items"].items()
                }}
            context["readiness_checklist"] = checklist_context
            geometry = order.get("job_geometry") or {}
            context["geometry_summary"] = {k: v for k, v in geometry.items() if k not in {"approaches", "work_limits"}}
            context["geometry_summary"].update(approach_count=len(geometry.get("approaches", [])), work_limit_points=len(geometry.get("work_limits", [])), verification_status="customer_reported")
            if selected["edition"] == "enterprise" and re.search(r"sign|flagger|placement|safety|mutcd|vdot|osha|reference|source|requirement|work.zone", payload.question, re.I):
                packet = prepare_order(order, knowledge_store)
                context["questions"] = packet["questions"]
                context["evidence_review"] = packet["evidence_review"]
                # Bounded candidates; official citation metadata stays outside generated text.
                for topic in packet["references"]["topics"]:
                    if topic["candidates"]:
                        citations.append(topic["candidates"][0])
                    if len(citations) == 3:
                        break
                context["candidate_references"] = [{**ref, "text": ref["text"][:600]} for ref in citations]
        try:
            answer = await reply_until_disconnected(request, intelligence, payload, context)
        except ClientDisconnected:
            return JSONResponse({"detail": "Reply stopped"}, status_code=499)
        except ModelUnavailable as error:
            raise HTTPException(503, str(error)) from error
        return {"answer": answer, "model_called": True, "actions_performed": [],
                "navigation": navigation_for(payload.question, selected["edition"], bool(payload.order_id)),
                "approved_for_field_use": False, "citations": citations, "checklist_basis": checklist_basis,
                "order_version": payload.expected_version if payload.order_id else None}

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

    def checklist_record(row, order_version):
        return {"version": row["version"], "order_version": row["order_version"],
                "items": json.loads(row["payload"]), "author_id": row["author_id"],
                "saved_at": row["saved_at"], "stale": row["order_version"] != order_version}

    @app.get("/api/orders/{order_id}/checklist")
    def read_checklist(order_id: str, request: Request, version: int | None = Query(None, ge=1)):
        with connect() as conn:
            order = permitted_row(conn, order_id, actor(request))
            latest = conn.execute("SELECT MAX(version) FROM preview_checklists WHERE order_id=?", (order_id,)).fetchone()[0] or 0
            row = conn.execute("SELECT * FROM preview_checklists WHERE order_id=? AND version=?", (order_id, version or latest)).fetchone()
            if version and not row:
                raise HTTPException(404, "Checklist revision not found")
            return {"order_id": order_id, "current_order_version": order["version"],
                    "latest_version": latest, "labels": CHECKLIST_ITEMS,
                    "approved_for_field_use": False,
                    "checklist": checklist_record(row, order["version"]) if row else None}

    @app.put("/api/orders/{order_id}/checklist")
    def save_checklist(order_id: str, payload: ChecklistInput, request: Request):
        selected = actor(request)
        with connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            order = permitted_row(conn, order_id, selected)
            latest = conn.execute("SELECT MAX(version) FROM preview_checklists WHERE order_id=?", (order_id,)).fetchone()[0] or 0
            if order["version"] != payload.expected_order_version or latest != payload.expected_version:
                raise HTTPException(409, "Job or checklist changed. Reload saved records before reviewing again.")
            packed = json.dumps({key: item.model_dump() for key, item in payload.items.items()}, sort_keys=True)
            conn.execute("INSERT INTO preview_checklists VALUES (?,?,?,?,?,?)", (order_id, latest + 1,
                         order["version"], packed, selected["id"], datetime.now(timezone.utc).isoformat()))
            row = conn.execute("SELECT * FROM preview_checklists WHERE order_id=? AND version=?", (order_id, latest + 1)).fetchone()
            return {"checklist": checklist_record(row, order["version"]), "approved_for_field_use": False}

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
        return prepare_order(record, knowledge_store)

    return app
