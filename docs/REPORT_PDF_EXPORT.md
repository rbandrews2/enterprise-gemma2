# Saved Work Zone Report PDF export

October 10, 2026. Integration candidate; no live deployment.

## Behavior and access

The report history offers **Download draft PDF** for a saved snapshot. The
authenticated GET `/api/orders/{order_id}/reports/{snapshot_id}/pdf` reuses the
existing report detail boundary: Enterprise entitlement, organization, visible
work order and snapshot author. Admin access does not override another author's
private snapshot. No public download URL is created.

The export includes saved work-order details, reported geometry, readiness
checklist, linked form draft fields, reference preparation, citation passages,
edition/revision/page/section, review/publication status and coverage gaps.
The snapshot hash and job revision identify its basis. Later job changes leave
the saved PDF bytes unchanged; the workspace and response header indicate changed
inputs. The PDF remains a draft requiring review, not approval for field use.

## Implementation and limits

Reuses ReportLab tooling already present in V1; V2 pins ReportLab 5.0.1 and
Pillow 12.3.0. Bundled fonts support the tested accented text. Rendering escapes
customer/source markup, performs no network/model calls, verifies the stored
payload hash, and rejects payloads over 2 MiB or layouts over 5,000 elements.
Responses use no-store and an attachment filename based on the snapshot UUID.
Only HTTPS source links become PDF links. No startup DDL or storage migration.

Imagery, sign/flagger placement diagrams, attachments/signatures, approval and
external email/SMS delivery are not included in this increment. Existing saved
limitations are preserved rather than silently rewritten.

## Evidence and remaining gates

- Employee baseline 8024631: disposable native PostgreSQL 16 Cloud Shell gate
  passed all 353 tests in 61.678 seconds, zero failures/errors/skips. That run
  precedes this PDF increment; new PDF PostgreSQL acceptance remains required.
- PDF focused tests: three SQLite cases passed; three PostgreSQL cases skipped
  locally pending the disposable database. Covers entitlement/author/org checks,
  immutable bytes, changed-job indicator, multipage citations and literal markup,
  official-link traceability, tampering and size rejection.
- Node suite: 21 passed; report.js syntax and diff checks passed.
- Two-page synthetic PDF rendered and both pages visually inspected: legible,
  no overlaps or clipping. Ignored proof: `.local-data/report-pdf-proof.pdf` and
  `.local-data/report-pdf-page-1.png`, `report-pdf-page-2.png` in this worktree.
- Synthetic member browser sign-in and organization selection passed. My employee
  record opened read-only without admin save/review controls.

Full regression, PDF PostgreSQL and browser download/mobile acceptance must be
recorded before merging/deploying. The local suite must use
`python scripts/run_local_gate.py --test-timeout 300`; tests is intentionally a
non-package directory, so unittest discovery with `-t .` is invalid here.

Rollback: revert the PDF endpoint, renderer, report UI button and dependency pins.
Existing snapshots remain usable; no database rollback is required.
