# Stripe deployed activation acceptance

## Core and Enterprise deployed activation accepted - October 31, 2026

Repaired image sha256:26b1a23215f519be1177b575834b9186958c8f56ba71c4307e4e5c60b62f3574
ran as control revision00003-fbc and webhook revision00003-d7l.
Stripe resent the existing paid TEST events; no new payment was made.
Enterprise evt_1UWYCvCTCYI3n5kZPZLEVTAB: HTTP200, fulfilled=true,
activation_issued=true at09:12:59UTC. Core evt_1UWYCBCTCYI3n5kZ2mKHcCPR:
HTTP200, fulfilled=true, activation_issued=true at09:13:43UTC.
Core duplicate redelivery09:14:09UTC: HTTP200, duplicate=true, fulfilled=true.

Deployed authenticated checks PASS for both buyers: fulfilled receipt, wrong-buyer
receipt404, wrong-buyer redemption403, successful organization creation, correct
Core15/Enterprise25 seat limit, one seat used, repeat redemption same organization.
No activation code or credential printed. Cloud evidence: activation-results.json
under /tmp/wzos-checkout-gate.EEy9A26Q; screenshot checkout-stripe-delivery-20261031.png.
Earlier83 checks and repair78 PostgreSQL checks remain passing; no unchanged suite
rerun. Both owned synthetic subscriptions canceled (livemode=false). Disposable
Stripe webhook deleted and dashboard confirms no remaining destination in this list.
Cloud cleanup PASS: both temporary services absent; project Cloud SQL grant and all four secret grants removed and independently read back. Test database/secrets retained; production untouched.

Production has NOT received this invoice compatibility repair yet. Time Tracker
external acceptance remains deferred. Annual/additional-seat payment variants are
not claimed by these two monthly base-seat acceptance runs. Retain the test database
and test secrets as evidence; database deletion was not authorized.

## Paid test checkout exposed invoice compatibility issue - October 31, 2026

Both real Stripe SANDBOX Checkout submissions completed paid through deployed
control service: Core15800cents/15 seats and Enterprise124800cents/25 seats.
Core session cs_test_b1ll13vZxrTXLD0isdY2c0N7WdZwZ22p1wOduYGZeWcFcANJdOUG5P0KoF;
subscription sub_1UWYC9CTCYI3n5kZLz0jSGFz; event evt_1UWYCBCTCYI3n5kZ2mKHcCPR.
Enterprise session cs_test_b1OKqPEJBVDZppdq3cmDT0A9j9hDNSKCTvaYRwf9Fc4NgkDVHNVnsqTHYq;
subscription sub_1UWYCtCTCYI3n5kZvb0sHYFV; event evt_1UWYCvCTCYI3n5kZPZLEVTAB.
No real charges. Both receipts currently PENDING; do not call activation accepted.
Actual webhook deliveries reached receiver but checkout events returned400.
Read-only provider diagnosis: active subscriptions, invoice status paid, legacy
paid boolean absent. Code incorrectly required that retired field.
Repair d1ba27f uses invoice status with legacy contradictory values denied;
shared helper applied to initial activation and upgrade checks. Fixtures now
match current Stripe invoice shape. Local78 run:40pass/38PGskips; cloud78PASS,
zero skips,41.631s, invoice-repair.exit0. Earlier83gate retained, not replayed.
Repaired acceptance image building; no production deployment. Stripe dashboard
requires sign-in for event Resend; user asked. Reuse these payments, no new charge.

Receiver public setting uses no-invoker-iam-check after domain policy rejected
allUsers binding. This is Google's documented public-service method. Public
account route404, unsigned webhook400; private control anonymous403 and authorized
catalog200. Both services running candidate5805cfa until repair build completes.
Keep temporary acceptance environment until resend/receipt/redemption evidence is
complete, then cancel the two synthetic subscriptions and clean up test workloads.

