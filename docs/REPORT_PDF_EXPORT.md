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

- Full candidate regression passed359tests in663.867seconds:281passed,
  78PostgreSQLskips, zero failures/errors. Log `.local-data/report-full-python.log`.
- Real loopback HTTP acceptance passed after restarting the stale disposable
  fixture: member creates/saves a synthetic job report; PDF download succeeds,
  snapshot hash and extracted content match, and unauthenticated access returns401.
  The exported synthetic report had3pages. Helper `.local-data/report_http_check.py`
  and generated records are disposable local evidence, not customer data.

PDF PostgreSQL and browser download/mobile acceptance must be recorded before
merging/deploying. The local suite must use
`python scripts/run_local_gate.py --test-timeout 300`; tests is intentionally a
non-package directory, so unittest discovery with `-t .` is invalid here.

The October10 member dialog was also checked at a narrow preview size; the
browser reported innerWidth534/documentWidth520 despite a requested390px
override. No horizontal document overflow was observed, and Close returned to
the workspace. This is not a confirmed390px or real-phone acceptance. Ignored
synthetic screenshot: `.local-data/member-record-narrow.jpg`.

## Resume the cloud candidate gate

Browser control timed out again after the353-test baseline completed, including
after Ray reconnected. When Cloud Shell control works, use only the dedicated
checkout below, require a clean tree, and fast-forward to the pushed candidate.
These commands run disposable tests, not deployment:

```bash
cd ~/wzos-preproduction-20261010
test -z "$(git status --porcelain)" &&
  git fetch origin codex/integration-release &&
  git merge --ff-only FETCH_HEAD &&
  git rev-parse HEAD &&
  PATH=/usr/lib/postgresql/16/bin:$PATH bash scripts/test_postgres_native.sh > ~/wzos-report-pg-20261010.log 2>&1
tail -12 ~/wzos-report-pg-20261010.log
find /tmp -maxdepth 1 -type d -name 'wzos-pg-gate.*' -user "$(id -un)" -print
```

Record the exact tested SHA and gate summary; do not infer success from the
tail command's exit code. Empty find output confirms no remaining harness
directory owned by this operator; investigate any remaining directory without
deleting unrelated work.

Rollback: revert the PDF endpoint, renderer, report UI button and dependency pins.
Existing snapshots remain usable; no database rollback is required.
