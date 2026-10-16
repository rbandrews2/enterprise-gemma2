# Checkout runtime integration

Scope: new organization purchases through authenticated WZOS, Stripe-hosted
Checkout, verified payment activation and recurring billing state. Existing Core
upgrades stay separate: no duplicate subscription or unverified credit application.
Members with an existing organization receive no purchase/upgrade controls.

The runtime remains opt-in. No deployment, live payment, secret grant or customer
message is authorized merely by loading this module. Use Secret Manager-mounted
Stripe/encryption secrets; no browser keys or activation codes in URLs/logs.

## Additive startup schema review

When commerce is enabled, existing purchase_requests/purchase_events DDL from
scripts/purchase_seats_schema_review.sql runs, plus purchase_subscriptions below.
Disabled commerce creates none of these tables. No existing customer rows changed.

```sql
CREATE TABLE IF NOT EXISTS purchase_subscriptions (
  request_id TEXT PRIMARY KEY, subscription_id TEXT NOT NULL UNIQUE,
  customer_id TEXT NOT NULL, status TEXT NOT NULL,
  access_enabled INTEGER NOT NULL CHECK(access_enabled IN (0,1)),
  version INTEGER NOT NULL
);
```

Events resolve invoice -> subscription -> locally bound purchase/activation ->
organization; client metadata cannot select an organization. Authoritative
subscription status, paid latest invoice and approved recurring price quantities
determine access. A version check prevents a slower concurrent response overwriting
a newer observation. Unknown subscriptions cannot create grants. Failed/cancelled
billing prevents new activation and licensed workspace access while retaining all
records; identity and organization chooser remain available for recovery. Receipt
activation-code retrieval is denied while the subscription needs attention.
Legacy/manual licenses are unaffected. Rollback keeps all purchase and entitlement
tables and uses the prior image. Do not delete billing history on rollback.

Required validation: forged/duplicate/out-of-order events, pre-checkout lifecycle
events, paid/failed/recovered/cancelled state, cross-account/private receipts,
identity-derived purchasing email, disabled runtime, price/seat matching, exact
PostgreSQL startup schema, and hosted Checkout return flow. Live remains blocked
until these checks and secret bindings are accepted.

## Paused checkpoint - October16

Ray requested skipping unrelated steps and focusing on checkout; then requested
saving progress before refreshing the computer. All edits are saved locally.
No live deployment, payment, webhook registration or runtime secret grant occurred.

Implemented in source:
- Opt-in runtime mounted in the accounts app. Default disabled; no purchase DDL
  is applied when disabled. GET /api/account/commerce returns no offers for members
  or other existing organization users. POST /api/account/checkout derives email
  from verified sign-in, never a browser field.
- Hosted checkout UI in the new-organization chooser, server-provided pricing/seat
  limits, retry request identity, approved redirect hosts and verified private
  purchase receipt. Paid receipt fills activation code only after server approval.
- Same purchasing identity resumes its existing matching request even after reload;
  changes to an outstanding purchase return409 instead of a second subscription.
- Subscription lifecycle handlers, current paid invoice/price/customer validation,
  durable event deduplication, concurrency protection, and failed/cancelled license
  restriction with recovery. Legacy/manual organizations remain unaffected.
- Separate commerce dependency Dockerfile; new image has NOT been built/scanned.

Validation:
- Initial Python runtime+purchase run:68 discovered,34 passed,34 PostgreSQL skipped,
  zero errors/failures (checkout-runtime.log). This predates the reload safeguard.
- Final targeted purchase/reload/failure-recovery checks:3 passed, no skips/errors
  (checkout-retry.log), after that safeguard.
- Account and checkout Node UI suite:26 passed, no skips/failures. Includes retry
  request identity, rejected redirect, and pending versus verified paid receipt.
- Full integrated Python/Node, exact PostgreSQL, browser visual and real Stripe
  acceptance remain OPEN. Synthetic tests do not establish live payment acceptance.

Resume with Git state and this checkpoint. User reports updating the Stripe tax
classification; not independently read back. Virginia collection approval persists,
but no live configuration change is confirmed. Cloud browser control timed out.
Before activation: inspect existing Secret Manager name wzos-v2-stripe-api-keY;
do not create a duplicate or print the value. Need webhook signing secret and
stable Fernet purchase-encryption secret in Secret Manager. Restricted key now also
requires read-only Subscriptions for lifecycle retrieval, in addition to Checkout
Sessions write and prior catalog/tax reads. Register only the reviewed webhook
events at https://app.workzoneos.org/api/commerce/webhook after the configured
candidate exists. Preserve raw signatures, admin/member and tenant boundaries.

Runtime settings prepared, not applied: WZOS_COMMERCE_ENABLED=1, WZOS_STRIPE_MODE
(test/live matched to a server-owned catalog), WZOS_STRIPE_TAX_VERIFIED=1 only after
live tax acceptance; secret-backed WZOS_STRIPE_API_KEY, WZOS_STRIPE_WEBHOOK_SECRET,
WZOS_PURCHASE_ENCRYPTION_KEY. Catalog file must be packaged. Do not enable live
checkout merely to bypass missing tax/secret/acceptance results. Existing Core
upgrade subscriptions/one-time credit integration remains separate and unfinished.
