# Completed forms, SMS and installed PWA update

Scope: replace separate saved-form submission chooser with Send to office next to
completed printable forms. Reuse immutable form_submissions storage and admin
review queue. No startup DDL or migration. Server validates the selected published
template revision and all field shapes/limits; retries compare payload hashes and
actor/organization. Office notifications contain a generic notice only, never form
contents. Member-triggered office notices target only that organization's admins;
normal SMS composition remains admin-only. Consent, verified phones, opt-outs,
active membership, provider status and ambiguous-send safeguards remain enforced.

Live inspection before changes: Twilio test mode ready, approved recipient count1;
admin phone Not enabled, no SMS outbox entries. Root sending blocker is account
phone enrollment/verification, not a proven credential or transport failure. Do
not claim a delivered SMS until provider/device evidence confirms it. WZOS runtime
must use public https callback URL and the existing Secret Manager bindings.

V1 recovered manifest at .local-recovery/core-netlify/manifest.json used standalone,
root scope and home-screen launch. V2 already used standalone. Keep V2 application
identity stable, add explicit standalone display override and Apple capability
metadata, and improve install/launch instructions. Browser chrome cannot be hidden
by webpage code; installation and launch from the app icon are required. Preserve
pending offline data; no automatic uninstall or storage clearing.

Official references: https://www.twilio.com/docs/messaging/api/message-resource
and https://www.twilio.com/docs/messaging/guides/track-outbound-message-status .

## Focused validation

- Fourteen targeted Python checks PASS (SQLite; no skipped cases in this run):
  immutable printable snapshots, retries and tenant isolation; actual membership
  checks for admin-only office destinations; recipient removal stops queued SMS;
  private form content excluded from SMS; Twilio request shape and signatures;
  verification status exposed without secrets/body.
- Seven Node install/phone-format checks PASS; modified JavaScript syntax PASS.
- Live account inspection: no contact enrollment and empty outbox after reported
  failed click. Existing phone UI required international format and displayed its
  errors far away at the page header. Accept common US formatting, show inline
  errors/status and reveal provider outcomes. A device test is still required.
- No live SMS was sent by this work, and no cloud change yet. Cloud Shell browser
  control timed out repeatedly; user was asked to reconnect. Mode remains test.

## Release preparation

Candidate core266e302 was pushed. Follow-up adds a bounded 30-second form send
wait (idempotent retry checks receipt without duplicating notifications) and
source-only release helpers. scripts/test_office_sms_postgres.sh runs only the
impacted PostgreSQL fixture classes in a disposable Unix-socket cluster; no
production database access. scripts/deploy_office_sms_update.sh requires an exact
40-character candidate commit, runs that focused gate, checks current live base
imageec8f4243 and flow-354f7a9 traffic, builds/stages, compares preserved runtime
config, cuts over, checks fourteen frontend files/version, and rolls traffic back
to flow-354f7a9 if live asset verification fails. It leaves SMS mode unchanged.
No claim that these cloud steps ran: browser connection is still unavailable.

## Live acceptance - October17

Source 6caf8eeda859a927ceaa2237a65c32cb1a01b7c5 is LIVE at
https://app.workzoneos.org/ on wzos-v2-accounts-office-6caf8ee, 100% traffic.
Image sha256:454a9747b76ea9528bd1f703f7a504503450f020695f658cd8aa771af91a173d.
Cloud Build 0a56b34e-8427-4136-85db-52df4de4bfe7 succeeded. Release exit0;
staged runtime configuration preserved; fourteen public assets match exact source;
version endpoint200; no owned disposable PostgreSQL cluster still running.
Rollback: wzos-v2-accounts-flow-354f7a9 (billing/security compatible).
No DDL, dependency, IAM, secret binding, ingress or sending-mode changes.

Validation: 11 focused PostgreSQL checks PASS, zero skips (7.403s), in addition
to prior 14 local Python and seven Node checks. Do not rerun unrelated suites.
Live signed-in admin browser: old saved-form chooser absent; Send to office sits
under Print/save PDF. Submitted one clearly labeled SYNTHETIC incident worksheet
(no incident occurred); actual server receipt and office queue entry appeared,
with an in-app admin notice. No SMS queued: admin phone remains Not enabled.
Proof outside Git: .local-data/release-20261017/live-office-receipt.png.

Read-only provider preflight using pinned Secret Manager values without printing
or saving them: Twilio account active, type Full; configured sender found and SMS
capable. No provider settings or voice webhook were modified. Runtime uses SID1,
auth-token1, sender2 (latest enabled references); public callback origin correct.
SMS remains test mode with the previously approved recipient only. No actual SMS
sent by agent. User asked to enter phone/consent and request code in live Messaging;
carrier/device delivery acceptance is pending. Never mark SMS fully accepted yet.

PWA standalone metadata and V1-equivalent launch guidance deployed. Actual Android
home-screen launch without address bar still needs device confirmation. Launch
installed app icon, not a browser link; preserve offline drafts, no storage clearing.
Next: read user's SMS result, inspect inline/provider error if any, finish phone
verification and one controlled notification; confirm installed-icon launch.
Broader member SMS activation remains separate from controlled test mode.

## SMS live checkpoint - October17 after release

User entered phone/consent and requested a verification code in Chrome.
Read-only Refresh verification status showed Sent to carrier for the approved
recipient. Thus real provider handoff is confirmed; device receipt and successful
code verification remain pending. Agent did not enter consent or request/resend
codes. Live Messaging page is preserved for user completion. No broader SMS mode
change. Prior statement that no live SMS was sent by agent remains accurate.

## Android installed launch acceptance - October17

Ray opened WZOS from its installed home-screen icon and confirmed both: no Chrome
address bar and no repeated Install WZOS prompt. This closes those two device checks.
It does not establish update-prompt, offline-draft or all-device acceptance.
