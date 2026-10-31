# Standalone Time Tracker checkout candidate

Local, incomplete integration candidate. Do not deploy or set
`TRACKER_CHECKOUT_V2_ENABLED=true` until the release gates below pass.
This is not the deployed WZOS Time Tracker module.

Baseline: read-only copy of the two Netlify functions in
`.local-recovery/core-source-dev/TIME_TRACKER`. Netlify confirms functions with
these names and routes exist, but does not expose their source in the inspected
UI. The recovered code has NOT been proven identical to the published CLI deploy
`69fbb890a565ad9951a85943`. Original checkout was not modified.

## Implemented locally

- Require authenticated company owner/admin, valid company/request UUID and
  integer seats 1–30. Keep role lookup in the standalone membership table.
- One base monthly price plus seats minus one additional-user quantities. No
  setup charge. Require `STRIPE_EXTRA_USER_PRICE_ID`; never trust client prices.
- Require a client-generated request UUID; Stripe idempotency keys include
  company/user/request. Reuse it for retries of the same attempt; generate a new
  one only when the customer explicitly changes the selection or begins again.
- Reject a second initial checkout for a company with an existing subscription.
  Do not reset billing to pending when opening checkout.
- Payment verification checks current session/payment/subscription/company/
  customer/product. No default-to-active path. Handle async success.
- Signature check accepts rotated v1 signatures and rejects timestamps outside
  five minutes, ambiguous timestamps, malformed hashes and altered bodies.
- Subscription events reread current state and can update only a previously
  linked subscription. Unknown states fail closed to inactive.
- Ten-second upstream request bounds; safe checkout error text; no-store receipts.

## Required before activation

1. Locate the source for the published CLI deployment; compare and reconcile
   this patch in a separate owned checkout. Confirm exact live catalog/account,
   setup retirement, extra-user price and tax settings without exposing secrets.
2. Read-only database inspection: check current grants/policies. Recovery SQL
   grants authenticated admins INSERT on billing with no status restriction.
   Prepare a CLI-generated migration to revoke client billing writes, retain
   tenant-scoped reads, and make webhook writes server-only. Do not blindly
   apply recovery SQL to the current database.
3. Add durable checkout reservations, unique session/subscription linkage,
   transactional event deduplication, concurrency and ordering protection.
   The current candidate has Stripe request idempotency but NOT complete
   database webhook idempotency or checkout-reservation concurrency control.
4. Persist purchased seat allowance and enforce it in membership creation/join
   server-side. Metadata alone does not enforce purchased seats. Review existing
   customer allowances and lifecycle transitions before migrating anything.
5. Wire seat selection/requestId through the actual app, preserving them across
   sign-in. Display payment pending/success/failure from authoritative billing;
   never grant access based on a URL. Connect storefront only after acceptance.
   Existing storefront Tracker link remains unchanged meanwhile.
6. Verify invoice failures/renewals, refunds/disputes, cancellation and recoveries
   against the documented access policy. Add required event handling.
7. Run PostgreSQL authorization/atomicity checks plus a Stripe sandbox lifecycle
   including duplicate/out-of-order events and an interrupted return page.
   Current unit checks mock external services and cannot satisfy this gate.

No migrations, credentials, live purchases, production deploy or customer sends
were performed. Rollback of this local increment is simply excluding this
directory; it is outside the WZOS application runtime.

## Validation

Run `node --test integrations/time-tracker/tests/checkout.test.mjs` from the
integration checkout. Initial run: 17 PASS, zero skips/fails. Results for the
final candidate are recorded in `docs/STOREFRONT_ACTIVATION_20261031.md`.

References: [Stripe webhook processing](https://docs.stripe.com/events/manage-webhook-endpoints),
[Supabase row security](https://supabase.com/docs/guides/database/postgres/row-level-security).
