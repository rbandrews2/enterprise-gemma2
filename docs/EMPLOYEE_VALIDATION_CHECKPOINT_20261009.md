# Employee integration validation checkpoint — October 9, 2026

Candidate branch: `codex/integration-release`, based on committed checkpoint
`65843c4`. This increment has not been merged into `enterprise-v2` or deployed.

## Latest regression attempt

Added `scripts/run_local_gate.py` to report each test's start/end and elapsed
time, and terminate a test exceeding a configured timeout with a stack trace.
This diagnostic runner does not replace PostgreSQL validation.

The full local run terminated at its 120-second test timeout while
`tests.test_knowledge.StoreTests.test_reverted_remote_content_becomes_latest_download`
was in `Store.rebuild()` / `Store.revisions()` / `Path.glob()`.
The preserved log is `.local-data/employee-timed-gate.log` (gitignored).
This is an incomplete regression gate, not a passing result. The trace alone
does not establish a source-backend defect: browser control and simple local
file reads were also timing out or delayed during this run.

The isolated rerun passed: one test in 24.477 seconds. No source-backend change
was justified by this result. A full rerun with a 300-second diagnostic timeout
was then started; collect its result from `.local-data/employee-timed-retry.log`.

## Resume sequence

1. Restore responsive host/browser control and collect the full rerun.
2. Investigate a reproducible failure, or rerun the full local gate after the
   host is responsive. Preserve skips separately from actual passes.
3. Complete the synthetic member browser checks: own profile visible;
   another employee inaccessible; member cannot edit administrative records.
4. Run disposable PostgreSQL checks for the employee startup DDL and writes.
5. Record exact results, review the diagnostic runner, commit and push the
   candidate; merge only after the contract's integration gates pass.
6. Next feature increment: render the saved Work Zone Report snapshot as a
   draft PDF, preserving revision/citation/review information and reusing
   compatible V1 ReportLab code. No new compliance claims or paid model calls.

Existing employee API/UI and availability implementation remains unchanged.
V1, public DNS, production, and contributor worktrees were not modified.
