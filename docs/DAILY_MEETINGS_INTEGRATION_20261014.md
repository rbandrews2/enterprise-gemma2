# Daily embedded meetings integration - October 14, 2026

## Decision and implementation
Ray selected Daily, created its account, provided public domain `wzos.daily.co`,
and reports saving `wzos-v2-daily-api-key` in Google Secret Manager.
Live calls are not accepted yet. Public app revision remains 00044-xim.

The existing schedule editor now selects Schedule only, WZOS embedded meeting,
or a legacy Google Meet link. Admins alone save schedules and prepare private
rooms; authorized members join existing rooms. Both editions retain meetings.
Assigned meetings restrict joining to assigned members plus organization admins.
Legacy Google Meet links continue to open separately.

The existing TV hosts pinned Daily Prebuilt SDK 0.93.0, with explicit Join,
Leave and Full screen controls. Camera/microphone start off. Selecting a card
or visiting the page does not create a call. Destroy the call on leaving the
module, sign-out, organization switch, page hide or offline transition. Late
requests cannot reopen a previous organization's frame. Join tokens remain only
in memory, never localStorage, logs or URL parameters. Actual joined SDK event
is required before showing CONNECTED.

## Backend and migration
New routes: authenticated GET /api/meetings/config; admin-only POST
/api/meetings/{id}/prepare; scoped POST /api/meetings/{id}/join.
Only catalogued schedule IDs are accepted; browser cannot supply room hosts.
Private room names hash organization, schedule ID and revision. Limit 10 people,
60-minute schedules, join window from 15 minutes before start to scheduled end;
5-minute room-bound token issuance. API response bounded 64 KiB, fixed HTTPS
provider host, no redirects, bounded timeout, safe error messages, no retries.
Six requests per user and 30 per organization per minute per runtime process.
Limits are not a global usage quota across Cloud Run instances.

Startup DDL in scripts/daily_meetings_schema_review.sql adds daily_meeting_rooms.
No existing table columns or historical records are rewritten. Deploying this
code applies the additive DDL. Existing PostgreSQL advisory writer lock serializes
prepare and schedule edits. Provider close requests occur inside schedule saves:
provider failure rejects the edit rather than claiming successful cancellation.
A remote close followed by local transaction failure cannot be atomically undone;
retry or reload may be needed, and old-room re-entry fails closed.

Rollback: disable WZOS_DAILY_ENABLED, route traffic to 00044-xim, retain the new
table. Stop active calls and verify provider expiry before disabling key access.
Do not drop this table during rollback. Remote rooms expire; media acceptance
must verify that updating room expiry ejects already connected participants.

## Secure activation proposal
Use only domain wzos.daily.co. Grant the existing runtime service account
wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com secretAccessor on only
wzos-v2-daily-api-key. Bind enabled version 1 to WZOS_DAILY_API_KEY; configure
WZOS_DAILY_DOMAIN=wzos.daily.co and WZOS_DAILY_ENABLED=1 on the tested revision.
No project-wide grant, no API key in Git, browser code, terminal output or chat.
CSP frame and camera/microphone permissions add only https://wzos.daily.co.
WZOS identity/storage remain Google-backed; participant display name, hashed
organization/user identifier, network information and call media go to Daily
when the user explicitly joins. Recording/transcription add-ons remain off.

First controlled acceptance: two consenting devices, one synthetic 5-minute
meeting (10 participant-minutes), no recording/transcription/invitations.
After the published free allowance this would cost $0.04 at $0.004 per
participant-minute; this is an estimate, not a spending cap. No paid subscription
or customer calls are authorized by the local implementation.

## Validation and remaining gates
Local focused Python: 20 passed, eight PostgreSQL cases skipped.
Full Node: 96 passed, zero skips. Full local Python574 passed with169 PostgreSQL skips; exact PostgreSQL gate running.
Provider tests use httpx.MockTransport, UI tests use a mocked SDK; neither proves
real audio/video, Android/fullscreen, denied camera permission, or cancellation.
Verify the secret metadata only; never read the key into an agent output.
Required: exact PostgreSQL gate, schema/backup/rollback check, scoped credential
activation approval, guarded build/release and actual two-device acceptance.
Already joined participant revocation is not instant merely because a WZOS
membership changes or token expires. Room expiry/host removal applies; confirm
and define the immediate-revocation policy before marking this production ready.

## Official references
- https://docs.daily.co/reference/rest-api/rooms/create-room
- https://docs.daily.co/reference/rest-api/rooms/update-room
- https://docs.daily.co/reference/rest-api/meeting-tokens/create-meeting-token
- https://docs.daily.co/reference/daily-js/factory-methods/create-frame
- https://www.daily.co/pricing/video-sdk/
