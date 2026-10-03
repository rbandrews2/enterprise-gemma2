# Time Clock completion — Claude worktree handoff

Branch `claude/time-clock`, based on `enterprise-v2` at `fac7af9`. Worktree is separate from Codex's checkout. Ownership is Time Clock only.

Note: the assignment asked for `AGENTS.md`, but there isn't one in this repository. The only copies are inside vendored `node_modules`. I used `docs/SESSION_HANDOFF.md`, `docs/REMAINING_TASKS.md` (task 9), `docs/TIME_CLOCK_INTEGRATION.md` and `docs/OFFLINE_CAPABILITIES.md`.

## Plan (written before implementation)

### Existing behavior that stays as it is
- `services/workspace_preview/timeclock.py` records shifts as JSON snapshots in `preview_shifts`. It keeps one active shift per employee through a partial unique index and stores command receipts in `preview_clock_events`, keyed by `(organization, employee, request_id)` so retries are idempotent.
- Timestamps come from the **server at receipt**. That is why queued offline punches must never be replayed as ordinary commands.
- Members read their own shifts. Admins read team shifts within their organization. Export is CSV and stops at 50 shifts.
- Offline mode keeps the last known shift in the open tab, blocks writes, and offers downloadable free-text notes. It does not synchronize anything.

### Gaps to close
1. **Admin corrections with an audit trail.** Admins can edit times, breaks, task intervals and the work-order link for a shift in their organization, with a required reason. Admins can also enter a missing shift. Each change writes an immutable audit row with the before and after snapshots, the admin, the time and the reason. Corrections are idempotent per `request_id` and checked against the shift version. Validation covers chronology, containment, overlaps, no future times and no overlap with the employee's other shifts. An admin can correct an active shift only by closing it.
2. **Record basis.** Every shift reports `server_recorded`, `admin_corrected` or `admin_entered`. Exports carry this basis, so estimated or offline-derived times are never presented as server-verified.
3. **Safe offline reconciliation.** Offline actions become structured *attendance drafts* in the open tab. Each draft carries the device time it was captured, an optional user-stated time and the last shift ID and version the device knew about. When the connection returns, the member reviews the drafts and submits them as **offline submissions**. The server stores the receipt time and the device clock offset, and marks each submission `pending`. Submissions never change shifts on their own. An admin rejects a submission, marks it a duplicate, or applies it through a correction or manual entry that references it in the same transaction. Duplicate prevention happens at four levels:
   - `request_id` idempotency for each submission.
   - A client-side state machine that refuses impossible sequences, such as two clock-outs in a row.
   - A server-side hint that flags possible duplicates of verified receipts within ±15 minutes.
   - A server check that a submission can be resolved only once.
4. **Online, offline and reconnect states.** A dedicated connection badge shows these states: online and verified, offline with the last known status, reconnecting, and reconnected and verified.
5. **Exports.** Admins can filter by employee. Exports include employee names, record basis and correction count, and an optional per-interval format. The limit rises from 50 to 1,000 shifts, with a clear 422 response when exceeded.
6. **Member access.** Members can read the detail and audit history of their own shifts and the status of their own submissions. Another employee's records return 404, and team or admin endpoints return 403.

### Shared-file, API and schema impact (kept narrow)
- `services/workspace_preview/app.py`: one line. `timeclock.register(...)` now also receives `roster`, which is used for employee names and for checking that a target employee belongs to the organization. The parameter is optional and keeps backward compatibility.
- `services/workspace_preview/static/index.html`: adds one `<script>` tag for `/timeclock-review.js` and one `<link>` for `/timeclock.css`. New markup is created by the Time Clock scripts. The static routes are registered inside `timeclock.register`, so `app.py` routing is unchanged.
- New tables are created by `timeclock.initialize`, following the existing `CREATE TABLE IF NOT EXISTS` convention: `time_corrections` and `time_offline_submissions`. Existing tables and columns are unchanged, and existing shift payloads gain only optional keys. The reviewable PostgreSQL DDL is in `docs/migrations/20261003_time_clock_corrections.sql`. **Important:** the app creates these tables at startup, so deploying the code applies the DDL to whichever database it connects to. I have not applied anything to a shared database.
- New API endpoints, all under `/api/time/`, all requiring an authenticated actor and all scoped to the organization:
  - `GET members`
  - `GET entries/{id}` returns the detail and audit history.
  - `POST entries` is the admin manual entry.
  - `POST entries/{id}/corrections` (admin)
  - `POST offline-submissions` (own)
  - `GET offline-submissions` (own; `team=true` requires admin)
  - `POST offline-submissions/{id}/resolve` (admin; reject or mark duplicate)
  - Existing `entries` and `export` gain the optional parameters `employee_id` and `detail`.

