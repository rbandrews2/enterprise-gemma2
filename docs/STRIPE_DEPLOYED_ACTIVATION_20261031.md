# Stripe deployed activation acceptance

## Deployed webhook audit and environment guard - October 31, 2026

Current user objective: verify Stripe-to-deployed-handler activation for Core,
Enterprise and standalone Tracker. NOT complete; local/replayed passes are not
external webhook-delivery evidence.

Fresh Cloud Shell: admin@workzoneos.org, enterprise-gemma2; production traffic100%
wzos-v2-accounts-history-2d77bc6, image100f17c262e3eab4abc3c5b88e9fc9d1bc0a685b8059f4642ed021254656c558.
Commerce enabled, mode live, checkout unpaused, existing secret references intact.
No deployment or IAM changes in this audit. Restricted runtime key correctly
lacks webhook-management read permission (403); do not expand it for the audit.
Stripe live Dashboard supplies endpoint evidence instead:
- Core/Enterprise: we_1URGPxCTCYI3n5kZ0ga45o1D, active,
  https://app.workzoneos.org/api/commerce/webhook; completed, async success/failure,
  subscription created/updated/deleted, invoice paid/payment_failed.
- Tracker: we_1TTxS2CTCYI3n5kZ2dzPIyDI, active,
  https://clock.superiorllc.org/api/stripe-webhook; completed and subscription
  created/updated/deleted ONLY. Missing async_payment_succeeded and expired
  reservation coverage required by the candidate. Add after candidate deployment
  and exact handler/config verification, not against the older unsafe handler.
- Both dashboards show 0 deliveries this week; 0% errors is not acceptance.
- Unsigned empty POST to each public URL returns400, not a static page/redirect.

Connected Molecular Stripe TEST mode has zero webhook endpoints. Secret Manager
contains only existing live API/webhook secret names, no test API secret.
User asked to save a restricted TEST key (Checkout Sessions Write, Subscriptions
Read, Prices Read) as wzos-stripe-test-api-key in enterprise-gemma2. Do not request
or print its value. Browser credential creation/entry is user-operated.

Candidate repair: explicit STRIPE_MODE=test|live, API-key prefix/mode agreement,
and matching livemode on event plus re-fetched session/subscription. Misconfigured
checkout fails before downstream calls; wrong-mode events cannot reach billing.
28 focused JS checks PASS,17 captured-payment PostgreSQL replay checks PASS.
These reruns were justified by changed mode validation; no unrelated suite rerun.
No schema change in this repair. New required deployment variable STRIPE_MODE.

Acceptance sequence (do not use production records for synthetic tests):
1. Provision/configure isolated deployed candidate(s) with test-only credentials,
   persistent isolated database/schema, explicit offer catalog and authenticated
   checkout. Existing production DB or service identity assignment needs a concrete
   scope review; no new workload or access is provisioned by this note.
2. Register Stripe test destinations for those exact deployed URLs and bind each
   corresponding signing secret. Keep signature/mode/tenant checks enabled.
3. One paid Checkout per Core, Enterprise and Tracker through the candidate's own
   checkout endpoint. Record Stripe event ID, destination HTTP delivery, and DB
   fulfillment. Core/Enterprise: buyer-only recoverable code, correct edition/seats,
   successful organization redemption; Tracker: correct company/seats/paid access.
4. Redeliver the same event; assert one activation. Verify delayed-payment success
   and cancellation. Cancel owned synthetic subscriptions. Never fabricate paid
   events or count a local signature replay as external delivery.
5. Only after gates: reviewed migration and candidate deployment, live price/secret
   binding verification, updated storefront handoff and correct live event lists.
   Test-mode success alone does not prove a live payment; no real charges authorized.

## Test API credential verified - October 31, 2026

wzos-stripe-test-api-key version2 is a restricted TEST key. Read-only calls to
known test checkout/session, subscription and price objects all returned test-mode
records. An intentionally incomplete Checkout POST returned400 parameter_missing
success_url, not an authentication/permission error; it created no session.
Version1 was a LIVE key and was not used for test API calls. Pin version2 for
staging; do not bind latest or the prior live version. No key values logged/saved.

Credential blocker cleared. Deployed isolated receiver/database configuration,
test webhook registration/signing-secret binding and actual external delivery
for Core/Enterprise/Tracker remain outstanding. No deployment, real charge,
subscription creation, IAM or production database change in this credential check.
