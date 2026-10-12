# Release assembly and online cutover checkpoint — October 12, 2026

Ray requested a publicly reachable V2 product tonight. Keep application sign-in,
admin/member authorization, organization isolation and edition entitlements.
Do not describe unfinished provider/field acceptance as completed production.

## Independently observed release gates

- Frozen code: 1afe3d6ec8da15b1dca9a0dcdae9d2d374d5814b.
- Full native PostgreSQL: 498 tests, 149.577s, failures/errors/skips all zero.
  Persistent evidence: /home/admin_/wzos-release-20261012/postgres-1afe3d6.log.
- Existing live schema compatible: no conflicts; only time_location_events missing.
  Reviewed additive SQL remains docs/migrations/20261011_time_tracker_locations.sql.
- SQL backup 1791784800000 SUCCESSFUL, ended 2026-10-12T06:53:30.190Z.
- Build f1a1b800-07f6-4f01-b545-13d1f758576a SUCCESS; immutable inherited
  source library validated during build. Uploaded only 117 selected runtime files.
- Candidate revision wzos-v2-accounts-00037-xot Ready, tracker-1afe3d6 tag,
  zero main traffic. No IAM/public/domain change performed.
- Rollback service export and IAM captured in the persistent evidence directory.
- Billing account overview October1–12: cost19.73, savings1.52, net18.21USD.
  Account-level displayed total, not a reconciled project-only Oct8–17 ledger;
  billing lag and ongoing/build charges remain relevant. Existing150USD cap retained.
- Local Time Tracker rendered desktop and phone-width with original eagle/black-gold
  treatment. Synthetic-only preview shows assignment notification unavailable because
  dispatch is registered only in the account-backed application; validate live there.

## Provider clarification

Ray reports the original Twilio number is registered and supports messaging/voice;
it is currently used by AIRA for incoming calls. Voice and incoming-message routing
are distinct. Do not remove AIRA's voice webhook for WZOS outbound SMS/MMS.
Inspect actual account/number/campaign and sender-secret binding before enabling
sending. WZOS text replies require the appropriate messaging webhook. No number,
secret or private account details recorded here; no provider send/routing change.

## Remaining before cutover

Verify candidate authenticated HTTP/UI and additive table, configuration/secret
bindings, actual public routing/TLS, production identity origins/passkey RP scope,
provider readiness and live Atlas availability. Public exposure needs the concrete
security-sensitive action confirmation required by browser policy. Complete release
limitations and rollback before requesting it. Source review, GPS retention, closed-app
push, automatic Meet creation, real recovery and training content remain open in
existing lists; do not silently call those finished.

## Live candidate acceptance and public-release boundary

- Candidate digest: sha256:d4c64f6eb9aa55c8a91dcf4dbee0ff6eda3161572e1cce95ef6e7029da7f0df0.
- HTTPS candidate HTML200 and unauthenticated location API401 through the operator
  proxy. Google synthetic admin sign-in and organization selection passed; account
  workspace/My jobs loaded without the synthetic-only preview's dispatch404.
- Live Time Tracker loaded original existing shift, task controls, history and review.
  Location history successfully returned no evidence; no actual GPS permission accepted
  or new attendance/location writes. Evidence: .local-data/tracker-live-00037.png.
- Routes enabled. Atlas private_vllm selected but WZOS_ATLAS_VLLM_ENABLED=0;
  the candidate does not currently provide live model inference. Must activate/test
  the intended engine before claiming completed Atlas-enabled product.
- Origin and passkey RP still target Cloud Shell preview, not app.workzoneos.org.
  Public cutover requires explicit origin/RP changes and credential re-enrollment.
- Current URL map gemma-load-balancer defaults to gemma-assistant-api-backend;
  it has no host-specific paths in the inspected export. Do not blindly replace a
  shared default backend without verifying TLS/DNS/other hostname dependencies.
- Three Twilio credential secrets exist; read-only Twilio account request succeeded.
  Saved sender matches an owned number supporting sms/mms/voice; its direct Voice
  and SMS webhook hosts are empty. One account number has an AIRA voice webhook.
  These observations do not prove messaging campaign approval or sender identity
  equivalence. No webhook changed and no messages sent. Runtime still lacks Twilio
  secret bindings/public callback URL.
- Ray selected admin@workzoneos.org for public admin login. Synthetic tester uses
  a shared weak test password; disable its admin access before public exposure.
  Real account credential creation/sign-in must be performed by Ray, not the agent.

## Account-creation diagnostics repair

Ray's real account creation returned only a generic failure. The client discarded
all provider errors; the agent cannot establish the precise failure from that text.
Read-only Google admin lookup returned403; do not treat that as account absence or
as the sign-up cause. No IAM expansion or password/verification change performed.

Client now maps approved provider codes to actionable messages without showing raw
payloads, keys or identifiers. Missing-account/invalid-login remain generic. Network
and malformed responses are handled. If sign-up succeeds but requesting verification
email fails, report that the account was created and offer Resend verification email;
clear tokens/password either way and retain the verified-email access requirement.
Full Node74passed/zero failures/skips, including10new provider-error/token-clear tests.
Next exact candidate PostgreSQL/build/deploy and user-operated retry; real failure
cause and real admin setup remain open until observed.

Password visibility control requested by Ray: eye button inside the input,
44px touch target, open/closed SVG states, accessible Show/Hide labels and pressed
state; password remains unchanged, defaults masked and remasks on submission.
Full Node75 passed/no skips; synthetic browser eye toggle rendered correctly.
No real password entered/created by the agent. No schema/backend changes.

## Password-eye/account-error cloud acceptance

Frozen code2b425601af9508f47798d08a531a9a4ed5933e95. Full Node75 passed;
full native PostgreSQL498 passed/zero failures/errors/skips,151.867s.
Buildd6aa530a-3ff0-4903-a721-4866e37be1e4 SUCCESS.
Private revision00038-yoz Ready, auth-2b42560 tag, zero main traffic.
No authentication/IAM/schema/public-routing changes. Synthetic local mobile/tap/
keyboard eye tests passed; evidence .local-data/password-eye-mobile.png.

Public routing correction: the inspected gemma-load-balancer URL map is not the
one attached to HTTPS. Actual target proxy gemma-load-balancer-target-proxy uses
app-workzoneos-org-url-map, whose app.workzoneos.org host and /* path currently
route to gemma-assistant-api-backend. gemma2-certificate is ACTIVE for that hostname.
Existing backend IAP is enabled. Retain its export as rollback; exposing V2 requires
reviewed host/path/backend and access changes, not blind default replacement.
User-operated real signup retry remains required; the generic earlier message did
not establish its actual provider failure. Do not bypass verification or create a
password for Ray. Atlas activation and provider readiness remain separate work.
Live acceptance after proxy update: candidate HTML200; served account.js byte-for-byte
matches frozen2b42560. Online sign-in refreshed and shows the closed-eye password
control; admin@workzoneos.org prefilled for user-operated retry. Evidence:
.local-data/password-eye-live-00038.png. Disposable PostgreSQL process cleanup
verified; local synthetic fixture stopped. New proxy expires after45minutes.
