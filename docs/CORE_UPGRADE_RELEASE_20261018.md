# Core upgrade release - October18,2026

## Live provenance

Runtime source bf9f524304a994bc9ff9cb54b795271510df8491.
Build a651a66a-82eb-43c9-8193-621029f2ab77 SUCCESS.
Image us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:f347f6901acb223b412ae729aa52afc47a1210804b861916ecfc18f46f5e3873.
Revision wzos-v2-accounts-upgrade-live-bf9f524,100% traffic.
Rollback wzos-v2-accounts-upgrade-hold-bf9f524 uses the SAME new image with new
upgrade requests disabled; signed webhook reconciliation remains available.

## Acceptance and changes

- Existing restricted Stripe key's Invoices/Subscriptions Write permissions were
  explicitly approved and saved by Ray; independently reopened persisted editor
  confirmed both. No other permission, credential rotation or Google IAM change.
- Existing runtime pinned key passed a non-persisted live invoice preview: approved
  Enterprise catalog, one-time$20 credit, automatic_tax.status complete, total$1228
  for synthetic state/postcode. No customer, subscription, persisted invoice or
  payment created/modified. This is not paid upgrade/proration acceptance.
- Exact runtime source: PostgreSQL810 PASS/no failures/errors/skips; Node136 PASS;
  Stripe SDK7 PASS; pip check clean. Earlier local19 billing/6 UI and synthetic
  desktop/mobile dialog checks remain evidence; full suites not needlessly repeated.
- Staged comparison preserved existing runtime identity, resources, secret refs,
  ingress, Daily policy, hourly weather flags and SMS modes; only image and new
  WZOS_CORE_UPGRADES_ENABLED flag changed. Generated revision creator metadata was
  separately verified against admin@workzoneos.org, not treated as an IAM change.
- Zero-traffic revisions were imported but inactive/Retired. Brought hold revision
  to100% first with upgrades disabled; public startup/assets/auth/media checks
  passed. Then switched to enabled live revision; public version/auth checks passed.
  Final deployment exit0 and independent service traffic readback verified100%.
- Post-release read-only schema check PASS: compatible=true, missing[],conflicts[].
  Only reviewed organization_upgrades startup table added. Pre-release SQL backup
  1792216800000 SUCCESSFUL. Owned SQL proxy stopped; independent process read empty.
- Real browser: existing verified admin selected Molecular Project Development LLC
  and entered the Enterprise dashboard. No upgrade nudge on this Enterprise account,
  as designed. No new synthetic live identity/organization or billing record created.

## Capability and limits

Core organization admins can review Enterprise estimates and explicitly authorize
upgrading the existing verified paid subscription. Members have no billing offer
or upgrade API access. Current receipts remain historical; Enterprise/seat changes
require authoritative paid webhook reconciliation. No duplicate subscription.
Established paid Core customers receive one$20 credit; Stripe Tax and proration
are retained. Legacy subscriptions without verified WZOS ownership mapping require
billing review; do not guess matching by email.

Real paid existing-Core acceptance remains a user-led financial action. Do not
charge for testing or claim it passed from the catalog preview. All other remaining
integration/device checks are still listed in REMAINING_TASKS.md; mobile redesign
is deferred until that list is addressed.

Cloud evidence root: $HOME/wzos-core-upgrade-path.txt. Main artifacts:
upgrade-deploy.log/exit,upgrade-live-service.json,upgrade-provider-preview.json,
upgrade-build.json,upgrade-schema-after.json. UI proof outside Git:
.local-data/release-20261017/live-core-upgrade-release.png and
stripe-upgrade-permissions-after.png. Preserve this evidence and billing records.

Next: Atlas private31B restart scope in ATLAS_RESTART_SCOPE_20261018.md. Current quota,
model metadata, private bucket-viewer binding, subnet and identity verified. Actual
model service remains absent/production Atlas disabled. No GPU started by this release.