## Results (October 3, 2026)

### Completed
- **Persistent records.** The existing server-receipt clock-in, clock-out, break and task-switch commands are unchanged. Shifts now report a `record_basis` of `server_recorded`, `admin_corrected` or `admin_entered`, plus `correction_count`.
- **Admin corrections with audit trail.** Use `POST /api/time/entries/{id}/corrections`.
  - Full-shift times are validated: chronology, a 48-hour maximum, no future times, breaks and task intervals inside the shift, no overlaps, task intervals never overlapping breaks, and no overlap with the employee's other shifts, including an active one.
  - A reason is required. The update is version-checked and idempotent: the same `request_id` returns the original response, and a changed body returns 409.
  - Correcting an active shift closes it, and the member's next stale command receives 409.
  - Each change writes an append-only `time_corrections` row containing the full before and after snapshots.
- **Manual entry.** Use `POST /api/time/entries`, admin only. The employee must belong to the organization. The new shift is audited with `before = null` and labelled `admin_entered`.
- **Audit history.** `GET /api/time/entries/{id}` returns the entry, server receipts, admin changes and linked offline submissions. Members can read their own entries, admins can read any entry in their organization, and anything else returns 404.
- **Offline reconciliation.** Device drafts become `pending` offline submissions that store the captured, stated, device-submitted and server-received times, the device clock offset and an estimated time. Submissions never alter shifts.
  - Duplicate hints flag server receipts with the same action within ±15 minutes, as well as admin-entered or corrected boundaries.
  - An admin either applies a submission inside a correction or manual-entry transaction, which links it and sets `applied`, or resolves it as `rejected` or `duplicate` with a reason.
  - A submission can be resolved only once (409 otherwise).
  - Drafts older than 14 days are refused with a message to use a manual entry.
- **Connection states.** A visible badge shows checking, online and verified (with the time), offline showing the last known status with the timer marked as an estimate, reconnecting and checking, and server error.
- **Exports.** Exports carry employee names, record basis and correction count. A per-interval format and an admin `employee_id` filter are available. The limit is now 1,000 shifts (422 above that), and the filename includes the date range. CSV formula injection is still neutralized.
- **UI.** Added an admin review queue, a correction and manual-entry editor, per-entry audit history, record-basis badges and an employee filter. The design is gloss-black with amber accents, wraps to one column at phone width, and is fully keyboard operable: the editor focuses its first field, Escape closes it, and focus returns to the button that opened it. Reduced motion stops the connection pulse.
- **Atlas guidance.** The Time Clock guide text in `intelligence.py` and `assistant.js` now describes corrections and offline drafts. This is a text-only change in Atlas-owned files; see the integration notes below.

### Tests and actual results
- Full Python suite: **217 tests, 201 passed, 16 skipped**. The skips are the existing PostgreSQL cases with no `WZOS_TEST_DATABASE_URL` set. The baseline before this work was 206 tests, 190 passed and 16 skipped.
- New `tests/test_timeclock_corrections.py` (11 tests) covers:
  - audit visibility to the member
  - replay and conflict handling, and stale versions
  - 11 validation cases
  - member 403 and 404 responses, and cross-organization 404s for reads, corrections, manual entries, offline queues and resolution
  - closing an active shift and overlap protection
  - concurrent corrections (exactly one 200 and one 409)
  - offline submissions: no attendance change, device offset, idempotency, conflict, future, stale, naive-time and other-organization work-order cases
  - application, resolve-once and duplicate hints
  - exports: basis, filters, intervals, the 1,000-shift limit and formula safety
  - persistence across an application restart
- Node suite: **15 of 15 passed**. `tests/offline-clock.test.cjs` was rewritten as 5 tests covering connection states, blocked commands while offline, the draft sequence check, submission on reconnect with no clock commands posted, retries reusing the same request IDs after an unconfirmed submission, and clearing on scope change. `node --check` passes on all static JS.
- **Real browser:** Microsoft Edge (headless, via Playwright) against an isolated loopback preview on a fresh scratch SQLite database with synthetic identities. The full flow passed:
  - Online clock-in, task switch and break.
  - Offline: clock-out disabled, an impossible draft refused, a duplicate draft refused, and 0 POST requests.
  - Reconnect message, then submission, and the member was still clocked in.
  - Admin queue with a duplicate hint.
  - Editor focus, Escape and focus return.
  - Correction applied with the submission linked.
  - Manual entry.
  - Audit history.
  - CSV export with basis and names.
  - Member sees "Applied by admin".
  - At 390 px with reduced motion: no horizontal overflow and no animation.
