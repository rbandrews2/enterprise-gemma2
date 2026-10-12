# Time Tracker increment — October 11, 2026

Ray requested the TIME_TRACKER reference appearance, lightning branding, offline
shift/task timing, and location at punches, task changes and intervals. This
authorizes this focused module increment in Codex's checkout; Claude's checkout
is untouched. Reference: https://github.com/rbandrews2/dev/tree/main/TIME_TRACKER.

## Storage and API proposal

Reuse server-timestamped commands and audited offline-submission review.
Normal controls record device-time drafts while disconnected; a scoped local
snapshot and draft timeline survive reload once the authenticated shell loads.
Device times remain visibly unverified until admin reconciliation. No automatic
replay of ordinary commands at reconnect. Explicit logout/scope switching clears
local data. Loading the entire authenticated app without a network is outside
this increment; no service worker caches private pages.

Add `time_location_events`, keyed by organization/employee/request UUID, storing
client-reported event/task, optional command UUID/known shift, device and server
receipt times, coordinates/accuracy or explicit unavailable reason. GPS is evidence,
not proof of attendance. POST `/api/time/locations` is self-only, idempotent and
bounded; GET uses existing admin/member/organization access rules. No new external
provider, auth layer or employee-selectable write target. Capture on punch, task
change, reconnect and every five minutes while clocked in (including breaks).
Never backfill missing coordinates from a later fix. Browser permission and HTTPS
are required; closed/suspended mobile browsers cannot guarantee interval delivery.

Additive startup DDL is a migration: PostgreSQL review/validation precedes shared
deployment. Rollback code first; retain evidence table until reviewed retention
and deletion policies are agreed. No existing shift tables or data are rewritten.
No cloud deployment or paid provisioning is authorized by this document.
