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
   that tax collection is configured. No tax setting is changed in this pass.

Use Stripe-hosted Checkout for new subscription sales and a server-authorized
Customer Portal or reviewed subscription update for existing organizations.
Do not publish generic upgrade Payment Links that can create duplicate subscriptions
or let an unverified buyer select an unrelated organization.
