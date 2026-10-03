"""Forms Hub: versioned templates, form records, review status, print/export data.

Records reuse module_records/module_revisions (kind='forms') so the Work Zone
Report, attachments and revision history keep working; no new tables. Templates
come from forms_catalog.json. A record pins its template revision and checksum.
Official form references never reproduce or determine applicability of an
agency form; internal worksheets are WZOS working documents.
"""
import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from fastapi import HTTPException, Query, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, ConfigDict, Field

CATALOG = Path(__file__).with_name("forms_catalog.json")
STATIC = Path(__file__).with_name("static")
CATEGORIES = {"internal_worksheet", "official_form_reference"}
FIELD_TYPES = {"text", "textarea", "select", "multiselect", "date", "time", "number", "rows"}
EDITABLE = {"draft", "returned"}
MAX_FIELDS_BYTES = 64 * 1024


def checksum(template):
    return hashlib.sha256(json.dumps(template, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_catalog(path=None):
    """Return {(id, revision): template-with-checksum} and {id: latest revision}; refuse an invalid catalog."""
    data = json.loads(Path(path or CATALOG).read_text(encoding="utf-8"))
    revisions, latest = {}, {}
    for template in data["templates"]:
        key = (template["id"], template["revision"])
        if key in revisions or template["category"] not in CATEGORIES:
            raise ValueError(f"Invalid or duplicate form template {key}")
        if template["category"] == "official_form_reference" and template.get("official_reference", {}).get("official_template_stored") is not False:
            raise ValueError(f"Official form reference {key} must not claim to store the official template")
        keys = [f["key"] for s in template["sections"] for f in s["fields"]]
        if len(keys) != len(set(keys)) or any(f["type"] not in FIELD_TYPES for s in template["sections"] for f in s["fields"]):
            raise ValueError(f"Invalid fields in form template {key}")
        revisions[key] = {**template, "checksum": checksum(template)}
        latest[template["id"]] = max(latest.get(template["id"], 0), template["revision"])
    return revisions, latest


def fields_of(template):
    return [f for s in template["sections"] for f in s["fields"]]


def blank(value):
    return value is None or value == "" or value == []


def clean_fields(template, values):
    """Validate submitted values against the pinned template; drafts may be incomplete."""
    definitions = {f["key"]: f for f in fields_of(template)}
    unknown = sorted(set(values) - set(definitions))
    if unknown:
        raise HTTPException(422, f"Unknown field for this template revision: {unknown[0]}")
    cleaned = {}
    for key, field in definitions.items():
        value = values.get(key, field.get("default"))
        label, kind = field["label"], field["type"]
        if blank(value):
            cleaned[key] = [] if kind in ("multiselect", "rows") else None
            continue
        if kind in ("text", "textarea"):
            if not isinstance(value, str):
                raise HTTPException(422, f"{label} must be text")
            value = value.strip()
            if len(value) > field.get("max_length", 4000 if kind == "textarea" else 200):
                raise HTTPException(422, f"{label} is too long")
        elif kind == "select":
            if value not in field["options"]:
                raise HTTPException(422, f"{label} must be one of the listed options")
        elif kind == "multiselect":
            if not isinstance(value, list) or len(set(value)) != len(value) or not set(value) <= set(field["options"]):
                raise HTTPException(422, f"{label} must use distinct listed options")
            value = [o for o in field["options"] if o in value]
        elif kind == "date":
            try:
                value = date.fromisoformat(value).isoformat() if isinstance(value, str) and len(value) == 10 else None
            except ValueError:
                value = None
            if value is None:
                raise HTTPException(422, f"{label} must be a date (YYYY-MM-DD)")
        elif kind == "time":
            if not isinstance(value, str) or not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", value):
                raise HTTPException(422, f"{label} must be a time (HH:MM)")
        elif kind == "number":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not field.get("min", float("-inf")) <= value <= field.get("max", float("inf")):
                raise HTTPException(422, f"{label} must be a number in the allowed range")
        elif kind == "rows":
            columns = {c["key"]: c for c in field["columns"]}
            if not isinstance(value, list) or len(value) > field["max_rows"]:
                raise HTTPException(422, f"{label} allows at most {field['max_rows']} rows")
            rows = []
            for row in value:
                if not isinstance(row, dict) or not set(row) <= set(columns):
                    raise HTTPException(422, f"{label} rows contain an unknown column")
                entry = {}
                for column_key, column in columns.items():
                    cell = row.get(column_key, "")
                    if not isinstance(cell, str) or len(cell.strip()) > column.get("max_length", 200):
                        raise HTTPException(422, f"{label}: {column['label']} must be short text")
                    entry[column_key] = cell.strip()
                if any(entry.values()):
                    rows.append(entry)
            value = rows
        cleaned[key] = value
    return cleaned


def missing_required(template, values):
    labels = {f["key"]: f["label"] for f in fields_of(template)}
    missing = [{"key": f["key"], "label": f["label"], "message": f"{f['label']} is required"}
               for f in fields_of(template) if f.get("required") and blank(values.get(f["key"]))]
    for rule in template.get("rules", []):
        if rule["type"] == "required_if_any" and any(values.get(k) == rule["equals"] for k in rule["fields"]) and blank(values.get(rule["require"])):
            missing.append({"key": rule["require"], "label": labels[rule["require"]], "message": rule["message"]})
        elif rule["type"] == "not_value":
            for key in rule["fields"]:
                if values.get(key) == rule["value"]:
                    missing.append({"key": key, "label": labels[key], "message": f"{labels[key]}: {rule['message']}"})
    return missing


class FormSave(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    expected_version: int = Field(ge=0, strict=True)
    template_id: str = Field(min_length=1, max_length=60)
    template_revision: int = Field(ge=1, strict=True)
    template_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    title: str = Field(min_length=1, max_length=120)
    location: str = Field(default="", max_length=500)
    order_id: str | None = Field(default=None, max_length=100)
    fields: dict[str, Any] = Field(default_factory=dict)


class FormTransition(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    expected_version: int = Field(ge=1, strict=True)
    action: Literal["submit", "return", "mark_reviewed", "cancel", "reopen"]
    note: str = Field(default="", max_length=1000)


# action: (allowed from statuses, resulting status, admin only)
TRANSITIONS = {
    "submit": ({"draft", "returned"}, "ready_for_review", False),
    "return": ({"ready_for_review"}, "returned", True),
    "mark_reviewed": ({"ready_for_review"}, "reviewed", True),
    "cancel": ({"draft", "returned"}, "cancelled", False),
    "reopen": ({"reviewed", "cancelled"}, "draft", True),
}


def register(app, connect, actor, permitted_row, actors, catalog_path=None):
    revisions, latest = load_catalog(catalog_path)
    # Tables are owned and created by modules.register (module_records/module_revisions).

    def now():
        return datetime.now(timezone.utc).isoformat()

    def names(selected):
        return {k: v.get("name") or k for k, v in actors(selected).items() if v.get("organization_id") == selected["organization_id"]}

    def summary(template):
        return {k: template.get(k) for k in ("id", "revision", "title", "category", "summary", "provenance", "print_notice", "official_reference", "checksum")}

    def template_for(record):
        return revisions.get((record.get("template_id"), record.get("template_revision")))

    def visible(db, selected, record_id):
        clause, params = "organization_id=? AND kind='forms' AND id=?", [selected["organization_id"], str(record_id)]
        if selected["role"] != "admin":
            clause += " AND owner_id=?"
            params.append(selected["id"])
        row = db.execute("SELECT * FROM module_records WHERE " + clause, params).fetchone()
        if not row:
            raise HTTPException(404, "Form not found")
        return row

    def present(row, selected, people):
        record = json.loads(row["payload"])
        template = template_for(record)
        legacy = template is None
        status = record.get("status", "draft")
        owner = row["owner_id"] == selected["id"]
        admin = selected["role"] == "admin"
        missing = [] if legacy else missing_required(template, record.get("fields", {}))
        return {"id": row["id"], "version": row["version"], "updated_at": row["updated_at"], "owner_id": row["owner_id"],
                "owner_name": people.get(row["owner_id"], row["owner_id"]), "title": record.get("title"),
                "location": record.get("location", ""), "order_id": record.get("order_id"), "status": status,
                "legacy": legacy, "legacy_type": record.get("form_type") if legacy else None,
                "legacy_record": {k: record.get(k) for k in ("details", "inspection", "safety")} if legacy else None,
                "template": summary(template) if template else None, "fields": record.get("fields", {}),
                "review": record.get("review"), "missing_required": missing,
                "permissions": {
                    "can_edit": not legacy and status in EDITABLE and (owner or admin),
                    "can_submit": not legacy and status in EDITABLE and (owner or admin) and not missing,
                    "can_cancel": not legacy and status in EDITABLE and (owner or admin),
                    "can_review": not legacy and admin and status == "ready_for_review",
                    "can_reopen": not legacy and admin and status in ("reviewed", "cancelled")}}

    def write(db, selected, record_id, row, record, version):
        serialized = json.dumps(record, sort_keys=True)
        stamp = now()
        if row:
            db.execute("INSERT INTO module_revisions VALUES (?,?,?,?,?,?,?) ON CONFLICT DO NOTHING",
                       (selected["organization_id"], "forms", str(record_id), row["version"], row["payload"], row["owner_id"], row["updated_at"]))
        db.execute("INSERT INTO module_revisions VALUES (?,?,?,?,?,?,?)",
                   (selected["organization_id"], "forms", str(record_id), version, serialized, selected["id"], stamp))
        db.execute("INSERT INTO module_records VALUES (?,?,?,?,?,?,?) ON CONFLICT(organization_id,kind,id) DO UPDATE SET version=excluded.version,payload=excluded.payload,updated_at=excluded.updated_at",
                   (str(record_id), "forms", selected["organization_id"], row["owner_id"] if row else selected["id"], version, serialized, stamp))
        return db.execute("SELECT * FROM module_records WHERE organization_id=? AND kind='forms' AND id=?",
                          (selected["organization_id"], str(record_id))).fetchone()

    @app.get("/forms-hub.js")
    def forms_script():
        return FileResponse(STATIC / "forms-hub.js", media_type="text/javascript")

    @app.get("/forms-hub.css")
    def forms_styles():
        return FileResponse(STATIC / "forms-hub.css", media_type="text/css")

    @app.get("/api/forms/templates")
    def templates(request: Request):
        actor(request)
        items = [{**summary(revisions[(tid, rev)]), "revisions": sorted(r for t, r in revisions if t == tid)} for tid, rev in latest.items()]
        return {"items": sorted(items, key=lambda t: (t["category"] != "internal_worksheet", t["title"]))}

    @app.get("/api/forms/templates/{template_id}/{revision}")
    def template_detail(template_id: str, revision: int, request: Request):
        actor(request)
        template = revisions.get((template_id, revision))
        if not template:
            raise HTTPException(404, "Template revision not found")
        return {**template, "latest_revision": latest[template_id]}

    @app.get("/api/forms")
    def listing(request: Request, q: str = Query("", max_length=100), status: str | None = Query(None, max_length=30),
                category: Literal["internal_worksheet", "official_form_reference", "legacy"] | None = None,
                order_id: str | None = Query(None, max_length=100), offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=50)):
        selected = actor(request)
        clause, params = "organization_id=? AND kind='forms'", [selected["organization_id"]]
        if selected["role"] != "admin":
            clause += " AND owner_id=?"
            params.append(selected["id"])
        if q.strip():
            escaped = q.strip().lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            clause += " AND lower(json_extract(payload,'$.title')) LIKE ? ESCAPE '\\'"
            params.append(f"%{escaped}%")
        if status:
            clause += " AND json_extract(payload,'$.status')=?"
            params.append(status)
        if category == "legacy":
            clause += " AND json_extract(payload,'$.template_id') IS NULL"
        elif category:
            clause += " AND json_extract(payload,'$.template_category')=?"
            params.append(category)
        if order_id:
            clause += " AND json_extract(payload,'$.order_id')=?"
            params.append(order_id)
        with connect() as db:
            total = db.execute("SELECT COUNT(*) FROM module_records WHERE " + clause, params).fetchone()[0]
            rows = db.execute("SELECT * FROM module_records WHERE " + clause + " ORDER BY updated_at DESC, id LIMIT ? OFFSET ?", [*params, limit, offset]).fetchall()
        people = names(selected)
        items = []
        for row in rows:
            item = present(row, selected, people)
            items.append({k: item[k] for k in ("id", "version", "updated_at", "owner_id", "owner_name", "title", "order_id", "status", "legacy", "legacy_type")}
                         | {"template": {k: (item["template"] or {}).get(k) for k in ("id", "revision", "title", "category")} if item["template"] else None,
                            "missing_count": len(item["missing_required"])})
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    @app.get("/api/forms/{record_id}")
    def detail(record_id: UUID, request: Request):
        selected = actor(request)
        with connect() as db:
            row = visible(db, selected, record_id)
        return present(row, selected, names(selected))

    @app.put("/api/forms/{record_id}")
    def save(record_id: UUID, body: FormSave, request: Request):
        selected = actor(request)
        template = revisions.get((body.template_id, body.template_revision))
        if not template:
            raise HTTPException(422, "Unknown form template revision")
        if body.template_checksum != template["checksum"]:
            raise HTTPException(409, "This form template changed. Reload the template before saving.")
        if len(json.dumps(body.fields)) > MAX_FIELDS_BYTES:
            raise HTTPException(413, "Form content is too large")
        values = clean_fields(template, body.fields)
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT * FROM module_records WHERE organization_id=? AND kind='forms' AND id=?",
                                  (selected["organization_id"], str(record_id))).fetchone()
            row = visible(db, selected, record_id) if existing else None
            prior = json.loads(row["payload"]) if row else None
            if prior is not None:
                if "template_id" not in prior:
                    raise HTTPException(409, "Legacy form records are read-only in Forms Hub. Create a new form instead.")
                if (prior["template_id"], prior["template_revision"], prior["template_checksum"]) != (body.template_id, body.template_revision, template["checksum"]):
                    raise HTTPException(409, "A saved form keeps its original template revision")
            elif body.template_revision != latest[body.template_id]:
                raise HTTPException(409, "A newer template revision exists. Reload the form catalog.")
            if body.order_id:
                permitted_row(db, body.order_id, selected)
            record = {"form_type": body.template_id, "template_id": body.template_id, "template_revision": body.template_revision,
                      "template_checksum": template["checksum"], "template_category": template["category"],
                      "title": body.title, "location": body.location, "order_id": body.order_id,
                      "status": prior["status"] if prior else "draft", "review": prior.get("review") if prior else None,
                      "fields": values, "details": f"{template['title']} · template revision {template['revision']}"}
            version = row["version"] if row else 0
            if prior is not None and prior["status"] not in EDITABLE:
                if prior == record and body.expected_version == version - 1:
                    return present(row, selected, names(selected))
                raise HTTPException(409, "This form is locked while in review or after a decision. An admin can return or reopen it.")
            if row and row["payload"] == json.dumps(record, sort_keys=True) and body.expected_version == version - 1:
                return present(row, selected, names(selected))  # identical retry of the last save
            if body.expected_version != version:
                raise HTTPException(409, "This form changed. Reload before editing.")
            if prior and prior["status"] == "returned":
                record["status"] = "draft"
            saved = write(db, selected, record_id, row, record, version + 1)
            return present(saved, selected, names(selected))

    @app.post("/api/forms/{record_id}/status")
    def transition(record_id: UUID, body: FormTransition, request: Request):
        selected = actor(request)
        sources, target, admin_only = TRANSITIONS[body.action]
        if admin_only and selected["role"] != "admin":
            raise HTTPException(403, "Only an admin can review, return or reopen forms")
        if body.action == "return" and len(body.note) < 3:
            raise HTTPException(422, "Explain what needs to change before returning the form")
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = visible(db, selected, record_id)
            record = json.loads(row["payload"])
            template = template_for(record)
            if template is None:
                raise HTTPException(409, "Legacy form records are read-only in Forms Hub")
            review = record.get("review") or {}
            if (record["status"] == target and review.get("action") == body.action and review.get("by") == selected["id"]
                    and review.get("note") == body.note and body.expected_version == row["version"] - 1):
                return present(row, selected, names(selected))  # identical retry
            if body.expected_version != row["version"]:
                raise HTTPException(409, "This form changed. Reload before changing its status.")
            if record["status"] not in sources:
                raise HTTPException(409, f"A {record['status'].replace('_', ' ')} form cannot be changed with this action")
            if body.action == "submit":
                missing = missing_required(template, record["fields"])
                if missing:
                    raise HTTPException(422, "Complete required fields before submitting: " + ", ".join(m["label"] for m in missing[:5]))
            record["status"] = target
            record["review"] = {"action": body.action, "by": selected["id"], "at": now(), "note": body.note}
            saved = write(db, selected, record_id, row, record, row["version"] + 1)
            return present(saved, selected, names(selected))

    def revision_history(db, selected, record_id, people):
        rows = db.execute("SELECT * FROM module_revisions WHERE organization_id=? AND kind='forms' AND id=? ORDER BY version DESC LIMIT 50",
                          (selected["organization_id"], str(record_id))).fetchall()
        items = []
        for current, previous in zip(rows, list(rows[1:]) + [None]):
            record, before = json.loads(current["payload"]), json.loads(previous["payload"]) if previous else {}
            changed = sorted(k for k in set(record.get("fields", {})) | set(before.get("fields", {}))
                             if record.get("fields", {}).get(k) != before.get("fields", {}).get(k))
            items.append({"version": current["version"], "saved_at": current["saved_at"], "author_id": current["author_id"],
                          "author_name": people.get(current["author_id"], current["author_id"]), "status": record.get("status", "draft"),
                          "title": record.get("title"), "template_revision": record.get("template_revision"),
                          "review": record.get("review"), "changed_fields": changed if previous else [],
                          "title_changed": bool(previous) and record.get("title") != before.get("title")})
        return items

    @app.get("/api/forms/{record_id}/history")
    def history(record_id: UUID, request: Request):
        selected = actor(request)
        with connect() as db:
            visible(db, selected, record_id)
            return {"items": revision_history(db, selected, record_id, names(selected))}

    @app.get("/api/forms/{record_id}/export")
    def export(record_id: UUID, request: Request):
        selected = actor(request)
        people = names(selected)
        with connect() as db:
            row = visible(db, selected, record_id)
            items = revision_history(db, selected, record_id, people)
        record = present(row, selected, people)
        record.pop("permissions")
        document = {"export_type": "WZOS Forms Hub record", "exported_at": now(), "exported_by": selected["id"],
                    "official_submission": False, "record": record, "revision_history": items,
                    "notice": (record["template"] or {}).get("print_notice") or "Legacy WZOS draft record."}
        name = re.sub(r"[^A-Za-z0-9._-]+", "-", f"wzos-form-{record['title']}-v{record['version']}")[:120] + ".json"
        return Response(json.dumps(document, indent=2), media_type="application/json",
                        headers={"Content-Disposition": f'attachment; filename="{name}"'})
