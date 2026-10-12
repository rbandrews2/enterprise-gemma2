# Time Tracker integration — October 12, 2026

Release branch: codex/preproduction-modules. Original branch remains intact.
Preserves current modules, admin/member roles, organization and edition isolation.

## Resolved behavior

- Timeline uses the regular clock controls during connection loss after a verified
  shift load, with device-estimate labels and audited admin attendance review.
- Existing per-account draft store, Web Locks, retry IDs, old-record validation,
  download/discard safety and concurrent-tab tests remain. Account switching hides
  another account's evidence; scoped drafts stay available to their original account.
- Tracker baseline/uncertain command metadata is separate from attendance drafts.
  GPS outbox is separately scoped and locked; acknowledgements remove only accepted
  IDs, so concurrent evidence is retained. No locks/storage means tab-only evidence.
- Once attendance drafts are successfully submitted, the live timer returns to
  server-confirmed state; pending admin review remains visible separately. Submission
  does not apply attendance. Do not describe this as automatically approved time.
- GPS is requested at punches/task changes and five-minute intervals while a shift
  is open. Permission denial/offline/timeout stays explicit and never blocks time
  controls. Closed/suspended browser tracking is not guaranteed. No real location
  permission was accepted by the agent; only synthetic fixtures used in local tests.
- Black/gold Time Tracker palette and original eagle image/drift retained.

## Schema and rollback

Additive startup SQL: docs/migrations/20261011_time_tracker_locations.sql.
Creates time_location_events and scoped shift index; no attendance table changes.
Writes are self-only with complete-fix or unavailable-reason validation, UUID retry
idempotency, time-window limits and own-shift linking. Admin team reads remain inside
organization; members read only their own. Keep the evidence table on code rollback.

## Gates

Full Node62 passed before final location-memory warning adjustment. Includes25
clock tests covering original concurrent-tab protections plus offline task/break
timeline, missing/reconnect GPS, denied permission and uncertain command reopening.
Full Python and exact disposable PostgreSQL gate pending; no cloud update yet.
Main staging traffic verified100%00031-h5t; private Navigation tag00036-ray remains.
Existing1CPU/512Mi identity/resources retained. No V1/DNS/IAM changes or Twilio sends.

Next: finish local regression, push exact candidate, native PostgreSQL gate/cleanup,
verify budget and additive schema/backup, build frozen image and private no-traffic
staging candidate. Authenticated UI/phone and live location-scope acceptance remain.
