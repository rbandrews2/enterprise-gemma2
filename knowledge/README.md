# Virginia agency reference backend

The approved catalog is `sources.json`. Original documents, extraction results, revision manifests, download attempts, and SQLite live under `.local-data/knowledge/` (excluded from Git and container uploads). This is a local reference library, not an applicability engine or complete safety corpus.

## Setup and operation

Use the repository's Python 3.12 virtual environment and `requirements-v2.txt`.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-v2.txt
.\.venv\Scripts\python.exe -m services.v2.knowledge.cli ingest all
.\.venv\Scripts\python.exe -m services.v2.knowledge.cli ingest vdot-field-guide-2026
.\.venv\Scripts\python.exe -m services.v2.knowledge.cli rebuild
```

Run one ingestion/rebuild operator at a time. The ingestion command exits nonzero for unavailable, failed, or empty documents while retaining successful downloads and rebuilding the usable index. A server-side HTTP 403 remains unavailable; no authentication bypass or substitute source is attempted. New URLs and redirect targets must be explicitly added to the validated official-host catalog before downloading.

Downloads have a 100 MiB decoded-body limit, 30-second network timeouts, a 120-second transfer deadline checked while streaming, and at most three redirects. Extraction runs in a child process with a 120-second limit and a 2,000-page PDF limit. PDFium handles PDF text; Beautiful Soup handles HTML headings. No OCR is performed. Native PDF parsing occurs outside the API process; this is not an OS sandbox.

Retry a failed/empty extraction from its original download:

```powershell
.\.venv\Scripts\python.exe -m services.v2.knowledge.cli retry-extraction SOURCE_ID SHA256_REVISION
```

Successfully extracted revisions cannot be overwritten by that command. A retry preserves the prior failure manifest. Originals are identified by SHA-256; identical downloads do not create duplicate revisions. A remotely reverted document is recorded as the latest download without deleting newer historical copies. Rebuild verifies original and extracted-file hashes before atomically replacing the index. Rebuilding needs both originals and revision/extraction metadata; backing up SQLite alone is insufficient.

## Reviews and limitations

After checking representative pages/headings against the original, record exactly what was checked:

```powershell
.\.venv\Scripts\python.exe -m services.v2.knowledge.cli check-extraction SOURCE_ID SHA256_REVISION --note "Sampled physical pages/sections and findings here"
```

This records the operator account, time, and note. `extraction_checked` means a recorded extraction check, not a comprehensive review of every page, table, or diagram. It never sets `applicability_reviewed`. Project applicability review has no approval command in this milestone. Each new content revision starts unreviewed. Publication status is curated separately; an older downloaded revision is not automatically legally superseded.

PDF citations use physical file page numbers, which can differ from printed page labels. Extracted text does not preserve reliable table geometry, diagrams, emphasis, or binding/guidance distinctions; users must open the original. HTML sections include their native anchor when one exists, otherwise the source URL and heading. Search passages are limited to 350 words each. No content is sent to a model.

## API

Start the local service using `services/v2/README.md`.

- `GET /v2/sources?agency=VDOT&review_status=unreviewed&limit=20&offset=0`
- `GET /v2/sources/vdot-field-guide-2026`
- `GET /v2/references/search?q=flagger&agency=VDOT&limit=20&offset=0`

Agency values: `VDOT`, `FHWA`, `OSHA`, `VOSH`. Review values: `unreviewed`, `extraction_checked`, `applicability_reviewed`. Search also accepts `source_id`. Queries allow 1–500 characters and must contain words/numbers. Terms use literal AND matching, not caller-supplied query syntax. Pages allow 1–50 results and a nonnegative offset. Empty matches return `status=empty`; unknown source IDs return 404, invalid inputs 422, missing/broken index 503. Catalog browsing works before downloading documents.

Results include text, revision hash, agency, title, edition, retrieval date, physical page or heading, official link, review flags, warnings, and current publication status. `is_latest` means the most recently downloaded content for that source, not confirmed legal applicability. Historical revisions remain searchable and labeled. Source details expose the last download attempt even when older content remains searchable.

No public write/ingestion endpoints, new UI, email delivery, cloud deployment, or changes to the live V1 site are included.
