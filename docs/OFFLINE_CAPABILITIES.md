# Integrated offline behavior — October 12, 2026

Time Tracker regular controls can record device-estimate shift/task/break events
when an already loaded, authenticated app loses connectivity. Cross-tab-safe drafts
persist where browser storage and Web Locks work; otherwise they remain in the tab
with warnings and download. Submit after reconnecting for admin review. Submission
returns the timer to confirmed server state and does not apply attendance; pending
review is separate. Scoped device evidence is hidden from other accounts.

A full offline app launch is not supported: there is no cached authenticated shell.
GPS fixes require permission and availability; missing fixes keep explicit reasons.
Location uploads retry idempotently after reconnecting; closed/suspended browser
tracking is not guaranteed. Navigation keeps permitted loaded destinations and
explicitly downloaded address sheets; no offline Google map tiles, traffic or routes.
Messaging, meetings, provider delivery and Atlas inference need connectivity.
Read TIME_TRACKER_INTEGRATION_20261012.md; deployment/phone gates remain open.

## Earlier standalone implementation evidence

# Initial offline support

## October 11 Time Tracker increment (local candidate)

This supersedes the older Time Clock limitations below. Normal punches, breaks
and task changes maintain a device-time timeline while disconnected after one
verified load. Total work time excludes breaks; current-task duration updates.
The scoped snapshot, pending command UUID, drafts and location outbox persist in
localStorage. Reload recovers them once the authenticated app can load. Explicit
sign-out or organization changes clear device records. Storage errors stay visible
and enable download/unload protection. No private service-worker cache is added;
starting/reloading the complete app without a network remains unsupported.

Reconnection verifies server status without overwriting unresolved device records.
Members submit attendance evidence for existing audited admin reconciliation;
server attendance is never silently replayed at receipt time. Until reconciliation,
the regular buttons continue recording device evidence. GPS resumes automatically
on reconnect and is requested at punches/task changes and five-minute intervals
while clocked in. Missing fixes retain explicit reasons rather than later coordinates.
Location uploads use idempotent, authenticated, organization-scoped APIs. Closed or
suspended browsers cannot guarantee background GPS. Real-phone and PostgreSQL
acceptance remain open. See TIME_TRACKER_CONTRACT.md and TIME_TRACKER_COMPLETION.md.

## Historical implementation

Implemented locally September 29. Not cloud-deployed or full offline/PWA acceptance.

- Navigation uses already-authorized loaded destinations during connection loss. A user can save an address-only destination sheet for later use. No map tiles, imagery, live traffic or turn-by-turn routes are cached.
- Time clock retains its last confirmed active shift and labels the disconnected view. The running timer is an estimate. Confirmed clock commands and retry are blocked while the browser reports offline; reconnection refreshes the server state without replaying attendance changes.
- October 3 (branch claude/time-clock): the free-text notes have been replaced by structured **offline attendance drafts**. The open tab holds up to 50, and each draft carries an action, a task, a note, the device capture time, an optional stated time, and the last known shift ID and version. Drafts must follow a valid sequence: a second clock-out, or a clock-in while already clocked in, is refused. On reconnect, the member submits them to `/api/time/offline-submissions`. The server stores its receipt time and the device clock offset and marks each submission `pending`. Nothing changes attendance until an admin applies it through an audited correction or manual entry, or rejects it or marks it a duplicate. Retries are idempotent by `request_id`. See TIME_CLOCK_COMPLETION.md.
- October 9 (branch claude/offline-drafts): drafts now persist in browser storage under one key per organization and account, survive closing and reopening the app, and show explicit states (saved on device, submission unconfirmed, too old to submit). If storage is unavailable they fall back to the open tab with a warning. Opening the app with no connection is still not supported. See OFFLINE_DRAFTS_COMPLETION.md.
- Clock state/notes use organization plus actor scope and clear on scope change. Tokens are not persisted. Notes require download before closing/signing out; a before-unload warning is present. Keep downloaded employee/job files private on shared devices.

This is open-session offline support. Reloading/starting the app offline is not supported: no service worker or private authenticated shell cache has been introduced. Google Maps may use its own separately configured offline capabilities; WZOS does not guarantee that behavior.

Validation: two Node behavior tests verify stale-clock preservation, offline write blocking, online refresh, separate notes and organization-change clearing. Both modified JavaScript files pass syntax checks. Twelve Atlas API/guidance tests pass after capability-copy updates. Real desktop/mobile offline browser acceptance remains pending.

Done on claude/time-clock (see TIME_CLOCK_COMPLETION.md): user-reviewed offline attendance draft synchronization with captured and received timestamps, original shift/version, idempotency, conflicts and admin review. Do not replay ordinary time commands: current backend timestamps them at server receipt. Design authenticated offline reopening and storage/retention separately. Validate real navigation offline behavior and provider imagery permissions before any map-cache work.
