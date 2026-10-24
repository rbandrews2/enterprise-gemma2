# Prelaunch checklist — human involvement

## User-confirmed acceptance — October23

- [x] Created a work report using voice and WZOS successfully.
- [x] Created a Daily Work Report using voice and WZOS successfully.
- [x] Reviewed the resulting form and cleared the notification area.
- [x] Created an organization successfully.
- [x] Uploaded the employee roster successfully using CSV.

Evidence: Ray explicitly confirmed these completed workflows in chat. Exact test
time/release and report identifiers were not supplied. Reuse this acceptance;
do not repeat unchanged successful scenarios. Startup latency, failure recovery,
permission edge cases and employee credential provisioning remain separate.

Updated October 22, 2026. [Scope and release evidence](PRELAUNCH_REQUIREMENTS_20261022.md)
| [Codex checklist](PRELAUNCH_CODEX_20261022.md)

Owner: Ray / Product, consenting testers and qualified reviewers where needed.
Codex prepares screens, steps and evidence first. Human participation is for
physical-device results, business decisions, secure sign-in or necessary approvals.
Record results and the tested release. No open item is completed by this split.

Engineering testing has now started. See
[October22 results](PRELAUNCH_ENGINEERING_RESULTS_20261022.md) and
[privacy/retention decisions to approve](PRELAUNCH_PRIVACY_DECISIONS_DRAFT_20261022.md).
No participation is needed to repeat passing automated checks. The concise next
device checks are signature/PDF on Android, one consenting SMS
delivery/opt-out, two-device meeting media and installed-update preservation.
SMS is still in test mode; qualified DOT review and actual connector acceptance
remain prerequisites before customer availability claims. Existing budget is
USD50 with alerts; name its recipient/owner and approve an operating budget.

## General onboarding blockers — human acceptance

- [x] Smart Field Voice incident acceptance (Ray, October22): correct quantities/
  wording, notification received inside WZOS, form reviewed and notification
  cleared afterward. Recorded in VALIDATION_LEDGER_20261022.md; no retest needed
  without a relevant change/new issue.

- [ ] Accept the Core/Enterprise and admin/member feature matrix and prepared
  onboarding journeys against the intended customer experience.
- [ ] On installed Android WZOS, draw a signature, Clear it, try the typed alternative
  and inspect the office copy and actual printed/downloaded PDF.
- [ ] Authorize and participate in prepared Stripe live-account acceptance:
  purchase/activation, upgrade/one-time $20 credit, seats, failed payment,
  cancellation and applicable tax. Agree on real charges/subscription changes
  beforehand; Codex handles technical webhook/retry checks separately.
- [ ] Supply a consenting verified member for the prepared Twilio check; confirm
  delivery to the intended phone and opt-out. Approve final customer-texting
  configuration and supply any required business registration information.
- [ ] With two consenting devices, confirm Daily audio/video inside WZOS, reconnect
  and Leave stopping microphone/camera. Recording/transcription stay off unless
  separately approved.
- [ ] Approve privacy/retention terms for reports, signatures, location and media;
  confirm support, billing/cancellation and incident contacts and availability.
  Review prepared installation/cloud-processing explanations.
- [ ] Name the backup/restore owner and accept recovery/rollback responsibilities
  after Codex provides isolated-restore evidence.

## Feature-specific human acceptance — before enabling or promoting

- [ ] Smart Field Voice: retained/denied/revoked microphone permission, stalled
  processing and offline recovery. Successful voice report creation and form
  review/notification clearance passed above; do not repeat unnecessarily. Confirm
  model operating budget/alert ownership separately.
- [ ] Weather: accept the compact card with actual location changes, denied
  permission and prepared stale/alert scenarios. No weather configuration change
  is implied; hourly monitoring is not continuous emergency protection.
- [ ] Navigation: confirm job and ordinary routes launch Google Maps on the phone
  and guidance starts there; accept the handoff wording.
- [ ] Time Tracker: try clock/task/offline/reconnection/location-denial flows on a
  phone and confirm reconciliation is understandable.
- [ ] Work orders/My jobs: consenting admin/member testers confirm assignment
  notifications, acknowledgment and links to the correct job.
- [ ] Training: confirm video-link controls and actual playback on target devices;
  accept supported completion/assessment behavior.
- [ ] Atlas Security: accept prepared synthetic hold/recovery, admin-first notices,
  explanations and recovery controls. Do not alter real customer files/users to test.
- [ ] Ask Atlas / Work Zone Guardian: obtain qualified review of governing editions,
  jurisdiction, tables/corrections and applicability before field-use claims.
  Approve any needed model pilot/activation outside existing scope; availability
  remains conditional on technical and content acceptance.
- [ ] External integrations: provide authorized provider-account access/consent
  through secure sign-in and participate in actual QuickBooks/Workday connector
  acceptance before those integrations are advertised as supported.

## Launch decisions and availability

- [x] Ray supplied monitored operational-alert destination info@workzoneos.org.
  Four enabled policies connected; configuration readback PASS. Inbox receipt
  has not been tested; channel verificationStatus was not returned.
- [x] Ray explicitly approved the bucket-scoped retired-file cleanup repair.
  [Scope and rollback](FILE_CLEANUP_ACCESS_PROPOSAL_20261022.md) applied and exact
  additive policy readback PASS; no customer cleanup run as a test. Shared-bucket
  scope, existing queues, holds and retention remain documented.

- [ ] Approve accepted launch features and treatment of unfinished integrations.
- [ ] Confirm on-call/support, restore and budget-alert owners are available;
  resolve business decisions surfaced by technical review.
- [ ] Accept installed-app update behavior on the phone, including preservation of
  in-progress work, using prepared steps.
- [ ] Review final evidence/remaining risks and give go/no-go where a new release
  decision is required. Complete secure sign-in or new-access approvals only when
  an outstanding step needs them. Keep credentials out of chat and Git.
