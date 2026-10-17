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
