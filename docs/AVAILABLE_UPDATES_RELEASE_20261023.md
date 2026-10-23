# Available updates release — October 23, 2026

User authorized deployment of available updates, including previously tested work.
Candidate application content is b693d8b; a1d24d1 adds release tooling only.
The runtime, requirements and tests are identical between those two commits.

## Included

- Header notification area replaces floating review notices.
- Enterprise-only messaging/meeting enforcement and dashboard visibility;
  consent withdrawal remains available after downgrade.
- Object/embed CSP hardening and reviewed dependency repairs.
- Admin-only employee roster CSV import: template, review, duplicate/error
  handling, explicit confirmation and receipt. Both Core and Enterprise.

No new provider activation, IAM roles, customer messages or paid inference tests.
Existing Voice, weather, Stripe, secret pins, identities and scaling are preserved.
DOT inference/source approval remains separate and disabled as before.

## Schema and rollback

Only employee_roster and employee_import_batches may be newly initialized,
alongside already documented preview-only tables. See employee-import-additive.sql.
Check existing column compatibility and a successful backup within 24 hours first.
Rollback returns traffic to wzos-v2-accounts-pins-1022181839 and leaves the two
additive tables intact; older code ignores them.

## Acceptance evidence

- Local Node: 179 passed, no failures/skips, 2.082 seconds.
- Linux Node24.10.0: 179 passed, no failures/skips, 5.487 seconds.
- Narrow-screen synthetic import at390px: two imported/one duplicate skipped;
  confirmation required, visible completion receipt. Actual import JS/API exercised
  through isolated synthetic harness. Screenshot outside Git:
  .local-data/employee-import-mobile-20261023.png. Same-origin framing applies
  only to this local harness; production frame protections are unchanged.
- Full PostgreSQL gate: 919 passed in430.662seconds, zero failures/errors/skips,
  disposable private cluster. Earlier accepted real Voice/SMS/billing/human
  acceptance checks were not replayed.
- Public checker72aef6b additionally verifies the exact employees.js bytes and
  anonymous roster401. This operational helper does not change app/test content.

Cloud evidence root: /tmp/wzos-release-20261023.RFKngPNY.
Home pointer: $HOME/wzos-release-20261023-path.txt.
## Deployed and accepted

Build f90622b0-c415-4d3e-a279-2a32536f4180 SUCCESS.
Revision wzos-v2-accounts-ui-a1d24d1 serves100% (independent readback confirmed).
Image sha256:e29aeee408ea92f2372774a8fa9562e6b2b05b8dc9efa9be49c6bc2fc0cff7dc.
Public version e83ce03ec082a537e4795648.
Preflight, schema/backup, build, drift, staged settings, public asset/API and
traffic checks all PASS; deploy.exit0. No rollback required.

Signed-in live browser: notification appears in the header; Import employees
appears in Account and dashboard; dashboard button opens the dialog; authorized
roster read returns No employees imported yet. No live imports or notifications
sent as a test. Screenshot: .local-data/live-release-20261023.png.

Durable cloud evidence: $HOME/wzos-release-evidence-20261023 (logs, exit codes,
schema/backup readback, immutable digest, before/staged/live/independent metadata).
Do not rerun these unchanged checks unnecessarily. Physical-device acceptance
and remaining prelaunch/provider/source-review work are separate.
