"""Local-only, append-only project revisions. No customer authorization is implemented."""
import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Query
from uuid import UUID

from shared.projects import ProjectDraft, ProjectUpdate
from services.v2.knowledge.models import ROOT
from services.v2.planning import discover


class ProjectMissing(Exception):
    pass


class ProjectConflict(Exception):
    pass


def canonical(draft):
    return json.dumps(draft.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))


def evidence_review(draft):
    issues = []
    for evidence in draft.evidence:
        if evidence.observed_on is None:
            issues.append(f"{evidence.id}: observation/capture date is unknown.")
        elif evidence.observed_on > datetime.now(timezone.utc).date():
            issues.append(f"{evidence.id}: future observation/capture date needs correction or explanation.")
        if evidence.observed_on and draft.intake.project_date and evidence.observed_on > draft.intake.project_date:
            issues.append(f"{evidence.id}: evidence postdates the work date; confirm its relevance.")
        if evidence.kind == "imagery" and evidence.image_type == "generated_illustration":
            issues.append(f"{evidence.id}: generated illustration cannot establish actual site conditions.")
        if evidence.kind == "speed" and evidence.speed_type == "posted" and draft.intake.site.speed_limit_mph is not None:
            if evidence.value_mph != draft.intake.site.speed_limit_mph:
                issues.append(f"{evidence.id}: posted-speed evidence differs from the intake speed; resolve the discrepancy.")
    kinds = {e.kind for e in draft.evidence}
    visual_outputs = set(draft.intake.requested_outputs) & {"work_zone_setup", "annotated_image", "traffic_overlay"}
    if visual_outputs:
        if not any(e.kind == "speed" and e.speed_type == "posted" for e in draft.evidence):
            issues.append("Posted-speed evidence is missing; other speed types are not substitutes.")
        if "traffic" not in kinds:
            issues.append("Traffic evidence is missing.")
        if not any(e.kind == "imagery" and e.image_type != "generated_illustration" for e in draft.evidence):
            issues.append("Actual-site imagery reference is missing.")
    issues.append("All evidence remains customer-supplied and unverified. No source-reference URLs or files were fetched.")
    issues.append("Imagery entries are references only; image bytes and declared hashes have not been checked.")
    issues.append("Source applicability, road geometry, and field-use approval still require qualified review.")
    return {"verification_status": "not_verified", "approved_for_field_use": False,
            "issues": issues, "pending_applicability_notes": len(draft.applicability_notes)}


