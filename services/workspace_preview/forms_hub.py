"""Forms Hub: a customer form library for download and print.

Two sources:
- Built-in WZOS printable forms from forms_catalog.json. Users may type into them
  on screen before printing or downloading; nothing is stored on the server.
- Team forms added by organization admins: an uploaded file (PDF, PNG, JPEG, Word
  .docx or Excel .xlsx) or a link to a Google Doc, Sheet, Form or Drive file.
  Metadata lives in module_records (kind='form_library'); files use the existing
  private file store via /api/files with entity_kind='form_library'.
Every member of the organization can list and download its team forms. Admins can
permanently delete a team form together with its stored files. WZOS does not
verify, edit or determine the applicability of team forms.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CATALOG = Path(__file__).with_name("forms_catalog.json")
STATIC = Path(__file__).with_name("static")
FIELD_TYPES = {"text", "textarea", "select", "multiselect", "date", "time", "number", "rows"}
LIBRARY_CATEGORIES = {"official_agency_form": "Official agency form", "company_form": "Company form"}
# Google links: (host, path pattern, service, [(download label, export URL template)]).
GOOGLE_LINKS = [
    ("docs.google.com", r"/document/d/([\w-]{10,200})(?:/|$)", "Google Docs",
     [("PDF", "https://docs.google.com/document/d/{id}/export?format=pdf"), ("Word", "https://docs.google.com/document/d/{id}/export?format=docx")]),
    ("docs.google.com", r"/spreadsheets/d/([\w-]{10,200})(?:/|$)", "Google Sheets",
     [("PDF", "https://docs.google.com/spreadsheets/d/{id}/export?format=pdf"), ("Excel", "https://docs.google.com/spreadsheets/d/{id}/export?format=xlsx")]),
    ("docs.google.com", r"/forms/d/(?:e/)?([\w-]{10,200})(?:/|$)", "Google Forms", []),
    ("drive.google.com", r"/file/d/([\w-]{10,200})(?:/|$)", "Google Drive", [("File", "https://drive.google.com/uc?export=download&id={id}")]),
]


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


def google_link(url):
    """Normalize a Google Docs/Sheets/Forms/Drive link, or raise ValueError. Returns (url, service, downloads)."""
    parts = urlsplit(url.strip())
    if parts.scheme != "https" or parts.username or parts.password or parts.port or "\\" in url or not parts.hostname:
        raise ValueError("Use an https link from Google Docs, Sheets, Forms or Drive")
    for host, pattern, service, exports in GOOGLE_LINKS:
        match = re.match(pattern, parts.path)
        if parts.hostname == host and match:
            normalized = urlunsplit(("https", host, parts.path, parts.query, ""))
            return normalized, service, [{"label": label, "url": template.format(id=match.group(1))} for label, template in exports]
    raise ValueError("Use a link to a Google Doc, Sheet, Form or Drive file")


class LibraryItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    expected_version: int = Field(ge=0, strict=True)
    title: str = Field(min_length=1, max_length=120)
    category: Literal["official_agency_form", "company_form"]
    description: str = Field(default="", max_length=500)
    file_id: UUID | None = None
    link: str | None = Field(default=None, max_length=500)

    @field_validator("link")
    @classmethod
    def valid_link(cls, value):
        return google_link(value)[0] if value else None

    @model_validator(mode="after")
    def one_source(self):
        if self.file_id and self.link:
            raise ValueError("A team form is either an uploaded file or a Google link, not both")
        return self


class Deletion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=1, strict=True)


# Stored files that must be erased are queued in module_records under this kind (id = file id),
# in the same transaction that makes them unreachable. Object storage is only touched after that
# commits, and each object is forgotten only after its deletion succeeds, so a failure at any
# point leaves a queue entry to retry, never a published form pointing at a missing object.
# The generic /api/modules API accepts only "forms" and "schedule", so this kind is internal.
CLEANUP_KIND = "form_library_cleanup"


def library_record(db, organization_id, item_id):
    return db.execute("SELECT * FROM module_records WHERE organization_id=? AND kind='form_library' AND id=?",
                      (organization_id, str(item_id))).fetchone()


def queued_for_cleanup(db, organization_id, file_id):
    return db.execute("SELECT 1 FROM module_records WHERE organization_id=? AND kind=? AND id=?",
                      (organization_id, CLEANUP_KIND, str(file_id))).fetchone() is not None


def file_access(db, user, item_id, file_id=None, write=False):
    """Access rule the shared file API applies to entity_kind='form_library'.
    Admins may use any file of a live team form except files queued for erasure.
    Members may only list or download the current file of a published team form."""
    row = library_record(db, user["organization_id"], item_id)
    item = json.loads(row["payload"]) if row else None
    admin = user["role"] == "admin"
    if not item or item.get("deleting"):
        raise HTTPException(404, "Form not found")
    if write and not admin:
        raise HTTPException(403, "Only an organization admin can upload team forms")
    if not admin and not item.get("file_id"):
        raise HTTPException(404, "Form not found")  # unfinished entries are admin-only
    if file_id is not None and (queued_for_cleanup(db, user["organization_id"], file_id) or (not admin and str(file_id) != item.get("file_id"))):
        raise HTTPException(404, "File not found")


def queue_files(db, organization_id, item_id, keep=None):
    """Queue every stored file of a team form except `keep` for erasure. Call inside the caller's transaction."""
    rows = db.execute("SELECT id,object_key FROM workspace_files WHERE organization_id=? AND entity_kind='form_library' AND entity_id=?",
                      (organization_id, str(item_id))).fetchall()
    stamp = datetime.now(timezone.utc).isoformat()
    for row in rows:
        if row["id"] != keep:
            db.execute("INSERT INTO module_records VALUES (?,?,?,?,?,?,?) ON CONFLICT DO NOTHING",
                       (row["id"], CLEANUP_KIND, organization_id, "system", 1,
                        json.dumps({"entity_id": str(item_id), "object_key": row["object_key"]}, sort_keys=True), stamp))


