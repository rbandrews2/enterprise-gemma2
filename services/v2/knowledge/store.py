"""Immutable originals and revision manifests; SQLite is a disposable read index."""
import hashlib
import getpass
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import httpx

from .download import DownloadError, download
from .models import DATA, ROOT, Source, load_catalog


class IndexUnavailable(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


class Store:
    def __init__(self, data: Path = DATA, catalog: dict[str, Source] | None = None):
        self.data = Path(data)
        self.catalog = load_catalog() if catalog is None else catalog

    def revisions(self, source_id):
        current_path = self.data / "current" / f"{source_id}.json"
        current = json.loads(current_path.read_text())["revision"] if current_path.exists() else None
        return sorted(
            (json.loads(p.read_text(encoding="utf-8")) for p in
             (self.data / "revisions" / source_id).glob("*/manifest.json")),
            key=lambda x: (x["revision"] == current, x["retrieved_at"]), reverse=True,
        )

    def detail(self, source_id):
        source = self.catalog[source_id]
        attempt_path = self.data / "attempts" / f"{source_id}.json"
        revisions = self.revisions(source_id)
        return {"source": source.model_dump(mode="json"), "revisions": revisions,
                "ingestion": json.loads(attempt_path.read_text()) if attempt_path.exists()
                else {"status": "not_downloaded"},
                "review_status": revisions[0]["review_status"] if revisions else "unreviewed"}

    def ingest(self, source_id, client=None):
        source = self.catalog[source_id]
        attempt = {"attempted_at": now(), "status": "unavailable"}
        try:
            if client is None:
                with httpx.Client(trust_env=False, headers={"User-Agent": "WZOS-Reference-Ingestion/0.1"}) as own:
                    content, final_url = download(source, own)
            else:
                content, final_url = download(source, client)
            digest = hashlib.sha256(content).hexdigest()
            folder = self.data / "revisions" / source_id / digest
            folder.mkdir(parents=True, exist_ok=True)
            manifest_path = folder / "manifest.json"
            if manifest_path.exists():
                attempt.update(status="unchanged", revision=digest)
            else:
                original = folder / f"original.{source.kind}"
                original.write_bytes(content)
                extracted = folder / "extracted.json"
                result = {"passages": [], "warnings": ["extraction_failed_manual_review_required"]}
                extraction_state = "failed"
                try:
                    subprocess.run(
                        [sys.executable, "-m", "services.v2.knowledge.extract", str(original.resolve()),
                         source.kind, str(extracted.resolve())],
                        cwd=ROOT, check=True, timeout=120, capture_output=True,
                    )
                    result = json.loads(extracted.read_text(encoding="utf-8"))
                    extraction_state = "extracted" if result["passages"] else "needs_review"
                except (subprocess.SubprocessError, ValueError, OSError):
                    write_json(extracted, result)
                manifest = {
                    "source": source.model_dump(mode="json"), "revision": digest,
                    "retrieved_at": now(), "final_url": final_url,
                    "downloaded": True, "extraction_state": extraction_state,
                    "extraction_checked": False, "applicability_reviewed": False,
                    "review_status": "unreviewed", "review_note": None,
                    "passage_count": len(result["passages"]), "warnings": result["warnings"],
                    "extracted_sha256": hashlib.sha256(extracted.read_bytes()).hexdigest(),
                }
                write_json(manifest_path, manifest)
                attempt.update(status=extraction_state, revision=digest)
            write_json(self.data / "current" / f"{source_id}.json", {"revision": digest})
        except (DownloadError, httpx.HTTPError, ValueError) as error:
            attempt["error"] = str(error) if isinstance(error, DownloadError) else type(error).__name__
        write_json(self.data / "attempts" / f"{source_id}.json", attempt)
        return attempt

    def check_extraction(self, source_id, revision, note):
        if source_id not in self.catalog or not re.fullmatch(r"[a-f0-9]{64}", revision):
            raise ValueError("Unknown source or invalid revision")
        if len(note.strip()) < 20:
            raise ValueError("Record the sampled pages/sections and findings")
        path = self.data / "revisions" / source_id / revision / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest["extraction_state"] != "extracted":
            raise ValueError("No successful extraction to check")
        manifest.update(extraction_checked=True, review_status="extraction_checked",
                        review_note=note.strip(), extraction_checked_at=now(),
                        extraction_checked_by=getpass.getuser())
        write_json(path, manifest)

    def retry_extraction(self, source_id, revision):
        if source_id not in self.catalog or not re.fullmatch(r"[a-f0-9]{64}", revision):
            raise ValueError("Unknown source or invalid revision")
        folder = self.data / "revisions" / source_id / revision
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        if manifest["extraction_state"] not in {"failed", "needs_review"}:
            raise ValueError("Only failed or empty extractions can be retried")
        original = folder / f"original.{manifest['source']['kind']}"
        if hashlib.sha256(original.read_bytes()).hexdigest() != revision:
            raise ValueError("Original document integrity failure")
        output = folder / "retry-extracted.json"
        subprocess.run([sys.executable, "-m", "services.v2.knowledge.extract", str(original.resolve()),
                        manifest["source"]["kind"], str(output.resolve())],
                       cwd=ROOT, check=True, timeout=120, capture_output=True)
        result = json.loads(output.read_text(encoding="utf-8"))
        if not result["passages"]:
            raise ValueError("Retry still contains no searchable text")
        write_json(folder / "failed-extraction-manifest.json", manifest)
        output.replace(folder / "extracted.json")
        manifest.update(extraction_state="extracted", passage_count=len(result["passages"]),
                        warnings=result["warnings"], extraction_retried_at=now(),
                        extracted_sha256=hashlib.sha256((folder / "extracted.json").read_bytes()).hexdigest())
        write_json(folder / "manifest.json", manifest)
        write_json(self.data / "attempts" / f"{source_id}.json",
                   {"attempted_at": now(), "status": "extracted", "revision": revision})

    def rebuild(self):
        self.data.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix="index-", suffix=".sqlite", dir=self.data)
        os.close(fd)
        try:
            with closing(sqlite3.connect(temp)) as db, db:
                db.execute("CREATE TABLE passages (id INTEGER PRIMARY KEY, source_id TEXT, agency TEXT, revision TEXT, page INTEGER, section TEXT, url TEXT, text TEXT, review_status TEXT, publication_status TEXT, is_latest INTEGER, metadata TEXT)")
                db.execute("CREATE VIRTUAL TABLE search USING fts5(text, content='passages', content_rowid='id')")
                for source_id in self.catalog:
                    revisions = self.revisions(source_id)
                    for index, manifest in enumerate(revisions):
                        revision = manifest["revision"]
                        if not re.fullmatch(r"[a-f0-9]{64}", revision):
                            raise ValueError("Invalid revision")
                        folder = self.data / "revisions" / source_id / revision
                        source = Source.model_validate(manifest["source"])
                        if source.id != source_id:
                            raise ValueError("Revision source mismatch")
                        if hashlib.sha256((folder / f"original.{source.kind}").read_bytes()).hexdigest() != revision:
                            raise ValueError("Original document integrity failure")
                        extracted = (folder / "extracted.json").read_bytes()
                        if hashlib.sha256(extracted).hexdigest() != manifest["extracted_sha256"]:
                            raise ValueError("Extraction integrity failure")
                        for item in json.loads(extracted)["passages"]:
                            url = manifest["final_url"]
                            if item["page"]:
                                url += f"#page={item['page']}"
                            elif item["anchor"]:
                                url += "#" + quote(item["anchor"], safe="")
                            metadata = {key: manifest.get(key) for key in (
                                "retrieved_at", "extraction_checked", "applicability_reviewed", "warnings")}
                            metadata.update({key: manifest["source"].get(key) for key in (
                                "title", "edition", "jurisdiction", "effective_from", "effective_to", "applicability_note")})
                            db.execute("INSERT INTO passages(source_id,agency,revision,page,section,url,text,review_status,publication_status,is_latest,metadata) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                                       (source_id, source.agency, revision, item["page"], item["section"], url,
                                        item["text"], manifest["review_status"], self.catalog[source_id].publication_status,
                                        int(index == 0), json.dumps(metadata)))
                db.execute("INSERT INTO search(search) VALUES('rebuild')")
                count = db.execute("SELECT count(*) FROM passages").fetchone()[0]
            Path(temp).replace(self.data / "index.sqlite")
            return count
        finally:
            Path(temp).unlink(missing_ok=True)

    def indexed_revisions(self):
        path = self.data / "index.sqlite"
        if not path.exists():
            raise IndexUnavailable("index_not_built")
        try:
            with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
                return dict(db.execute("SELECT DISTINCT source_id,revision FROM passages WHERE is_latest=1"))
        except sqlite3.DatabaseError as error:
            raise IndexUnavailable("index_unavailable_rebuild_required") from error

    def search(self, query, agency=None, source_id=None, limit=20, offset=0, latest_only=False):
        tokens = re.findall(r"\w+", query, flags=re.UNICODE)
        if not tokens or len(query) > 500 or not 1 <= limit <= 50 or offset < 0:
            raise ValueError("Invalid search parameters")
        path = self.data / "index.sqlite"
        if not path.exists():
            raise IndexUnavailable("index_not_built")
        # Literal terms, never caller-supplied FTS syntax or SQL.
        match = " AND ".join('"' + term + '"' for term in tokens)
        where, params = ["search MATCH ?"], [match]
        if latest_only:
            where.append("p.is_latest = 1")
        if agency:
            where.append("p.agency = ?")
            params.append(agency)
        if source_id:
            where.append("p.source_id = ?")
            params.append(source_id)
        sql = " FROM search JOIN passages p ON search.rowid=p.id WHERE " + " AND ".join(where)
        try:
            with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
                db.row_factory = sqlite3.Row
                total = db.execute("SELECT count(*)" + sql, params).fetchone()[0]
                rows = db.execute("SELECT p.*, bm25(search) AS rank" + sql +
                                  " ORDER BY rank,p.source_id,p.revision,p.id LIMIT ? OFFSET ?",
                                  [*params, limit, offset]).fetchall()
                results = []
                for row in rows:
                    item = dict(row)
                    item.update(json.loads(item.pop("metadata")))
                    item["is_latest"] = bool(item["is_latest"])
                    results.append(item)
                return {"status": "ok" if total else "empty", "total": total,
                        "limit": limit, "offset": offset,
                        "notice": "Reference passages only; applicability is not determined. PDF page numbers are physical file pages. Consult the original for figures and tables.",
                        "results": results}
        except sqlite3.DatabaseError as error:
            raise IndexUnavailable("index_unavailable_rebuild_required") from error