## Checkout database provisioned and receiver preparation - October 31, 2026

Reconnected in-app Cloud Shell and freshly verified admin@workzoneos.org,
enterprise-gemma2, clean tracked cloud checkout and proxy5546. Approved setup
script c39d076 completed: RESTRICTED_TEST_DATABASE_LOGIN_READY and
TEMPORARY_SQL_ADMIN_REMOVED. Independent SQL user list confirms only postgres,
wzos_app and wzos_checkout_test; no temporary administrator remains.
New database-url secret version1 granted only to acceptance runtime.
Private bootstrap control revision00001-fst rejects anonymous access403 and its
service IAM policy has no public binding. Private receiver revision00001-qh7
also prepared. Both min0/max1,1CPU/512MiB. No production changes.
Created Stripe TEST endpoint we_1UWY8BCTCYI3n5kZXXeTZT6X with eight scoped events.
Signing secret transferred encrypted into acceptance-webhook-secret:1, with
one-time transfer key removed; runtime access is secret-scoped. No secret values
printed or committed. Candidate5805cfa deployment to both private services is in
progress. Actual payment, external delivery, redemption and cleanup remain open.

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

## Checkout acceptance preparation - October 31, 2026

Candidate fefb926 pushed to codex/preproduction-modules. Test catalog created for
Core/Enterprise in Molecular Stripe TEST mode; no payments created. Test catalog
and return-origin isolation repairs plus separate private-control/public-webhook
acceptance factory prepared. No production deployment or data changes.

Cloud checkout /tmp/wzos-checkout-gate.EEy9A26Q/repo ran 83 focused checks PASS
with no skips (commerce runtime, purchase onboarding, staging config and surface),
including disposable native PostgreSQL cases. Log: ../postgres.log; exit: ../gate.exit.
Local new checks: 4 config + 3 surface PASS; Tracker26 checkout/config PASS.
Do not repeat these unchanged tests. Actual Stripe network delivery remains open.

Pending user answers: approve WZOS isolated receiver/database/runtime scope in
docs/CHECKOUT_ACCEPTANCE_SCOPE_20261031.md; select separate Tracker test project
or investigate Supabase plan upgrade. Branch creation was refused because the
current plan lacks branching; no branch or paid plan created. Do not use customer
records for synthetic checkout acceptance. Test API secret remains pinned version2.

## Approved checkout environment preparation - October 31, 2026

User approved isolated WZOS deployment; then prioritized Core and Enterprise
before Time Tracker. No Supabase project or plan change should proceed now.

Created wzos_checkout_acceptance database on existing wzos-v2-staging-db and
wzos-checkout-acceptance service account. Runtime has conditional Cloud SQL
Client limited to that instance, and secretAccessor only on the two new secrets:
wzos-checkout-acceptance-stripe-key (copy of verified test version2) and
wzos-checkout-acceptance-encryption-key. The original key secret contains a live
version1, so it was deliberately NOT granted to the test runtime.

Build8d4a0cd3-6688-4d4c-b1dd-01a9f4075e85 SUCCESS; image digest
5805cfa34b8c83e4130ab6e5587fef04b0534e28f1aecfba8c528c3f9845a795.
No Cloud Run acceptance services or test Stripe endpoint created yet.

Existing wzos_app SQL login lacks CREATEDB and CREATEROLE. User does not know
postgres password. Prepared scripts/provision_checkout_test_database.py to use
a temporary expiring SQL administrator, create restricted runtime login and
acceptance DSN secret, then remove/verify temporary user. This broader setup
access awaits a specific approval; do not run yet. Scope documented in
CHECKOUT_ACCEPTANCE_SCOPE_20261031.md. Test DB owner is cloudsqlsuperuser.
Cloud Shell terminal1 proxy PID7364, localhost5546; log/pid files under
/tmp/wzos-checkout-gate.EEy9A26Q. Terminal0 is the successful build shell.
