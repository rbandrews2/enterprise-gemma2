# V2 pricing activation - October 16, 2026

Ray approved the V2 model and proceeding with additive live Stripe catalog setup.
Account: Molecular Project Development, LLC, acct_1RVoyBCTCYI3n5kZ. The connected
Stripe tool exposes test mode only; authenticated Chrome exposes the live catalog.
Do not mistake either catalog for the other or change the connector's mode silently.

| USD | Core | Enterprise |
|---|---:|---:|
| One-time setup | 99 | 999 |
| Monthly organization fee | 59 | 249 |
| Included active logins | 15 | 25 |
| Monthly additional active login | 3 | 7 |
| Total capacity | 30 | No commercial maximum agreed |

All active logins count, including admins. Employee records without login access
do not count. Additional billed quantity is max(0, purchased seats - included seats).
The existing licensing path requires a positive purchased seat limit; Enterprise
has no agreed commercial ceiling, which is not permission for unlimited unbilled
logins. Capacity and subscription quantities must remain synchronized server-side.

Established Core customers get a one-time USD20 Enterprise upgrade credit, never
a recurring monthly discount. Eligibility must be verified by the backend against
the organization and existing payment/subscription history. The offer appears only
to Core admins; members receive no upgrade nudge or purchase action.

## Catalog setup

Separate WZOS V2 Core and WZOS V2 Enterprise products preserve the older product
and price records. No existing customer, subscription, invoice, payment link or
payment method is changed by this setup. No charge or customer message is sent.
The new monthly price is each product's default; setup and additional-seat prices
are explicit separate components of the same edition, not alternative editions.

- Core product: prod_VS8NPXcRzhnRq4.
- Core monthly: price_1URE6GCTCYI3n5kZNnpAVdVw.
- Core setup: price_1UREAZCTCYI3n5kZMp4p4xKi.
- Core additional login monthly: price_1UREB9CTCYI3n5kZXZ9HwzUj.
- Enterprise product: prod_VS8NpLjO1KtlTl.
- Enterprise monthly: price_1URE6yCTCYI3n5kZrHaJaAv8.
- Enterprise setup: price_1URE86CTCYI3n5kZghQ7IOIU.
- Enterprise additional login monthly: price_1URE8gCTCYI3n5kZQIvNi5fb.
- Upgrade coupon: wzos_v2_core_upgrade_20_once_20261016, USD20 off once,
  restricted to prod_VS8NpLjO1KtlTl, no public promotion code. Catalog coupon
  creation does not itself enforce prior Core membership or per-organization
  lifetime usage; those are required runtime checks, not accepted functionality.

All six prices were created and read back in the live dashboard. Both V2 products
show three prices. The two monthly base prices remain their products' defaults.
The catalog mapping is saved in knowledge/billing/v2-stripe-catalog.json; it is
reference configuration and does not mount or enable live billing endpoints.

Validation: three local price-contract tests PASS (included versus additional
seats, Core capacity bounds, distinct price IDs, once-only credit configuration
and disabled checkout). These are contract checks, not live payment acceptance.
Read-only Secret Manager inventory in enterprise-gemma2 returned no secret names
matching stripe/billing/checkout. Credentials may exist under unrelated names;
none were read, printed, created or bound. Secure runtime credentials and a
verified webhook destination remain required before accepting money.

## Runtime release gates

Catalog preparation alone does not enable checkout. The existing purchases.py
factory explicitly rejects production commerce. Before a live purchase button:

1. Bind restricted Stripe credentials and webhook signing secret using Secret
   Manager; never copy browser/dashboard credentials into Git or the frontend.
2. Verify raw webhook signatures, expected live account/mode, authoritative line
   items/amounts and payment status; use durable idempotency for events and sessions.
3. Handle invoice paid/failed, subscription updated/deleted and delayed Checkout
   payments. Never grant an edition based on a redirect or supplied metadata alone.
4. Create/update exactly one organization subscription. Upgrades must not duplicate
   an existing Core subscription; preserve the old plan until the reviewed change
   succeeds. Apply the one-time credit only once to an eligible organization.
