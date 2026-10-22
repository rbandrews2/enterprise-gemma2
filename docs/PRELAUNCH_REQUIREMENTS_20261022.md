# WZOS prelaunch requirements

Updated October22,2026. Unchecked items require acceptance; a screen or integration
being present does not establish end-to-end readiness. Owners: Product = Ray;
Engineering = WZOS development. Keep evidence and the tested release identifier.

Latest release: signatures/compact weather/report review deployed as ui-358cf45;
focused Node18,SQLite8,PostgreSQL8PASS. Phone handwriting and exported PDF still
need field acceptance. See FORMS_WEATHER_RELEASE_20261022.md for live evidence.

## Release blockers for general customer onboarding

- [ ] Product + Engineering: complete one Core-admin, Core-member, Enterprise-admin
  and Enterprise-member journey from account creation/invitation through first job.
  Verify org isolation, seat limits (all active logins including admins), roles and
  the final Core/Enterprise feature matrix, including Messaging/Video meetings.
- [ ] Product: accept installed Android phone workflows: handwritten signature,
  Clear/typed alternative, saved office copy and printed/downloaded PDF; verify a
  Smart Field Voice draft opens visibly and office review produces confirmation.
- [ ] Engineering: verify deployed signature persistence with PostgreSQL, safe
  retries, cross-org denial and old unsigned records. Record the deployment result.
- [ ] Product + Engineering: Stripe live-account acceptance for purchase, activation,
  upgrade/one-time credit, seat changes, webhook retries, failed payment/cancellation
  and applicable configured tax. No test purchases/charges without authorization.
- [ ] Product + Engineering: close Twilio acceptance beyond successful verification:
  admin-to-consenting verified member notification, recipient scope, delivery/failure
  receipt, opt-out handling and final customer-texting configuration/registration.
- [ ] Product: finish Daily two-device audio/video, reconnect and Leave stopping
  microphone/camera. Recording/transcription remain off unless separately approved.
- [ ] Engineering: recover a backup into an isolated database and verify a submitted
  form/signature; confirm retention, monitoring, restore owner and rollback runbook.
- [ ] Product + Engineering: finalize privacy/retention terms for reports, signatures,
  location and media; publish customer support, billing/cancellation and incident
  contacts. Ensure installation/onboarding explains permissions and cloud processing.
- [ ] Engineering: targeted security release review of access boundaries, runtime
  secrets/IAM, upload quarantine/recovery and dependency findings; track remaining
  lower-severity findings. Do not claim SOC2 compliance without the required review.

## Feature-specific acceptance before enabling or promoting

- [ ] Smart Field Voice: actual-phone recording/revocation/offline behavior; quantities
  and incidents reviewed by worker; duplicate Send produces one office submission;
  raw audio/transcripts remain transient. Existing synthetic passes do not replace
  field acceptance. Confirm model budget/alerts and scale-to-zero configuration.
- [ ] Weather: accept compact local card with populated and missing values; verify
  changing location, permission denied, stale/unavailable states and active alerts.
  Confirm hourly monitoring's actual schedule and notices. Keep critical warnings
  visible; do not promise continuous/background emergency protection.
- [ ] Navigation: job route and ordinary start/end routes work; Google Maps launches
  active guidance. Communicate the handoff clearly; no in-PWA turn-by-turn claim.
- [ ] Time Tracker: clock/task transitions, offline continuity, reconciliation and
  location denial; device-estimated records remain unverified until reconciled.
- [ ] Work orders/My jobs: assignment arrival, member visibility/acknowledgment and
  admin updates; notification links land on the correct authorized job.
- [ ] Training: admin paste/replace/remove video URLs, embedded playback and member
  access; completion/assessment records reflect actual supported behavior.
- [ ] Atlas Security: upload/hold/recovery acceptance on deployed persistence;
  admin notifications first; clear reason, audited decision and safe recovery.
- [ ] Ask Atlas / Work Zone Guardian DOT answers: source edition/jurisdiction,
  pages/tables/corrections/applicability review and bounded pinned-model acceptance.
  DOT inference flags were last documented off; verify before advertising availability.
- [ ] Integration API: scoped credentials, revocation/rate limits/audit trail and
  tenant isolation; QuickBooks/Workday connector acceptance before claiming support.

## Launch-day checklist

- [ ] Publish only accepted features; hide or clearly label unfinished integrations.
- [ ] Record immutable image, traffic/version checks, rollback revision and on-call
  owner. Verify installed app detects the update without losing in-progress work.
- [ ] Confirm budgets/alerts, production service status and support availability.
- [ ] Run one bounded smoke journey; monitor errors/failed sends/payment events.

## Later roadmap (not prerequisites for the current PWA)

Android package first, then iOS; camera/time/location-stamped photo/KML concept;
additional DOT/state coverage. Preserve the working PWA while planning these.
