# Atlas source grounding and display checkpoint

## Implemented locally

- Saved-job safety questions now receive explicit library status, candidate count,
  unverified applicability and coverage gaps. API/UI expose the same source basis.
  An unavailable library cannot be mistaken for verified governing documentation.
- Conversation status distinguishes an enabled model awaiting startup from a
  deliberately disabled model. Status performs no private-model inference request.
- Replies render paragraphs, ordered/unordered lists and bold text with DOM text
  nodes. Generated HTML, images, links and scripts remain inert text.
- `scripts/package_source_library.py` copies only catalog revisions and metadata,
  checks originals/extractions by SHA-256, rebuilds SQLite and writes a per-file
  hash manifest. It refuses existing destinations and overlapping source paths.
  Failed snapshots lack the final snapshot manifest and must not be deployed.

## Preserved-source snapshot

Created ignored `.local-data/source-deployment-20260928/` from the surviving
library. It contains 26 hashed files plus snapshot.json, without unrelated local
files, QA leftovers or customer records. No downloads or freshness claims.

Six sources have extracted text: FHWA MUTCD, VDOT manual, field guide, known
errors, VOSH program and regulatory references. Five are extraction-checked;
VDOT known-errors remains unreviewed. OSHA factsheet is missing. None of this
establishes applicability to a job or locality. Review states are unchanged.

## Validation

- Full Python suite: 178 tests, 162 passed / 16 database skips.
- After adding the citation traceability case, all 11 focused intelligence tests
  passed. This last test was added after the full-suite run.
- Seven Node tests passed, including inert HTML and cold/disabled status.
- Source-package tests reject corrupted originals and exclude unrelated files.
- Real loopback HTTP snapshot preparation: available library, 13 candidate
  passages; stale job version 409 and Core advanced-preparation denial 403.
  Temporary port 8084 used the supported loopback Host header for this harness;
  its initial unapproved Host was correctly rejected. Server stopped afterward.
- Snapshot search for advance warning returned 339 matches with preserved
  source/revision/page/review metadata.

## Cloud boundary and next action

No deployment or GPU call in this pass. The account Dockerfile copies catalog
code, but not ignored downloaded documents or index. Therefore cloud source
grounding is not accepted yet. The snapshot is local-only and not GitHub-backed.

Next: transfer the snapshot with its hash manifest, build a staging-only image
containing it under `/app/.local-data/knowledge`, and verify hashes/search in that
image. Preserve originals and manifest for reproducibility. Recheck source
freshness/applicability separately; packaging must never mark sources approved.
Then run saved-job/citation model tests, true scale-from-zero, concurrency and
cloud cancellation checks under the remaining approved trial allocation.

Cloud remains at the previous checkpoint: app 00008-5dx, inference disabled,
trial GPU service removed. V1, production and DNS unchanged.
