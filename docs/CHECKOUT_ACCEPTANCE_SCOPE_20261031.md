# Isolated paid-checkout acceptance deployment

## Additional one-shot SQL setup approval required

User approved the isolated deployment and then prioritized Core/Enterprise before
Tracker. Test database and dedicated service account are created. Existing
`wzos_app` has neither CREATEDB nor CREATEROLE; user does not have the postgres
password. Do not reset postgres or broaden the existing application login.

Prepared script: scripts/provision_checkout_test_database.py. Proposed new login
`wzos_checkout_setup_20261031` receives Cloud SQL's default administrative SQL
privileges across this instance, including the ability to affect the production
database. The script only connects to the empty test database, creates the limited
`wzos_checkout_test` login, grants test schema access, stores its DSN in the
acceptance-only secret, and deletes the temporary administrator in finally.
Its password expires after one hour; cleanup is independently read back. No app
runtime receives the temporary administrator credential. No production records
or existing passwords are changed. This broader temporary access was NOT part of
the original test-runtime approval and needs specific confirmation before running.

Prepared, not deployed. No live payments, customer messages or production writes.

## WZOS Core and Enterprise

- Build Dockerfile.checkout-acceptance from this checkout. It reuses the existing
  account, purchase, licensing and signed-webhook handlers; no fake fulfillment.
- New database `wzos_checkout_acceptance` on existing instance
  `enterprise-gemma2:us-central1:wzos-v2-staging-db`. Dedicated SQL user restricted
  to this database; do not reuse production database credentials.
- Dedicated runtime identity `wzos-checkout-acceptance@enterprise-gemma2.iam.gserviceaccount.com`.
  Cloud SQL connection permission; access only to test API-key version2 and new
  acceptance database, webhook-signing and encryption secrets. No production
  secrets, file buckets, Firebase management or other application permissions.
- Two services in us-central1, each 1 CPU/512 MiB, min0/max1, timeout60:
  `wzos-checkout-acceptance-control` requires Cloud Run IAM, invocation only by
  admin@workzoneos.org; `wzos-checkout-acceptance-webhook` publicly accepts only
  signed webhook requests plus a generic return page. Verify private IAM before
  binding credentials or invoking checkout. The private synthetic buyer selector
  is NOT an authentication credential. Never expose the control service publicly.
- Explicit TEST mode and test catalog; pin API secret version2 (version1 is live).
  Startup refuses any database name other than `wzos_checkout_acceptance`.
- Create a Stripe TEST destination for the public service only. Save its signing
  secret directly to the acceptance secret, never Git/chat/logs. Google/Stripe
  credential entry that needs browser handoff remains user-operated.
- Test Core15 and Enterprise25 purchases, actual Stripe-signed delivery, receipt
  ownership, activation redemption and duplicate event. Cancel owned synthetic
  subscriptions afterward. Record event/delivery IDs and database results.
- No new Cloud SQL instance. Cloud Run/build/secret usage can incur charges;
  scale-to-zero is not a spending cap. Remove the temporary services, test endpoint
  and runtime grants after acceptance, preserving sanitized evidence. Database
  deletion requires explicit disposable-data scope; do not touch `wzos`.

## Time Tracker

The existing Supabase project ebzfbuqclkumncnugbvq cannot create a development
branch: its plan does not support branching (provider returned PaymentRequired).
No branch was created and no plan was upgraded. Production company data must not
be used as a substitute. A separate test project or an approved plan upgrade is
needed before deploying the real authenticated Tracker checkout and migration.
Netlify staging must bind only that isolated project's keys and test Stripe keys.
Production Netlify environment variables and existing webhooks remain unchanged.

## Configuration repair and evidence

WZOS now supports explicit test catalog and return origin, forbidden in live mode.
Tracker supports a separately allowlisted test return origin; live remains fixed
to clock.superiorllc.org. Test-only Core/Enterprise monthly catalogs were created
in Stripe and saved in knowledge/billing/acceptance-stripe-catalog.json.
No payments were created in this increment.

Focused checks: 4 Python staging-config checks PASS; 3 acceptance-surface checks
PASS; 26 Tracker checkout/config checks PASS. Initial Python invocation lacked
the pinned Stripe package; installed15.6.0 in ignored local test dependencies and
reran successfully. PostgreSQL/external delivery are still separate open gates.
New acceptance startup invokes existing account/licensing/purchase DDL only in
the new test database. No production migration is introduced by these files.