- The browser run found one defect, now fixed and re-verified: saving an editor field the admin hadn't touched truncated sub-second server times. Untouched fields now keep their exact original value; the before and after audit snapshots are identical.
- The only console error is the existing `/favicon.ico` 404.
- Screenshots: `docs/screenshots/time-clock/` (offline drafts, admin review queue, audit history, mobile admin).

### Not verified / remaining gaps
- **PostgreSQL:** there is no local PostgreSQL or Docker. The SQL uses the existing portable contract: qmark placeholders, the `json_extract` compatibility function, and `BEGIN IMMEDIATE` mapped to an advisory lock. It has not been executed against PostgreSQL. Codex should run `scripts/test_postgres_accounts.sh`, or a variant that includes `test_timeclock_corrections.py`, in Cloud Shell.
- **Verified accounts:** the new tests use the synthetic preview identities. The account-workspace roster path, `Accounts.roster`, is exercised only through the existing shared `roster(selected)` contract.
- **Persistence of drafts across reloads:** drafts still live only in the open tab, and offline reopening is unsupported (no service worker). See the product questions below.
- **Not in scope / not started:** GPS and location consent, payroll, overtime and rate rules, a member "withdraw submission" action, site and task administration parity, and real-device offline tests on mobile hardware.

## Open product decisions (questions for Ray)
1. **Self-correction.** Can an admin correct or enter their own shifts? It's currently allowed and audited (the admin ID is recorded). A two-person rule would block single-admin organizations.
2. **Draft persistence.** Should offline drafts survive a reload or tab crash, using `sessionStorage` or IndexedDB scoped to organization and actor and cleared on sign-out? That trades privacy on shared devices against data loss.
3. **Windows.** Offline submissions older than 14 days are refused, shifts are capped at 48 hours, and the duplicate-hint window is ±15 minutes. Are these the right values?
4. **Correcting active shifts.** A correction currently always closes the shift. Should admins also be able to adjust the start of a shift that is still running?
5. **Retention.** How long should audit rows, rejected submissions and exports be kept, and should members be able to export their own audit history?
6. **Payroll boundary.** Exports are labelled "Payroll calculated: No". Confirm that payroll integration stays out of WZOS.

## Changed files
- `services/workspace_preview/timeclock.py` (module: corrections, manual entry, audit detail, offline submissions, exports, new tables)
- `services/workspace_preview/static/timeclock.js` (connection badge, offline drafts, submission status, employee filter, export detail, basis badges)
- `services/workspace_preview/static/timeclock-review.js` (new: audit history, correction and manual-entry editor, review queue)
- `services/workspace_preview/static/timeclock.css` (new)
- `tests/test_timeclock_corrections.py` (new), `tests/offline-clock.test.cjs` (rewritten for drafts)
- `docs/migrations/20261003_time_clock_corrections.sql` (new, not applied), `docs/screenshots/time-clock/*.png`
- `docs/TIME_CLOCK_COMPLETION.md` (this file), `docs/OFFLINE_CAPABILITIES.md` (time-clock bullet)
- **Shared (narrow):**
  - `services/workspace_preview/app.py`: one line passing `roster`.
  - `services/workspace_preview/static/index.html`: one stylesheet link, one script tag and one sentence of help text.
  - `services/workspace_preview/intelligence.py` and `services/workspace_preview/static/assistant.js`: Time Clock guide sentences only.

## Integration instructions (for Codex)
1. Review the PR into `enterprise-v2`. Expect conflicts only if `app.py` line `timeclock.register(...)`, the `index.html` `<head>`, or the two guide strings changed in the meantime.
2. Run the full Python and Node suites. Run the PostgreSQL suite with `test_timeclock_corrections.py` added, against a disposable schema.
3. **Before deploying to shared staging:** the two new tables are created at startup. Review `docs/migrations/20261003_time_clock_corrections.sql`; the change is additive only. Verify on staging with synthetic accounts that admin and member roles and organization isolation hold for the new endpoints.
4. `SESSION_HANDOFF.md` and `REMAINING_TASKS.md` were intentionally not edited, to avoid conflicts. Mark task 9 according to the open gaps above when integrating.

## Rollback
- **Code:** revert the merge commit. The old client ignores the new tables, and older shift payloads remain valid. New optional payload keys are ignored by the old `present()`, although corrected or admin-entered shifts would then display without their basis label.
- **Data:** keep the new tables for audit retention. Drop them only with the commented statements in the migration file, and only if no audit record needs to be retained.
