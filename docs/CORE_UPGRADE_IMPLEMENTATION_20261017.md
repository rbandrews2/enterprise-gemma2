# Existing Core subscription upgrade

Implementation scope: reuse the existing verified Stripe subscription/customer and
signed lifecycle webhooks. Never create a second subscription for an organization.
Admin-only UI and server authorization; members receive no offer or billing data.

Approved offer: Enterprise $999 setup, $249/month including25 active logins,
$7/month/additional login; established paid Core organizations receive one $20
credit. Preserve the existing billing date, with Stripe-calculated proration and
applicable Stripe Tax shown before confirmation. Do not perform a real payment
during agent acceptance.

Proposed additive startup DDL: organization_upgrades (organization_id primary key,
request_id unique, purchase_request_id, subscription_id, customer_id, seats,
status, payload, created_at). Payload stores the immutable quoted Stripe parameters,
proration date, quote expiry, previous paid service expiry and resulting invoice ID.
No credentials, payment methods or raw card data. Keep historical purchase receipts.

Flow: quote (no charge) -> explicit admin payment confirmation -> update the same
subscription with payment_behavior=pending_if_incomplete and always_invoice ->
hosted Stripe invoice if payment needs action -> signed webhook retrieves current
subscription -> atomic edition/seat grant after matching paid upgrade. Unpaid
upgrade retains only previously paid Core access, never Enterprise. Retries reuse
the same provider idempotency key; ambiguous requests older than24hours require
review, not automatic re-charge. Legacy subscriptions without a verified WZOS
ownership mapping are ineligible for automatic upgrades.

Rollout: default OFF until disposable PostgreSQL, SDK contract, role/tenant,
duplicate/concurrency, payment-failure/recovery and browser checks pass. Current
production image and hourly weather configuration remain unchanged while building.
Rollback must preserve upgrade reconciliation and billing enforcement; pausing new
upgrade requests must not disable already-paid fulfillment. No destructive DDL.

References inspected: Stripe pending updates, invoice previews, prorations and
subscription lifecycle documentation; existing purchases.py/purchase_lifecycle.py.

## Candidate validation

Implemented backend/Stripe adapter and Core-admin dialog, including a landing
launch card for mobile discovery.16 focused SQLite billing cases PASS;6 focused
Node dashboard cases PASS. Synthetic provider only; no Stripe payment/subscription
was created or changed. Sandbox Windows temp ACL blocked the first attempt;
unchanged tests passed with normal temporary-file access outside that sandbox.
Node subprocess isolation was blocked; direct node:test execution passed6 cases.
PostgreSQL/full-suite/SDK/provider/browser gates remain OPEN. Live upgrades remain
OFF; current production weather-hourly-1017 is unchanged by this source candidate.
Expired unpaid upgrade invoices retain previously paid Core access only and require
billing review before a fresh charge. Unmapped legacy/V1 subscriptions require an
explicit verified billing association; no email-based ownership guessing.

Synthetic browser acceptance: desktop and390px mobile estimate/consent/pending
flow rendered; no real provider calls. Corrected only the new consent control's
scoped layout; existing mobile module design remains unchanged. Browser CSS cache
initially retained the old local stylesheet; a fresh preview origin confirmed the
18px checkbox/flex layout and scrollable modal. Evidence outside Git:
.local-data/release-20261017/core-upgrade-estimate.png and core-upgrade-mobile.png.
Full cloud gate started on2febb92 using a disposable Unix-socket database; outcome
pending. Subsequent source delta is frontend consent classes/CSS only; Python
backend and test sources are unchanged. No live release or activation yet.

Additional review repairs: confirmation re-reads Stripe and checks the quote's
billing fingerprint, then re-previews tax/balance before making a provider write.
A changed quote requires fresh consent/estimate. Pending paid-Core exceptions are
bounded at read time by the original paid period, even without a later webhook.
19 final focused SQLite cases PASS (67.556s);6 Node cases PASS. A new exact-source
cloud gate is required for these backend guards; the earlier2febb92 full gate is
baseline evidence only. Live upgrade flag remains OFF.

Baseline cloud2febb92 PostgreSQL gate PASS:804 tests,401.645s,0 failures/errors/skips.
SDK install then blocked because requirements-commerce.txt requested cryptography
>=46,<47 while webauthn3.0.1 requires>=49. Installed verified accounts graph is
cryptography50.0.2 / pyOpenSSL26.4.0 (requires>=49,<51). Correct commerce declaration
to>=49,<51; retain the reviewed runtime dependency graph rather than downgrade it.
Do not report the baseline overall gate PASS: SDK/Node did not execute after that
resolver failure. Final candidate must pass all gates after the declaration repair.
