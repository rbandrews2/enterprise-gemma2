# Claude module review — October 10, 2026

## Decision

Hold integration pending the five reproduced repairs below. This was a read-only
review of Claude's four checkouts under `C:/Users/MolecularDev/claude-WZOS-2.0`.
Their tracked files were not modified. No module was merged or deployed and no
real text, cloud provisioning or production change occurred.

Reviewed heads: Messaging `99125c9`, Dispatch `69d4316`, Training `2426620`,
Offline drafts `f09fca5`. Dispatch is stacked on Codex employee integration and
Messaging; the other three are based on `2dc5935`. Do not merge that stack blindly
or duplicate its inherited commits.

## Reproduced findings and repair acceptance

### 1. P1 — Verification codes are exposed through the admin outbox

`messaging/services/workspace_preview/messaging.py:272-279,432-442` returns raw
verification-message bodies to admins. Codes remain present for blocked messages
and retryable sends. With SMS disabled, enrollment created a blocked verification
message; the admin outbox exposed its code; submitting that code verified the
contact (HTTP 200) despite zero provider sends.

Never expose verification codes through the public/admin DTO, UI or audit output.
Keep the worker's necessary secret payload separate and expiring. Test blocked,
queued, retryable and failed verification rows, and ensure admin access cannot
substitute for possession of the recipient phone. Do not print codes in evidence.

### 2. P1 — Concurrent tabs can delete an unsubmitted attendance draft

`offline-drafts/services/workspace_preview/static/timeclock.js:121,178` ignores
storage events while submitting, then writes its stale draft list. Reproduction:
tab A submits draft 1 with the response delayed; tab B adds draft 2 to shared
storage; A ignores the storage event; after A's successful response, its save
removes the storage key, including B's unsent draft 2. The review regression
asserting retention of draft 2 fails; the existing 12 offline tests pass.

Use transactional/serialized per-draft persistence or a safe merge/removal
mechanism that deletes only acknowledged IDs. Cover concurrent additions,
successful and uncertain submissions, removals and account changes. Do not
restore a discarded/submitted draft through a stale tab write.

### 3. P2 — Assessment retries ignore the requested module version

`training/services/workspace_preview/training_content.py:265` checks request ID,
organization, actor, module ID and answers, but not `module_version`. A request ID
used for version 1 and reused with version 2 plus the same answers returns HTTP
200 and the old attempt rather than a conflict. The requested version was not
assessed. Include the version in the retry identity; exact retries still return
the first result, changed versions must return 409 without additional writes.

### 4. P2 — Cancelling a training assignment prevents reassignment

`training/services/workspace_preview/training_content.py:221-224` returns an
existing assignment regardless of its status. Assign, cancel, then assign the
same member/module version again returns HTTP 200 with `status: cancelled`.
There is no restore operation; the admin cannot give that version a new active
assignment. Add an explicit audited restore/reassignment workflow while retaining
idempotent retries and completed records. Test cancellation/reassignment and
changed due dates, with a clear UI action and accurate status.

### 5. P2 — Cancellation notices describe current requirements, not the assignment

`dispatch/services/workspace_preview/dispatch.py:375,411` uses `when(req)` for
cancellation messages. Approve a job, change its requirements to the next day,
then cancel the original plan: HTTP 200; the notice names the new day, not the
day of the assignment being cancelled. Replacement notices have the same pattern.
Use immutable assignment/approved-plan times for cancellation notices, including
both dates for overnight/multi-day work. Preserve the new times only in new
assignment notices. Test both cancellation and replacement after date changes.

## Independently run checks

| Branch/check | Passed | Skipped | Outcome |
|---|---:|---:|---|
| Messaging focused Python | 19 | 16 PostgreSQL | Existing tests pass |
| Dispatch focused Python | 11 | 11 PostgreSQL | Existing tests pass |
| Training focused Python | 6 | 6 PostgreSQL | Existing tests pass |
| Offline full Node | 28 | 0 | Existing tests pass |
| Additional offline race reproduction | 0 | 0 | One failing retention assertion |

Additional isolated Python probes reproduced findings 1, 3, 4 and 5. They used
temporary synthetic fixtures and fake SMS providers, no live credentials or
customer data. Probe scripts are ignored under the Codex integration worktree's
`.local-data/review_claude_probe.py` and `.local-data/review_offline_probe.cjs`.

The existing tests cover important tenant, admin/member and Enterprise-dispatch
restrictions. Their success does not cover these newly identified cases. No
PostgreSQL, real Twilio, hosted-browser or combined candidate acceptance was
performed in this review. Training's handoff also discloses an earlier full-suite
socket-test error; rerun the full integrated candidate after repairs.

## Integration sequence after repairs

1. Claude repairs module-owned files on the corresponding branches and adds the
   regressions above; Codex reviews again. Ray can relay this document.
2. Bring the Codex employee candidate and module branches into an isolated combined
   candidate, accounting for Dispatch's inherited Messaging/Codex history.
3. Run full Python/Node, disposable PostgreSQL for all startup DDL, synthetic
   multi-user browser acceptance and employee/training/dispatch integration.
4. Resolve provider/background-worker and restricted webhook reachability before
   controlled SMS acceptance; keep SMS disabled until then. MMS, service-worker
   offline launch, private training media and Atlas dispatch explanation remain
   documented gaps, not completed capabilities.
5. Review the provisional product choices from each handoff with Ray separately
   before treating them as production policy. No approval is needed to repair
   the reproduced defects on the isolated module branches.

## Recovered Codex checkpoint

Yesterday's full employee rerun completed: 353 tests in 633.697 seconds; 278
passed, 75 PostgreSQL-dependent skips, zero failures/errors. Log:
`.local-data/employee-timed-retry.log`. Commit `abae32e` is confirmed on remote
`codex/integration-release`. Member-browser and new employee PostgreSQL gates
remain open; `enterprise-v2` is unchanged.