def forget_file(db, organization_id, file_id):
    """Drop the metadata of a file whose stored object has been erased."""
    db.execute("DELETE FROM workspace_files WHERE id=? AND organization_id=?", (file_id, organization_id))
    db.execute("DELETE FROM module_records WHERE organization_id=? AND kind=? AND id=?", (organization_id, CLEANUP_KIND, file_id))


def register(app, connect, actor, actors, file_store=None, catalog_path=None):
    revisions, latest = load_catalog(catalog_path)
    # module_records is created by modules.register; workspace_files by files.register.

    def names(selected):
        return {k: v.get("name") or k for k, v in actors(selected).items() if v.get("organization_id") == selected["organization_id"]}

    def summary(template):
        return {k: template.get(k) for k in ("id", "revision", "title", "category", "summary", "provenance", "print_notice", "checksum")}

    def present(row, file, people):
        item = json.loads(row["payload"])
        link = None
        if item.get("link"):
            url, service, downloads = google_link(item["link"])
            link = {"url": url, "service": service, "downloads": downloads}
        return {"id": row["id"], "version": row["version"], "updated_at": row["updated_at"], "title": item["title"],
                "category": item["category"], "category_label": LIBRARY_CATEGORIES[item["category"]],
                "description": item.get("description", ""), "added_by": people.get(row["owner_id"], row["owner_id"]),
                "file": {k: file[k] for k in ("id", "filename", "content_type", "size_bytes", "sha256")} if file else None,
                "link": link, "complete": bool(file or link), "verified_by_wzos": False}

    def current_file(db, selected, item_id, file_id):
        """The file a team form points at, unless it is missing or queued for erasure."""
        if not file_id or file_store is None or queued_for_cleanup(db, selected["organization_id"], file_id):
            return None
        return db.execute("SELECT * FROM workspace_files WHERE id=? AND organization_id=? AND entity_kind='form_library' AND entity_id=?",
                          (file_id, selected["organization_id"], item_id)).fetchone()

    def require_admin(selected):
        if selected["role"] != "admin":
            raise HTTPException(403, "Only an organization admin can manage team forms")

    def pending_cleanup(db, organization_id):
        queued = db.execute("SELECT COUNT(*) FROM module_records WHERE organization_id=? AND kind=?", (organization_id, CLEANUP_KIND)).fetchone()[0]
        deleting = sum(1 for r in db.execute("SELECT payload FROM module_records WHERE organization_id=? AND kind='form_library'", (organization_id,)).fetchall()
                       if json.loads(r["payload"]).get("deleting"))
        return queued + deleting

    def item_cleanup_pending(db, organization_id, item_id):
        return any(json.loads(r["payload"])["entity_id"] == str(item_id) for r in db.execute(
                "SELECT payload FROM module_records WHERE organization_id=? AND kind=?", (organization_id, CLEANUP_KIND)).fetchall())

    def run_cleanup(organization_id, limit=50):
        """Erase queued objects, then forget them; finish deleted forms whose files are all gone.
        Idempotent and safe to repeat after any failure or restart. Returns the work still pending."""
        with connect() as db:
            queue = db.execute("SELECT id,payload FROM module_records WHERE organization_id=? AND kind=? ORDER BY updated_at, id LIMIT ?",
                               (organization_id, CLEANUP_KIND, limit)).fetchall()
        for entry in queue if file_store is not None else []:
            try:
                file_store.delete(json.loads(entry["payload"])["object_key"])  # idempotent: a missing object is fine
            except Exception:
                continue  # stays queued; the file is already unreachable
            try:
                with connect() as db:
                    db.execute("BEGIN IMMEDIATE")
                    forget_file(db, organization_id, entry["id"])
            except Exception:
                continue  # object gone but still queued; the next run forgets it
        try:
            with connect() as db:
                db.execute("BEGIN IMMEDIATE")
                waiting = {json.loads(r["payload"])["entity_id"] for r in db.execute(
                    "SELECT payload FROM module_records WHERE organization_id=? AND kind=?", (organization_id, CLEANUP_KIND)).fetchall()}
                for row in db.execute("SELECT id,payload FROM module_records WHERE organization_id=? AND kind='form_library'", (organization_id,)).fetchall():
                    if json.loads(row["payload"]).get("deleting") and row["id"] not in waiting:
                        db.execute("DELETE FROM module_revisions WHERE organization_id=? AND kind='form_library' AND id=?", (organization_id, row["id"]))
                        db.execute("DELETE FROM module_records WHERE organization_id=? AND kind='form_library' AND id=?", (organization_id, row["id"]))
        except Exception:
            pass  # deleted forms stay hidden until a later run finishes them
        with connect() as db:
            return pending_cleanup(db, organization_id)

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
                if payload.get("deleting"):
                    continue  # deleted; erasure may still be finishing
                item = present(row, current_file(db, selected, row["id"], payload.get("file_id")), people)
                if item["complete"] or admin:  # members only see forms they can open or download
                    items.append(item)
            pending = pending_cleanup(db, selected["organization_id"]) if admin else 0
        return {"items": items, "can_manage": admin, "uploads_enabled": admin and file_store is not None, "cleanup_pending": pending}

    @app.post("/api/forms/library/cleanup")
    def cleanup(request: Request):
        """Finish erasing files from earlier deletions or replacements (admin; idempotent)."""
        selected = actor(request)
        require_admin(selected)
        return {"cleanup_pending": run_cleanup(selected["organization_id"])}

    @app.put("/api/forms/library/{item_id}")
    def save_item(item_id: UUID, body: LibraryItem, request: Request):
        selected = actor(request)
        require_admin(selected)
        record = {"title": body.title, "category": body.category, "description": body.description,
                  "file_id": str(body.file_id) if body.file_id else None, "link": body.link}
        serialized = json.dumps(record, sort_keys=True)
        queued = False
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = library_record(db, selected["organization_id"], item_id)
            if row and json.loads(row["payload"]).get("deleting"):
                raise HTTPException(404, "Team form not found")
            if body.file_id and not current_file(db, selected, str(item_id), str(body.file_id)):
                raise HTTPException(422, "Upload the file to this team form before attaching it")
            version = row["version"] if row else 0
            if row and row["payload"] == serialized and body.expected_version == version - 1:
                result = present(row, current_file(db, selected, row["id"], record["file_id"]), names(selected))  # identical retry
                return {**result, "cleanup_pending": item_cleanup_pending(db, selected["organization_id"], item_id)}
            if body.expected_version != version:
                raise HTTPException(409, "This team form changed. Reload before editing.")
            previous = json.loads(row["payload"]) if row else {}
            if row and (previous.get("file_id"), previous.get("link")) != (record["file_id"], record["link"]):
                # Replaced or switched source: the earlier file and any unattached uploads are queued for erasure,
                # becoming unreachable in this same commit. The new file is published either way.
                queue_files(db, selected["organization_id"], item_id, keep=record["file_id"])
                queued = True
            stamp = datetime.now(timezone.utc).isoformat()
            if row:
                db.execute("INSERT INTO module_revisions VALUES (?,?,?,?,?,?,?) ON CONFLICT DO NOTHING",
                           (selected["organization_id"], "form_library", str(item_id), row["version"], row["payload"], row["owner_id"], row["updated_at"]))
            db.execute("INSERT INTO module_revisions VALUES (?,?,?,?,?,?,?)",
                       (selected["organization_id"], "form_library", str(item_id), version + 1, serialized, selected["id"], stamp))
            db.execute("INSERT INTO module_records VALUES (?,?,?,?,?,?,?) ON CONFLICT(organization_id,kind,id) DO UPDATE SET version=excluded.version,payload=excluded.payload,updated_at=excluded.updated_at",
                       (str(item_id), "form_library", selected["organization_id"], row["owner_id"] if row else selected["id"], version + 1, serialized, stamp))
            saved = library_record(db, selected["organization_id"], item_id)
            result = present(saved, current_file(db, selected, str(item_id), record["file_id"]), names(selected))
        if queued:
            run_cleanup(selected["organization_id"])  # best effort after commit; anything left stays queued
        with connect() as db:
            return {**result, "cleanup_pending": item_cleanup_pending(db, selected["organization_id"], item_id)}

    @app.post("/api/forms/library/{item_id}/delete")
    def delete_item(item_id: UUID, body: Deletion, request: Request):
        """Permanently delete a team form. Step 1 (one transaction): hide the form and queue its files.
        Step 2 (after commit): erase the objects, then the metadata and revision history.
        If step 2 is interrupted the form stays deleted and `cleanup_pending` is true; repeating this
        request or POST /api/forms/library/cleanup finishes it. A retry after completion returns 404."""
        selected = actor(request)
        require_admin(selected)
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = library_record(db, selected["organization_id"], item_id)
            if not row:
                raise HTTPException(404, "Team form not found")
            payload = json.loads(row["payload"])
            if not payload.get("deleting"):
                if body.expected_version != row["version"]:
                    raise HTTPException(409, "This team form changed. Reload before deleting it.")
                queue_files(db, selected["organization_id"], item_id)
                db.execute("UPDATE module_records SET version=?,payload=?,updated_at=? WHERE organization_id=? AND kind='form_library' AND id=?",
                           (row["version"] + 1, json.dumps({**payload, "deleting": True}, sort_keys=True), datetime.now(timezone.utc).isoformat(),
                            selected["organization_id"], str(item_id)))
        run_cleanup(selected["organization_id"])
        with connect() as db:
            finishing = library_record(db, selected["organization_id"], item_id) is not None
        return {"deleted": True, "cleanup_pending": finishing}