class ProjectStore:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else ROOT / ".local-data" / "projects" / "projects.sqlite"

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS revisions(project_id TEXT, version INTEGER, created_at TEXT, payload TEXT, sha256 TEXT, PRIMARY KEY(project_id,version))")
            db.execute("CREATE TABLE IF NOT EXISTS create_keys(key TEXT PRIMARY KEY, payload_sha256 TEXT, project_id TEXT)")

    @staticmethod
    def record(row):
        if hashlib.sha256(row[3].encode()).hexdigest() != row[4]:
            raise sqlite3.DatabaseError("Stored project checksum mismatch")
        try:
            draft = ProjectDraft.model_validate_json(row[3])
        except ValueError as error:
            raise sqlite3.DatabaseError("Stored project validation failed") from error
        return {"workspace_kind": "local_development", "project_id": row[0], "version": row[1],
                "saved_at": row[2], "sha256": row[4], "draft": draft.model_dump(mode="json"),
                "evidence_review_as_of": datetime.now(timezone.utc).date().isoformat(),
                "evidence_review": evidence_review(draft)}

    def get(self, project_id, version=None):
        if not self.path.exists():
            raise ProjectMissing()
        with closing(sqlite3.connect(self.path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
            sql = "SELECT project_id,version,created_at,payload,sha256 FROM revisions WHERE project_id=?"
            params = [str(project_id)]
            if version is not None:
                sql += " AND version=?"
                params.append(version)
            row = db.execute(sql + " ORDER BY version DESC LIMIT 1", params).fetchone()
        if row is None:
            raise ProjectMissing()
        return self.record(row)

    def create(self, draft, key):
        self.initialize()
        payload = canonical(draft)
        digest = hashlib.sha256(payload.encode()).hexdigest()
        with closing(sqlite3.connect(self.path, timeout=10)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT payload_sha256,project_id FROM create_keys WHERE key=?", (key,)).fetchone()
            if old:
                if old[0] != digest:
                    raise ProjectConflict("idempotency_key_reused_with_different_content")
                project_id = old[1]
            else:
                project_id = str(uuid4())
                db.execute("INSERT INTO revisions VALUES(?,?,?,?,?)",
                           (project_id, 1, datetime.now(timezone.utc).isoformat(), payload, digest))
                db.execute("INSERT INTO create_keys VALUES(?,?,?)", (key, digest, project_id))
        return self.get(project_id, 1)

    def update(self, project_id, draft, expected_version):
        if not self.path.exists():
            raise ProjectMissing()
        payload = canonical(draft)
        digest = hashlib.sha256(payload.encode()).hexdigest()
        with closing(sqlite3.connect(self.path, timeout=10)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT max(version) FROM revisions WHERE project_id=?", (str(project_id),)).fetchone()
            if row[0] is None:
                raise ProjectMissing()
            if row[0] != expected_version:
                raise ProjectConflict("project_changed_reload_before_saving")
            db.execute("INSERT INTO revisions VALUES(?,?,?,?,?)",
                       (str(project_id), expected_version + 1, datetime.now(timezone.utc).isoformat(), payload, digest))
        return self.get(project_id, expected_version + 1)

    def list(self, limit, offset):
        if not self.path.exists():
            return {"total": 0, "results": [], "limit": limit, "offset": offset}
        with closing(sqlite3.connect(self.path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
            total = db.execute("SELECT count(DISTINCT project_id) FROM revisions").fetchone()[0]
            rows = db.execute("SELECT r.project_id,r.version,r.created_at,r.payload,r.sha256 FROM revisions r JOIN (SELECT project_id,max(version) version FROM revisions GROUP BY project_id) latest USING(project_id,version) ORDER BY r.created_at DESC,r.project_id LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        records = [self.record(row) for row in rows]
        return {"total": total, "limit": limit, "offset": offset,
                "results": [{"project_id": r["project_id"], "version": r["version"], "saved_at": r["saved_at"], "name": r["draft"]["name"]} for r in records]}


def project_router(projects, knowledge):
    router = APIRouter()

    def validate_notes(draft):
        for note in draft.applicability_notes:
            if note.source_id not in knowledge.catalog or note.revision not in {r["revision"] for r in knowledge.revisions(note.source_id)}:
                raise HTTPException(422, "applicability_note_requires_a_preserved_source_revision")

    @router.post("/v2/projects", status_code=201)
    def create(draft: ProjectDraft, idempotency_key: str = Header(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")):
        validate_notes(draft)
        return projects.create(draft, idempotency_key)

    @router.get("/v2/projects")
    def list_projects(limit: int = Query(20, ge=1, le=50), offset: int = Query(0, ge=0)):
        return projects.list(limit, offset)

    @router.get("/v2/projects/{project_id}")
    def get(project_id: UUID, version: int | None = Query(None, ge=1)):
        return projects.get(project_id, version)

    @router.put("/v2/projects/{project_id}")
    def update(project_id: UUID, request: ProjectUpdate):
        draft = ProjectDraft.model_validate(request.model_dump(exclude={"expected_version"}))
        validate_notes(draft)
        return projects.update(project_id, draft, request.expected_version)

    @router.get("/v2/projects/{project_id}/references")
    def references(project_id: UUID):
        record = projects.get(project_id)
        draft = ProjectDraft.model_validate(record["draft"])
        return {"project_id": str(project_id), "version": record["version"],
                "references": discover(draft.intake, knowledge)}

    return router
