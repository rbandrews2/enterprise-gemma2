"""Cloud Run entrypoint: isolated public-source archive, generation-checked lease."""
import json
import os
import tempfile
import time
from pathlib import Path

import httpx
from google.cloud import storage
from google.api_core.exceptions import NotFound, PreconditionFailed

from .models import load_catalog
from .research import run, targets


def execute(bucket):
    lease = bucket.blob("lease.json")
    now = time.time()
    try:
        lease.reload()
        generation = lease.generation
        existing = json.loads(lease.download_as_bytes(if_generation_match=generation))
        if existing["expires"] > now:
            return {"status": "already_running"}
    except NotFound:
        generation = 0
    try:
        lease.upload_from_string(json.dumps({"expires": now + 1800}),
                                 content_type="application/json", if_generation_match=generation)
    except PreconditionFailed:
        return {"status": "already_running"}
    owned_generation = lease.generation
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = bucket.blob("state.json")
            try:
                state.reload()
                state_generation = state.generation
                state.download_to_filename(str(root / "state.json"), if_generation_match=state_generation)
            except NotFound:
                state_generation = 0
            archived_bytes = sum(blob.size or 0 for blob in bucket.list_blobs(prefix="candidates/"))
            with httpx.Client(headers={"User-Agent": "WZOS-Atlas-SourceWatch/1.0"}, trust_env=False) as client:
                result = run(root, targets(load_catalog()), client, archived_bytes=archived_bytes)
            if result["status"] != "completed":
                return result
            for path in (root / "candidates").rglob("*"):
                if path.is_file():
                    blob = bucket.blob(path.relative_to(root).as_posix())
                    try:
                        blob.upload_from_filename(str(path), if_generation_match=0)
                    except PreconditionFailed:
                        # Content-addressed originals; a previously completed upload is reusable.
                        pass
            report = json.dumps(result)
            bucket.blob("runs/" + str(int(now)) + ".json").upload_from_string(
                report, content_type="application/json", if_generation_match=0)
            bucket.blob("latest.json").upload_from_string(report, content_type="application/json")
            # Baseline advances only after all candidate uploads and the report succeed.
            state.upload_from_filename(str(root / "state.json"), if_generation_match=state_generation)
            return result
    finally:
        try:
            lease.delete(if_generation_match=owned_generation)
        except (NotFound, PreconditionFailed):
            pass


def main():
    bucket_name = os.environ["ATLAS_RESEARCH_BUCKET"]
    result = execute(storage.Client().bucket(bucket_name))
    summary = {"status": result["status"], "checked_at": result.get("checked_at"),
               "sources": [{k: r[k] for k in ("url", "status", "error", "reason") if k in r}
                           for r in result.get("results", [])]}
    print(json.dumps(summary), flush=True)
    return int(any(r["status"] in {"check_failed", "deferred"} for r in result.get("results", [])))


if __name__ == "__main__":
    raise SystemExit(main())
