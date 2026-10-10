# Offline attendance drafts that survive reopening, plus saved destinations

October 9, 2026. Claude increment for review. Client-only; local synthetic preview only.

- **Branch:** `claude/offline-drafts`, cut from `enterprise-v2` at `2dc5935`
- **Commit:** the branch head; this document and the code land in one commit.
- **PR:** `claude/offline-drafts` into `enterprise-v2` (link added when opened)

## What it does now

The October 3 Time Clock drafts are kept, with the same server API, review rules and
idempotent `request_id` retries. They now persist on the device:

- **Storage.** Drafts are stored in `localStorage` under
  `wzos.clockDrafts.v1:<organization_id>:<user_id>`. They are written on every keep,
  remove, submit and discard, and are loaded when that account and organization become
  active.
- **Separation.**
  - Another account, or the same person in another organization, never loads them.
  - A payload whose stored scope doesn't match its key is ignored.
  - Malformed entries and invalid JSON are ignored.
  - Signing out leaves the saved drafts in place for that account only.
- **Explicit states, shown on every draft:**
  - Saved on this device — not yet submitted.
  - In this tab only — not yet submitted (storage blocked or private browsing). A
    warning before closing still applies in this case.
  - Submission not confirmed — submit again; it won't create duplicates. This state
    persists, so after reopening the app the same request IDs are retried.
  - Too old to submit (over 14 days). These drafts are kept for download and an admin
    manual entry, are excluded from submission (the server rejects them), and are never
    silently deleted.
- **Submitted drafts.** After a confirmed submission the device copy is removed, and the
  server list shows "Awaiting admin review", "applied", "rejected" or "duplicate".
  Reconciliation stays the audited admin review from the time-clock increment. Device
  times are never replayed as server-verified punches, and nothing changes the shift.
- **Discard all drafts** requires a confirmation. It clears the device copy and sends
  nothing.
- **Other tabs:** another open tab for the same account refreshes its list through the
  `storage` event.
- **Closing the app:** the before-closing warning now appears only when drafts would
  actually be lost (tab-only storage, or a submission in progress).
- **Navigation:**
  - New "Save all destinations (n)" button saves one plain-text sheet listing every
    loaded job: title, address, locality, work date and a Google Maps search link.
  - The per-job sheet uses the same format, and job cards show the work date.
  - The sheets are labeled as address references only: no map, route, traffic or
    safe-access verification.

**Not implemented, and not claimed:**
- Opening WZOS with no connection. There's no service worker or cached authenticated
  shell, so reopening needs a connection or page load. Drafts then appear immediately.
- Offline map tiles, imagery or turn-by-turn directions.
- Encryption of the device copy.

## API and schema changes

None. There's no server, route, model or DDL change. Local-only fields (`submission`)
are stripped before posting to the existing `extra=forbid` endpoint.

## Changed files

- `services/workspace_preview/static/timeclock.js`: persistence, states, discard,
  cross-tab sync
- `services/workspace_preview/static/team-modules.js`: navigation sheets (navigation
  block only)
- `tests/offline-clock.test.cjs`: harness accepts storage/confirm/session; 7 new tests
- `docs/OFFLINE_CAPABILITIES.md`: one dated paragraph (shared doc, narrow edit), and
  this document

`team-modules.js` is also changed on `claude/messaging`, but in different hunks
(messages view and title map). The two branches should merge without conflict;
recheck after the first one merges.

## Validation (actual results)

- **Node offline-clock tests: 12/12.** That's the 5 existing tests unchanged, which
  exercise the tab-only fallback, plus 7 new ones:
  - reopen and submit with local fields stripped;
  - organization/account separation and malformed-data rejection;
  - unconfirmed state kept across reopen with the same IDs retried;
  - 14-day drafts excluded from submission but kept;
  - blocked storage falls back to the tab and warns before closing;
  - discard requires confirmation;
  - cross-tab refresh.
- **Full Node suite:** 28/28 pass. `node --check` passes on both scripts.
- **Full Python suite: 337 tests OK, 67 skipped** (existing PostgreSQL cases with no
  test database). No Python files changed.
- **Browser (local synthetic preview on loopback port 8081, in-app browser):**
  - Member clocked in, then a simulated offline period (`navigator.onLine` overridden,
    `offline` event) with two break drafts kept. Both were labeled "Saved on this
    device".
  - After a full reload back online, the same device showed **0** drafts to the
    Enterprise admin and to the Core member, and **both** drafts to the original
    member. The shift was still "CLOCKED IN".
  - Submitting removed the device copy; the drafts showed "Awaiting admin review". The
    Enterprise admin API listed both as `pending`; the Core admin saw none.
  - Navigation showed "Save all destinations (1)".
  - Mobile screenshot (375×812):
    `C:\Users\MolecularDev\claude-WZOS-2.0\evidence\offline-drafts\member-mobile-drafts-after-reopen.jpg`
    (outside Git).
  - Real airplane-mode testing on a phone was **not** done.
- **Side effect to note:** a Codex/Ray synthetic browser fixture was already running on
  port 8083 (`scripts/browser_session_fixture.py`). Before I noticed, a few of my
  browser actions reached it: selecting an identity, opening Time clock and clicking
  Clock in. It also removed `wzos.clockDrafts.*` keys, which didn't exist there. The
  page still showed "Loading clock", so the click was most likely refused while status
  was loading. Please check that fixture's test data if it matters. I didn't stop or
  modify that process.

## Remaining gaps and dependencies

- **Opening the app offline** needs a service worker and cached app shell, plus a
  remembered last session scope so drafts can be shown before sign-in verification.
  That touches `app.py` routes, CSP (`worker-src`) and session handling, which Codex
  owns. Proposal: Codex adds a versioned `/sw.js` caching only static assets and
  `index.html`; Claude then adds an offline Time clock / Navigation mode that reads
  only that account's saved data.
- **Shared-device policy:** drafts persist for the account until submitted or
  discarded, and the device copy is not encrypted.
- **Real-device and browser acceptance:** Android/iOS airplane mode, browser restart,
  private browsing and storage eviction.

## Product questions for Ray (current behavior in brackets)

1. On sign-out from a shared device, should unsubmitted drafts be kept for that
   account, or must they be submitted, downloaded or discarded first? [Kept for that
   account, never shown to others.]
2. Should drafts older than 14 days be deleted automatically after some period? [Kept
   until the member discards them.]
3. Is a service-worker offline app shell in scope for the pilot? [Not implemented.]

## Integration and rollback

Merge as a normal front-end change. Nothing is deployed or migrated. Rollback means
reverting the commit. Saved device drafts then remain inert in browser storage:
older code ignores them and they can't be submitted until this code returns.
