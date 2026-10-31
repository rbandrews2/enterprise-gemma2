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

## Baseline and latest increment

Owner authorized the recovered source after loss of the original deployment folder.
GitHub rbandrews2/dev main 14e3b1fa27a72e058e2f5cd3b3f757ac772e84b1 was fetched
into an isolated review checkout. All 58 TIME_TRACKER files match the recovered
copy after line-ending normalization. This proves source-copy equivalence, not
identity with the Netlify CLI-built artifact.

The app source and build inputs are now in this directory. The original remains
untouched. Admin checkout includes seat selection, per-user/company retry identity,
and bounded payment-status polling. A return URL never claims payment succeeded.

The server now calls service-only reservation and atomic fulfillment RPCs specified
in billing-schema-proposal.sql. That SQL is a REVIEW PROPOSAL, not an applied or
CLI-generated migration. It includes company serialization, duplicate-event storage,
subscription/session binding, stale-event protection, a same-timestamp conflict
that explicitly requires reconciliation, purchased-seat storage and membership caps.
Checkout expiry releases a pending reservation only after Stripe confirms expiration.
Initial paid activation derives seats from exact Stripe price quantities.

Existing accounts with NULL seat_limit are deliberately preserved pending allowance
reconciliation. They must be reconciled before release; never guess their purchases.

## Required before activation

1. Inspect live schema/grants and customer allowances read-only. Generate the actual
   migration with the Supabase CLI after review. Validate tenant RLS and concurrent
   writes on disposable PostgreSQL. The embedded check uses synthetic schema and
   roles; it is not live Supabase acceptance or a cross-connection race test.
2. Test the exact client in a synthetic browser and verify receipt recovery after
   interruption. Current UI compiles; signed-in browser acceptance remains open.
3. Verify live catalog/account, extra-user price, setup retirement and tax settings.
   Enable neither candidate function nor storefront routing before acceptance.
4. Verify complete Stripe sandbox lifecycle: invoice failures/renewals, disputes,
   refunds, cancellation, duplicate and out-of-order delivery. Refund/dispute policy
   handlers and operator reconciliation for equal-timestamp conflicts or orphaned
   reservations still need implementation. Existing legacy subscription metadata
   must be migrated/reconciled before replacing the production webhook.
5. Deploy reviewed schema before functions and app, then connect the storefront.
   No live enablement is authorized by this document. The Tracker storefront link
   remains unchanged until the complete flow is accepted.

Rollback: disable new checkout, retain paid reports/records and billing event tables.
Do not restore browser billing-write permissions. Preserve transactional fulfillment
while existing payments remain in flight; rolling back blindly to the old webhook
would remove its payment checks. Take a database backup before any approved migration.

No migrations, credentials, live purchases, production deploy or customer sends
were performed. Rollback of this local increment is simply excluding this
directory; it is outside the WZOS application runtime.

## Validation

Run `node --test integrations/time-tracker/tests/checkout.test.mjs` from the
integration checkout. Latest JavaScript run: 23 PASS, zero skips/fails. Embedded PostgreSQL proposal
checks: 17 PASS. Final Vite production build PASS (1740 modules). Results recorded in `docs/STOREFRONT_ACTIVATION_20261031.md`.

References: [Stripe webhook processing](https://docs.stripe.com/events/manage-webhook-endpoints),
[Supabase row security](https://supabase.com/docs/guides/database/postgres/row-level-security).


## Live read-only audit and migration preparation - October 31, 2026

Public app bundle identifies Supabase project ebzfbuqclkumncnugbvq. Authenticated
read-only schema/policy audit confirms the recovered structures. Seven companies
have one member each; one billing row is pending, with zero linked subscriptions.
No customer identities, contact details or credentials were exported.

Live policies confirmed admin billing INSERT and broad table grants. The repair
now revokes ALL client billing privileges, restores authenticated SELECT behind
existing tenant RLS, and adds a restrictive paid-access check for NEW shifts only.
History and shift completion remain available. Production has NOT been changed.

Supabase CLI 2.122.0 generated
supabase/migrations/20261031070800_tracker_checkout_activation.sql locally.
Its body matches the tested proposal except the comment marking migration status.
24 embedded PostgreSQL checks PASS against synthetic roles with live-policy shapes.
Prior unchanged 23 JS checks and final Vite build retained; no redundant reruns.
Cross-connection concurrency and actual deployment validation remain outstanding.

Stripe dashboard confirms Molecular acct_1RVoyBCTCYI3n5kZ: Tracker base $9.99/month,
extra user $4/month, both with zero active subscriptions. Product currently uses
txcd_10000000; no tax configuration was changed. Dashboard also displays an account
information request affecting payouts; owner must review that private task.

Stripe connector still returns reauthentication-required after user's reconnect.
Chrome reconnected as browser 5, but sandbox submenu control/DOM timed out. No
sandbox purchase, API-key creation, live billing mutation or deployment occurred.
Resume sandbox access; do not repeat already passing local gates without changes.


## Stripe test-mode connection and branded checkout repair - October 31, 2026

Connector verified Molecular acct_1RVoyBCTCYI3n5kZ with livemode=false. Existing
shared test-mode catalog had no Tracker prices. Created clearly labeled test-only
product and $9.99 base/$4 extra monthly prices; IDs saved in stripe-test-catalog.json.
No customer information supplied and no payment completed.

Actual Stripe test session cs_test_b18C2l4BSzQBoVeqE7RETtm7dIfJzjPL2WJGHffQRsVYhAV37TIFPiwghd
returned total 1799 cents for 3 seats, status=open/payment_status=unpaid. Session
creation validates Stripe request shape and amount only, not end-to-end activation.
Test session left to expire automatically; connector search did not expose expire.

Stripe returned checkout.superiorllc.org instead of checkout.stripe.com. Repaired
both server and browser URL checks to accept those two exact HTTPS origins with
/c/pay/cs_ paths and no embedded credentials. Other hosts remain rejected.
24 focused JS tests PASS; Vite build PASS (index-waLqWMXD.js,1740 modules).
Unchanged 24 PostgreSQL checks retained. No production deployment or migration.
Next: complete synthetic paid checkout and signed-event delivery into an isolated
candidate, then test cancellation/failure and review remaining release gates.
