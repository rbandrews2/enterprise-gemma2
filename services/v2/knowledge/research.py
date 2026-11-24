"""Bounded official-source watch. Discovery never changes approved Atlas evidence.

Run once daily from an operator-controlled scheduler with persistent --state.
No model calls, user questions, credentials, ingestion, or publication.
"""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urljoin

import httpx

from .download import download, DownloadError
from .models import DATA, approved_url, load_catalog

WATCH_IDS = (
    "vdot-vwapm-2026", "vdot-field-guide-2026", "vdot-known-errors",
    "vdot-mutcd-11", "vdot-mutcd-known-errors-20261110", "fhwa-mutcd-11-r1",
)


class Links(HTMLParser):
    def __init__(self, base):
        super().__init__()
        self.base = base
        self.links = set()

    def handle_starttag(self, tag, attrs):
        if tag != "a" or len(self.links) >= 500:
            return
        href = dict(attrs).get("href")
        if not href:
            return
        url = urldefrag(urljoin(self.base, href))[0]
        try:
            approved_url(url)
        except ValueError:
            return
        self.links.add(url)


def targets(catalog):
    """Explicit traffic-control scope; publication pages also catch renamed PDFs."""
    found = {}
    for sid in WATCH_IDS:
        source = catalog[sid]
        if source.origin != "official" or source.kind not in {"pdf", "html"}:
            raise ValueError("Watch sources must be official PDF or HTML")
        found[source.url] = source
        if source.publication_page not in found:
            found[source.publication_page] = source.model_copy(update={
                "url": source.publication_page, "kind": "html", "allowed_redirects": [],
            })
    return list(found.values())


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def run(root, sources, client, *, now=None, max_bytes=100 * 1024 * 1024, archived_bytes=0):
    """Single writer, once per 24 hours; failures retain last successful baseline."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    lock = root / "running.lock"
    try:
        fd = lock.open("x")
    except FileExistsError:
        return {"status": "already_running"}
    try:
        fd.close()
        state_path = root / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"sources": {}}
        now = time.time() if now is None else now
        # Calendar day avoids skipped runs from scheduler jitter or DST changes.
        if state.get("last_run") and datetime.fromtimestamp(now, timezone.utc).date() == datetime.fromtimestamp(state["last_run"], timezone.utc).date():
            return {"status": "not_due"}
        stamp = datetime.fromtimestamp(now, timezone.utc).isoformat()
        results = []
        started = time.monotonic()
        for source in sources[:16]:
            stored_bytes = sum(p.stat().st_size for p in (root / "candidates").rglob("*") if p.is_file())
            if archived_bytes + stored_bytes + max_bytes > 512 * 1024 * 1024:
                results.append({"status": "deferred", "reason": "archive_storage_budget"})
                break
            if time.monotonic() - started > 240:
                results.append({"status": "deferred", "reason": "run_time_budget"})
                break
            key = hashlib.sha256(source.url.encode()).hexdigest()
            previous = state["sources"].get(key)
            try:
                data, final_url = download(source, client, max_bytes=max_bytes)
                digest = hashlib.sha256(data).hexdigest()
                result = {"url": source.url, "fetched_url": final_url,
                          "sha256": digest, "checked_at": stamp}
                if previous and previous["sha256"] == digest:
                    result["status"] = "unchanged"
                else:
                    result["status"] = "changed_pending_review" if previous else "baseline_unreviewed"
                    result["previous_sha256"] = previous["sha256"] if previous else None
                    directory = root / "candidates" / key / digest
                    directory.mkdir(parents=True, exist_ok=True)
                    (directory / ("source.pdf" if source.kind == "pdf" else "source.html")).write_bytes(data)
                    if source.kind == "html":
                        parser = Links(final_url)
                        parser.feed(data.decode("utf-8", errors="replace"))
                        result["official_links_for_review"] = sorted(parser.links)
                    write_json(directory / "discovery.json", result)
                state["sources"][key] = {"sha256": digest, "checked_at": stamp, "url": source.url}
                results.append(result)
            except (DownloadError, httpx.HTTPError, ValueError) as exc:
                # Do not log arbitrary response content or exception URLs.
                reason = str(exc) if isinstance(exc, DownloadError) else type(exc).__name__
                results.append({"url": source.url, "status": "check_failed", "error": reason})
        state["last_run"] = now
        write_json(state_path, state)
        report = {"status": "completed", "checked_at": stamp, "results": results}
        write_json(root / "latest.json", report)
        return report
    finally:
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=DATA / "research")
    args = parser.parse_args()
    with httpx.Client(headers={"User-Agent": "WZOS-Atlas-SourceWatch/1.0"}, trust_env=False) as client:
        result = run(args.state, targets(load_catalog()), client)
    print(json.dumps(result, indent=2))
    return int(any(r["status"] in {"check_failed", "deferred"} for r in result.get("results", [])))


if __name__ == "__main__":
    raise SystemExit(main())
