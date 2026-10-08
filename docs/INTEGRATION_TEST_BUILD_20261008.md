# October 8 integration test build

## Current candidate

Codex repair worktree `.local-data/forms-retirement`, branch
`codex/forms-retirement`, contains Forms Hub PR #2 through `80bafed` and the
`enterprise-v2` checkpoint through `5ea77e0`. Claude's worktrees are unchanged.
The candidate is not merged or deployed. Time Clock PR #1 is not included yet.

## Reproducible local preview

From the candidate checkout, with account dependencies installed:

```powershell
python scripts/start_integration_preview.py --port 8083
```

Open `http://127.0.0.1:8083/`. Use **Test identity** to switch between Core and
Enterprise admin/member fixtures. Choose **Forms hub** to inspect printable forms
and the admin's team-form library. Data and uploads persist under the candidate's
ignored `.local-data/integration-preview` directory. Use synthetic data only.

This launcher binds only to loopback and rejects cloud runtimes. It explicitly
disables live model calls and Maps credentials and supplies local file storage.
Atlas here is local app guidance, not live Gemma inference. The source store is
empty in this isolated fixture; this is not an agency-reference acceptance test.

## Verified this pass

- Workspace page and its styles/scripts loaded through a real local HTTP server.
- Created a synthetic team form, uploaded a PDF fixture and attached it.
- Member download before publication: 404. After publication: byte-identical PDF.
- Other-organization download: 404. Member delete: 403.
- Focused runner/Forms Hub tests: 43 total, 23 passed, 20 PostgreSQL skipped.
- Browser navigation actions timed out before dispatch; interactive UI acceptance
  is still open. No screenshot acceptance is claimed.
- Chrome/Cloud Shell connection was not available at the last inventory check.
  No cloud state, IAM, database or GCS mutation was performed.

## Database gate

The old `scripts/test_postgres_accounts.sh` ran only account-storage tests. It now
runs the full suite through `scripts/run_postgres_gate.py`, including Forms Hub
and any integrated Time Clock tests. The runner rejects missing database settings,
empty runs, failed tests and skipped tests. Local SQLite results cannot satisfy it.

In authorized Cloud Shell from a clean candidate checkout, use:

```bash
bash scripts/test_postgres_accounts.sh
```

The script starts a uniquely named disposable PostgreSQL 16 container on loopback,
generates a temporary password, installs pinned account dependencies into a local
test virtual environment, runs tests and removes that test container on exit.
It requires Docker and package-network access; no paid database is provisioned.
Do not point the runner at a production database. If the container run cannot be
used, provide an authorized disposable test database using
`WZOS_TEST_DATABASE_URL` and run `python scripts/run_postgres_gate.py`; do not
print or commit the connection string.

## Next delivery sequence

1. Finish Forms Hub PostgreSQL, private-GCS and browser checks; integrate PR #2.
2. Review and validate Time Clock PR #1, including its startup DDL, tenant/role
   rules, offline reconciliation and corrections; integrate only after gates pass.
3. Repair Atlas private invocation using the prepared preflight, then run the
   bounded concurrency trial with fresh budget/state checks and cleanup guard.
4. Validate the combined restricted test build across work orders, forms, report,
   time, navigation, messaging, scheduling and training. Record missing functions
   against `REMAINING_TASKS.md`, with clear distinctions between UI and working
   backend functionality.
5. Continue the production checklist: account lifecycle, reviewed references and
   placement logic, PDF/delivery, Twilio, Enterprise dispatch, operations and pilot.

No new production date is claimed. Reuse passing evidence unless the candidate or
environment changes in a way that invalidates it. Keep V1/DNS/production unchanged.
