"""Forms Hub: a customer form library for download and print.

Two sources:
- Built-in WZOS printable forms from forms_catalog.json. Users may type into them
  on screen before printing or downloading; nothing is stored on the server.
- Team forms uploaded by organization admins (for example an agency's official
  form). Metadata lives in module_records (kind='form_library'); files use the
  existing private file store via /api/files with entity_kind='form_library'.
Every member of the organization can list and download its team forms. WZOS does
not verify, edit or determine the applicability of uploaded forms.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

CATALOG = Path(__file__).with_name("forms_catalog.json")
STATIC = Path(__file__).with_name("static")
FIELD_TYPES = {"text", "textarea", "select", "multiselect", "date", "time", "number", "rows"}
LIBRARY_CATEGORIES = {"official_agency_form": "Official agency form", "company_form": "Company form"}


def checksum(template):
    return hashlib.sha256(json.dumps(template, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_catalog(path=None):
    """Return {(id, revision): template-with-checksum} and {id: latest revision}; refuse an invalid catalog."""
    data = json.loads(Path(path or CATALOG).read_text(encoding="utf-8"))
    revisions, latest = {}, {}
    for template in data["templates"]:
        key = (template["id"], template["revision"])
        if key in revisions or template.get("category") != "wzos_printable":
            raise ValueError(f"Invalid or duplicate form template {key}")
        keys = [f["key"] for s in template["sections"] for f in s["fields"]]
        if len(keys) != len(set(keys)) or any(f["type"] not in FIELD_TYPES for s in template["sections"] for f in s["fields"]):
            raise ValueError(f"Invalid fields in form template {key}")
        revisions[key] = {**template, "checksum": checksum(template)}
        latest[template["id"]] = max(latest.get(template["id"], 0), template["revision"])
    return revisions, latest


class LibraryItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    expected_version: int = Field(ge=0, strict=True)
    title: str = Field(min_length=1, max_length=120)
    category: Literal["official_agency_form", "company_form"]
    description: str = Field(default="", max_length=500)
    file_id: UUID | None = None


class Removal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=1, strict=True)


def register(app, connect, actor, actors, file_storage_enabled=False, catalog_path=None):
    revisions, latest = load_catalog(catalog_path)
    # module_records is created by modules.register; workspace_files by files.register.

    def names(selected):
        return {k: v.get("name") or k for k, v in actors(selected).items() if v.get("organization_id") == selected["organization_id"]}

    def summary(template):
        return {k: template.get(k) for k in ("id", "revision", "title", "category", "summary", "provenance", "print_notice", "checksum")}

    def present(row, file, people):
        item = json.loads(row["payload"])
        return {"id": row["id"], "version": row["version"], "updated_at": row["updated_at"], "title": item["title"],
                "category": item["category"], "category_label": LIBRARY_CATEGORIES[item["category"]],
                "description": item.get("description", ""), "added_by": people.get(row["owner_id"], row["owner_id"]),
                "file": {k: file[k] for k in ("id", "filename", "content_type", "size_bytes", "sha256")} if file else None,
                "verified_by_wzos": False}

    def current_file(db, selected, item_id, file_id):
        if not file_id or not file_storage_enabled:
            return None
        return db.execute("SELECT * FROM workspace_files WHERE id=? AND organization_id=? AND entity_kind='form_library' AND entity_id=?",
                          (file_id, selected["organization_id"], item_id)).fetchone()

    def require_admin(selected):
        if selected["role"] != "admin":
            raise HTTPException(403, "Only an organization admin can manage team forms")

    @app.get("/forms-hub.js")
    def forms_script():
        return FileResponse(STATIC / "forms-hub.js", media_type="text/javascript")

    @app.get("/forms-hub.css")
    def forms_styles():
        return FileResponse(STATIC / "forms-hub.css", media_type="text/css")

    @app.get("/api/forms/templates")
    def templates(request: Request):
        actor(request)
        items = [{**summary(revisions[(tid, rev)])} for tid, rev in latest.items()]
        return {"items": sorted(items, key=lambda t: t["title"]), "saved_on_server": False}

    @app.get("/api/forms/templates/{template_id}/{revision}")
    def template_detail(template_id: str, revision: int, request: Request):
        actor(request)
        template = revisions.get((template_id, revision))
        if not template:
            raise HTTPException(404, "Template revision not found")
        return {**template, "latest_revision": latest[template_id]}

    @app.get("/api/forms/library")
    def library(request: Request):
        selected = actor(request)
        admin = selected["role"] == "admin"
        people = names(selected)
        with connect() as db:
            rows = db.execute("SELECT * FROM module_records WHERE organization_id=? AND kind='form_library' ORDER BY updated_at DESC, id LIMIT 200",
                              (selected["organization_id"],)).fetchall()
            items = []
            for row in rows:
                payload = json.loads(row["payload"])
                if payload.get("removed"):
                    continue
                file = current_file(db, selected, row["id"], payload.get("file_id"))
                if file or admin:  # members only see forms they can download
                    items.append(present(row, file, people))
        return {"items": items, "can_manage": admin, "uploads_enabled": admin and file_storage_enabled}

    @app.put("/api/forms/library/{item_id}")
    def save_item(item_id: UUID, body: LibraryItem, request: Request):
        selected = actor(request)
        require_admin(selected)
        record = {"title": body.title, "category": body.category, "description": body.description,
                  "file_id": str(body.file_id) if body.file_id else None, "removed": False}
        serialized = json.dumps(record, sort_keys=True)
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM module_records WHERE organization_id=? AND kind='form_library' AND id=?",
                             (selected["organization_id"], str(item_id))).fetchone()
            if row and json.loads(row["payload"]).get("removed"):
                raise HTTPException(404, "Team form not found")
            if body.file_id and not current_file(db, selected, str(item_id), str(body.file_id)):
                raise HTTPException(422, "Upload the file to this team form before attaching it")
            version = row["version"] if row else 0
            if row and row["payload"] == serialized and body.expected_version == version - 1:
                return present(row, current_file(db, selected, row["id"], record["file_id"]), names(selected))  # identical retry
            if body.expected_version != version:
                raise HTTPException(409, "This team form changed. Reload before editing.")
            stamp = datetime.now(timezone.utc).isoformat()
            if row:
                db.execute("INSERT INTO module_revisions VALUES (?,?,?,?,?,?,?) ON CONFLICT DO NOTHING",
                           (selected["organization_id"], "form_library", str(item_id), row["version"], row["payload"], row["owner_id"], row["updated_at"]))
            db.execute("INSERT INTO module_revisions VALUES (?,?,?,?,?,?,?)",
                       (selected["organization_id"], "form_library", str(item_id), version + 1, serialized, selected["id"], stamp))
            db.execute("INSERT INTO module_records VALUES (?,?,?,?,?,?,?) ON CONFLICT(organization_id,kind,id) DO UPDATE SET version=excluded.version,payload=excluded.payload,updated_at=excluded.updated_at",
                       (str(item_id), "form_library", selected["organization_id"], row["owner_id"] if row else selected["id"], version + 1, serialized, stamp))
            saved = db.execute("SELECT * FROM module_records WHERE organization_id=? AND kind='form_library' AND id=?",
                               (selected["organization_id"], str(item_id))).fetchone()
            return present(saved, current_file(db, selected, str(item_id), record["file_id"]), names(selected))

    @app.post("/api/forms/library/{item_id}/remove")
    def remove_item(item_id: UUID, body: Removal, request: Request):
        """Hide a team form from the library. Its stored file is retained (no delete API exists yet)."""
        selected = actor(request)
        require_admin(selected)
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM module_records WHERE organization_id=? AND kind='form_library' AND id=?",
                             (selected["organization_id"], str(item_id))).fetchone()
            if not row:
                raise HTTPException(404, "Team form not found")
            payload = json.loads(row["payload"])
            if payload.get("removed"):
                if body.expected_version == row["version"] - 1:
                    return {"removed": True, "version": row["version"]}  # identical retry
                raise HTTPException(404, "Team form not found")
            if body.expected_version != row["version"]:
                raise HTTPException(409, "This team form changed. Reload before removing it.")
            stamp = datetime.now(timezone.utc).isoformat()
            serialized = json.dumps({**payload, "removed": True}, sort_keys=True)
            db.execute("INSERT INTO module_revisions VALUES (?,?,?,?,?,?,?) ON CONFLICT DO NOTHING",
                       (selected["organization_id"], "form_library", str(item_id), row["version"], row["payload"], row["owner_id"], row["updated_at"]))
            db.execute("INSERT INTO module_revisions VALUES (?,?,?,?,?,?,?)",
                       (selected["organization_id"], "form_library", str(item_id), row["version"] + 1, serialized, selected["id"], stamp))
            db.execute("UPDATE module_records SET version=?,payload=?,updated_at=? WHERE organization_id=? AND kind='form_library' AND id=?",
                       (row["version"] + 1, serialized, stamp, selected["organization_id"], str(item_id)))
            return {"removed": True, "version": row["version"] + 1}
