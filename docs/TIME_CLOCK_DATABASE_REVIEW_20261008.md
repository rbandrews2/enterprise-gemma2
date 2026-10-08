# Time Clock database coverage review — October 8, 2026

Reviewed isolated PR #1 revision `6410fbf`; Claude checkout unchanged.

## Verified findings

The focused local suite passed 17 tests. This is SQLite evidence only.
`tests/test_timeclock_corrections.py:35-41` creates a SQLite file and calls
`create_app` without injecting PostgreSQL storage. No PostgreSQL subclass exists
for these correction scenarios at this revision. The PostgreSQL account suite
inherits account tests, not Time Clock correction tests.

The export-limit scenario also opens SQLite directly (lines 269 and 277) and
uses SQLite `rowid` (line 278). Merely setting `WZOS_TEST_DATABASE_URL` does not
exercise corrections, offline reconciliation, or the new startup DDL on PostgreSQL.
This is a missing acceptance check, not evidence of a runtime defect.

## Required integration repair

1. Reuse the existing storage-injection interface in `create_app` and the disposable
   schema fixture pattern from account/Forms tests.
2. Route fixture SQL through the selected storage adapter; delete fixture rows by
   their explicit IDs rather than `rowid`.
3. Run the same correction, overlap, stale-version, concurrent-edit, tenant/role,
   offline-resolution, export, and restart scenarios against PostgreSQL.
4. Verify startup DDL creates both new tables/indexes and remains safe on restart.
5. Run the full integrated Python/Node suites and browser checks before merge.

The currently running Cloud Shell Forms candidate `f52996d` does not include
Time Clock PR #1. Its success must not be reported as Time Clock acceptance.
No schema, deployment, or Claude-owned code was changed by this review.
