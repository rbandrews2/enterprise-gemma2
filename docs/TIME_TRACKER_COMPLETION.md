# Time Tracker local increment — October 11, 2026

Branch: `codex/time-tracker-offline-location`, based on the clean `enterprise-v2`
checkout. Claude's checkout and branch were not changed. No cloud deployment,
paid resources, production changes or customer communications.

## Behavior

- October11 palette correction: Ray designated the open Chrome page at
  https://clock.superiorllc.org/ as the color authority, superseding the slate
  GitHub demo. Live computed styles verified near-black145-degree base,
  orange/gold radial halos at18%/18%,82%/12%,60%/88%, a subtle white sheen,
  zinc900/80 fields, zinc800 borders and orange400 accents. Local CSS now uses
  those colors with neutral charcoal cards; browser computed styles and screenshot
  `.local-data/time-tracker-black-gold.png` verified. CSS/diff checks passed;
  no runtime, attendance, GPS or schema changes in this correction.
- Matches the reference's near-black gradient, charcoal rounded cards, orange
  accents and green/red circular punch buttons. Prominent lightning bolt and
  Time Tracker label in title/navigation. Mobile layouts preserve touch controls,
  keyboard focus and reduced-motion behavior. Work-order/note selectors hide
  during an active shift; the active job, task and duration stay visible.
- Regular clock controls work offline after a verified load. A persisted device
  timeline records punch/task/break times, total work excluding breaks and
  current-task duration. Reopening recovers the saved timeline once the app loads.
- Reconnect preserves unresolved device records. Attendance submission retains
  device time and original shift/version, is idempotent, and requires existing
  audited admin reconciliation. Submitted records remain visible locally until
  all are resolved; ordinary commands are not replayed with reconnect timestamps.
- Persisted pending online command IDs support retries after uncertain writes and
  reload. Sign-out/organization changes clear device data. Storage failure is
  visible and enables JSON download plus unload protection.
- Location requested at punches, task changes, breaks, reconnect/foreground and
  every five minutes while clocked in (including breaks). Fresh fixes include
  coordinates/accuracy; offline, denied, timeout and unavailable events preserve
  missing-fix reasons. No gap is assigned a later coordinate. The scoped outbox
  uploads automatically and retries with stable UUIDs. Location history shows
  device evidence and uses existing member/admin/team/tenant boundaries.

## Files and migration

`static/index.html`, `timeclock.js`, `timeclock.css`, `workspace.js` implement UI,
device persistence and location collection. Text-only module guidance updated in
`assistant.js` and `intelligence.py`. Backend `timeclock.py` adds POST/GET
`/api/time/locations`; `test_timeclock_locations.py` covers validation, retries,
command linking and authorization with inherited PostgreSQL cases.
`offline-clock.test.cjs` covers timeline, reconnect, storage and GPS behavior.

Additive startup DDL creates `time_location_events` and its shift index. Exact SQL:
`migrations/20261011_time_tracker_locations.sql`. Existing attendance tables are
unchanged. Review and PostgreSQL validation precede shared deployment. Roll back
code first and preserve evidence until retention/deletion is approved. No automatic
table deletion or attendance migration is included.

## Verified evidence

- Full Python: **343 tests, 273 passed / 70 PostgreSQL skips**, no failures/errors,
  349.406 seconds. Log `.local-data/time-tracker-full-python.log`. Full run preceded
  final guidance wording and JS-only layout refinements; guidance was retested:
  5 assistant-guidance and 12 Atlas-intelligence tests passed.
- Final full Node: **27 passed**, including 11 clock/offline behavior tests.
  Log `.local-data/time-tracker-node.log`. JS syntax and `git diff --check` passed.
- Location API: three SQLite cases passed / three inherited PostgreSQL cases
  skipped without configured database. Covers stable retry/conflict, complete
  fixes/missing reasons/time bounds, self-only writes, member/admin and tenant access.
- In-app browser: desktop branding/colors, synthetic clock-in, task switch,
  start break, clock-out, reload restoration, and location-history entries verified.
  Browser GPS timed out; missing-fix records for clock-in, task change, break and
  periodic interval were visible. No actual GPS fix or phone tracking claimed.
- 390 px and 320 px layouts: document widths 375 and 305, respectively, below
  viewport width. Temporary viewport reset. Synthetic screenshot:
  `.local-data/time-tracker-desktop.png` (ignored; local evidence).

## Remaining acceptance and operational limits

The authenticated shell is not cached: starting/reloading the complete app without
network remains unsupported. Once loaded, offline clock controls/timing work.
Browser suspension/closure can pause GPS intervals; a native/background solution
would require a separate design. Test HTTPS GPS permission/fixes, actual phone
loss/recovery, storage eviction, and concurrent tabs/devices before production.
Offline drafts retain the existing 50-record and 14-day submission limits; location
outbox is bounded at 2,000 events, uploaded in batches of 50. Full queues/errors
remain visible and evidence can be downloaded. GPS retention/export/deletion policy
still needs agreement. Locations are device-reported evidence, not verified attendance.

Next: run PostgreSQL gate including new location cases in a disposable schema,
review SQL, then deploy only within separately authorized staging scope and perform
real-phone GPS/offline acceptance. Local preview is on `http://127.0.0.1:8083` with
synthetic identities; it provides no production-authentication acceptance.