5. Test billing, verified activation delivery, seat limits, concurrent invitations,
   admin/member and tenant boundaries in the test environment before live sales.
6. Review Stripe Tax registrations and applicable obligations before enabling
   automatic tax. A product category or dashboard tax preview is not evidence
   that tax collection is configured. No live tax setting is changed in this pass.

Use Stripe-hosted Checkout for new subscription sales and a server-authorized
Customer Portal or reviewed subscription update for existing organizations.
Do not publish generic upgrade Payment Links that can create duplicate subscriptions
or let an unverified buyer select an unrelated organization.

## Confirmed tax decision and secure connection preparation

Ray confirmed Cloud SaaS - business use (`txcd_10103001`) on October16. Apply it
only to the two new V2 products above. This decision is recorded in the reference
catalog; browser timeouts prevented applying/readback in live Stripe. A live
Dashboard read showed zero collecting locations, with only North Carolina and
global unattributed revenue listed as not collecting. Virginia was absent. Ray
then approved adding the existing Virginia registration for immediate collection,
without filing services; this approval is saved but not yet executed because the
browser disconnected again. A controlled tax calculation remains unverified. Do not infer
a tax rate or taxable treatment from this classification alone. Source:
https://docs.stripe.com/tax/tax-codes

Checkout fulfillment now validates pre-tax subtotal separately from the completed
automatic-tax amount and total, including legitimate zero-tax outcomes. Pending
tax calculations, altered subtotals/totals, unapproved discounts or shipping are
rejected. This is new-purchase validation, not an implemented upgrade workflow.
The production-commerce refusal remains in place; no new schema or mounted route.

The SDK adapter requires a restricted key matching test/live mode and a webhook
signing secret, uses a bounded 15-second request timeout with no automatic retries,
and preserves server-owned URLs, prices and request idempotency. Automatic tax
is opt-in only after configuration review. Real SDK signature tests reject forged,
expired and altered-body events. No real API call or customer charge is involved
in these local checks.

`scripts/check_stripe_configuration.py` is a read-only preflight for the six prices,
product classification, exclusive-tax behavior, once-only Enterprise coupon and
active Virginia registration. It explicitly reports tax calculation untested and
checkout disabled. Run with the commerce dependencies and a restricted key injected
into the process environment by Secret Manager (never paste values into a command):

```text
python scripts/check_stripe_configuration.py --live --approved-tax-code txcd_10103001
```

For this implemented adapter/preflight, prepare restricted permissions for Checkout
Sessions write (includes retrieval), and read-only Products, Prices, Coupons and
Tax Registrations. Everything else remains ungranted until its code needs review.
Exact Dashboard permission labels must be verified there. This is not yet the
complete production subscription-lifecycle permission set. Use separate test/live
keys, user-entered directly into Secret Manager as `wzos-v2-stripe-api-key`; the
endpoint's signing secret belongs in `wzos-v2-stripe-webhook-secret`. No key was
created, read, granted to a runtime or saved to Git in this pass. Registering the
production webhook must wait for the subscription-lifecycle handlers and gates;
do not point live billing at the current sandbox-only handler.

Explicit SDK gate (requires `requirements-commerce.txt`):
`python -m unittest discover -s commerce_tests` -- six checks PASS. Purchase gate:
`python -m unittest discover -s tests -p test_purchase_onboarding.py` --19 PASS.
These results do not substitute for current-candidate PostgreSQL, real tax,
subscription-lifecycle or deployed browser acceptance.

Final combined focused run:47 discovered,28 passed,19 PostgreSQL cases skipped
because no disposable database was configured; no failures/errors. This includes
purchase19, catalog3, SDK/preflight6. Full local discovery remains unaccepted:
sandbox temporary-directory access failed, and the normal-access retry stalled
and was stopped. No test process is intentionally left running. Browser inventory
also showed a Secret Manager page named `wzos-v2-stripe-api-keY` (capital Y); inspect
metadata before selecting the eventual binding rather than creating a duplicate.
No secret value or permissions were inspected through that page.
