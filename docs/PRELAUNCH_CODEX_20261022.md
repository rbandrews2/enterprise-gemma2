# Prelaunch checklist — Codex

Updated October 22, 2026. [Scope and release evidence](PRELAUNCH_REQUIREMENTS_20261022.md)
| [Human checklist](PRELAUNCH_HUMAN_20261022.md)

Owner: Codex / Engineering. Complete within existing access and authorization,
using synthetic records and focused checks. Prepare human checks before requesting
participation. If sign-in, new permissions, spending or a real send is necessary,
hand only that dependency to the human list. Record evidence and release identifiers.
This list does not authorize new charges, access grants or customer communications.
Reorganizing requirements does not start tests or establish acceptance.

## General onboarding blockers — technical work

- [ ] Validate Core-admin, Core-member, Enterprise-admin and Enterprise-member
  account/invitation-to-first-job journeys with synthetic identities. Check tenant
  isolation, roles, seats including admins and the agreed feature matrix, including
  Messaging/Video meetings. Prepare concise human walkthroughs.
- [ ] Consolidate deployed signature evidence: PostgreSQL persistence, safe retries,
  cross-org denial, unsigned historical records and office/print/download consistency.
  Existing focused checks passed; identify remaining evidence gaps before retesting.
- [ ] Check Stripe purchase/activation, upgrades and the one-time $20 credit, seat
  changes, verified/idempotent webhook retries, failed payment/cancellation and
  configured tax using fixtures or sandbox resources. Prepare live acceptance
  without charging or changing real subscriptions.
- [ ] Check Twilio organization/recipient scope, verified consent, opt-out,
  delivery/failure receipts and configuration using mocks/read-only inspection.
  Prepare one bounded consenting-recipient check; do not send it yet.
- [ ] Prepare and perform an isolated backup restore within existing authorization;
  verify a submitted form/signature, retention, monitoring and rollback steps.
  Obtain the named restore owner from the human list.
- [ ] Review retention implementation; draft privacy/retention documentation for
  reports, signatures, location and media. Prepare support/billing/cancellation/
  incident pages and onboarding permission/cloud-processing explanations for approval.
- [ ] Review security boundaries, runtime secrets/IAM, upload quarantine/recovery
  and dependency findings; track remaining lower-severity findings. Do not claim
  SOC2 compliance without the required review.

## Feature-specific technical acceptance

- [ ] Smart Field Voice: verify job/edition/access enforcement, review/receipts,
  duplicate submission protection, interrupted/offline handling and transient
  audio/transcripts. Inspect model budget alerts and scale-to-zero configuration.
- [ ] Weather: check populated/missing/stale/unavailable states, location handling,
  critical alerts and actual hourly schedule/notices. Use controlled data for edge
  cases; do not change weather permission/tracking configuration. Avoid continuous
  emergency-protection claims.
- [ ] Navigation: verify job and ordinary start/end routes plus Google Maps handoff
  links/copy. Do not advertise in-PWA turn-by-turn guidance.
- [ ] Time Tracker: check clock/task transitions, offline continuity, reconciliation
  and location denial; device-estimated records stay unverified until reconciled.
- [ ] Work orders/My jobs: check assignment arrival, authorized member visibility,
  acknowledgment, admin updates and notification links to the correct job.
- [ ] Training: check admin paste/replace/remove video URLs, embedded playback,
  member access and accurate supported completion/assessment behavior.
- [ ] Daily: inspect embedded-meeting configuration and prepare the two-device
  audio/video/reconnect/Leave check. Keep recording/transcription off.
- [ ] Atlas Security: check deployed synthetic upload/hold/recovery persistence,
  admin-first notification, reasons, audited decisions and safe recovery.
- [ ] Ask Atlas / Work Zone Guardian: inventory source editions, jurisdictions,
  pages/tables/corrections and applicability questions. Verify inference flag status
  before availability claims. Prepare bounded pinned-model acceptance; paid
  inference requires applicable approval and budget.
- [ ] Integration API: check scopes, revocation, rate limits, audit trail and tenant
  isolation. Prepare QuickBooks/Workday connector acceptance before support claims.

## Launch preparation

- [ ] Hide or clearly label unaccepted features according to approved launch scope.
- [ ] Record immutable image, traffic/version checks and rollback revision; prepare
  installed-app update checks protecting in-progress work.
- [ ] Inspect production services, budget/alert configuration and monitoring of
  errors, failed sends and payment events. Flag gaps for the human owner.
- [ ] Prepare one bounded smoke journey and final evidence summary. Execute release
  checks/deployment only within applicable release authorization.

Technical preparation does not close the linked human acceptance requirements.
