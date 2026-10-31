# Production checkout repair - October 31, 2026

User authorized deploying the WZOS backend repair. Source candidate:158bea6;
invoice repair:d1ba27f. Prior live revision:wzos-v2-accounts-history-2d77bc6,
image sha256:100f17c262e3eab4abc3c5b88e9fc9d1bc0a685b8059f4642ed021254656c558.

Build dbee9af9-11e1-412a-8c1e-0e84e8a3de65 overlays only commerce_runtime.py,
purchase_lifecycle.py, purchases.py, subscription_upgrades.py, static/account.js,
and knowledge/billing/v2-stripe-catalog.json onto that exact live image. No
package upgrades, source-library replacement, schema changes or IAM changes.
Existing runtime identity, secrets and environment are preserved.

Validation already completed:78 PostgreSQL repair checks, deployed Core15 and
Enterprise25 monthly sandbox payment/activation, isolation and duplicate delivery.
No new live charge is authorized or needed for deployment health checks.

Deploy no-traffic candidate checkout-158bea6, verify readiness and protected
checkout/webhook routes, then switch traffic only after checks pass. Verify public
release version and service-worker update identity after cutover.
Rollback: route100% back to wzos-v2-accounts-history-2d77bc6.

Status: build/staging in progress. Production cutover not yet verified.
Cloud evidence directory:/tmp/wzos-checkout-production-20261031.

## Production checkout repair deployed - October 31, 2026

Authorized production release built from158bea6 over exact prior live image.
Build dbee9af9-11e1-412a-8c1e-0e84e8a3de65 succeeded; image
sha256:b85d385dd1dce8cd1debe3fd3aab25ef922794bdd517ea55294c9160778ced93.
Revision:wzos-v2-accounts-checkout-158bea6. Public cutover checks PASS: root200,
account commerce401 without authentication, unsigned webhook400, account.js200,
service worker200. Release6550185e282683104b04c0b2 differs from prior
970b793986986cc9adc34a77 and matches HTML plus service worker.
Existing runtime identity/env/secrets retained, no schema or IAM changes.
Direct tagged URL404 is expected under existing internal-and-cloud-load-balancing
ingress; protection preserved. Candidate Ready then public checks passed on cutover.
Rollback revision:wzos-v2-accounts-history-2d77bc6.
PWA release/worker identities verified; installed-device update banner interaction
not independently verified this turn. No live charge/customer send performed.
Time Tracker activation remains separate and deferred. Storefront files unchanged.

