# Storefront activation integration - October 31, 2026

Status: implemented locally for WZOS Core/Enterprise; not deployed or live-payment validated.

The supplied Desktop storefront used Stripe Payment Links that bypass WZOS
purchase_requests. Its Core/Enterprise buttons now hand off to app.workzoneos.org
with allowlisted offer ID and seat count only. Verified sign-in precedes checkout;
the existing server-owned Checkout Sessions implementation sets exact quantities.
Existing signed webhook fulfillment generates encrypted, email-bound activation
codes only after authoritative paid session/subscription checks. The app prefills
the code, checks pending receipts up to 12 times, and can recover receipts without
a return URL. User still names and explicitly creates their organization.
No activation codes, credentials or payment amounts are trusted from URL inputs.
No email delivery added; codes are delivered inside the verified WZOS account.

Monthly offer IDs remain unchanged. Added core_annual and enterprise_annual using
price IDs from the supplied October 31 storefront catalog. Legacy monthly_cents
and monthly_price_id fields represent recurring-period amounts/IDs for these
annual offers; billing_period explicitly controls display. No schema changes.
Annual upgrade/proration behavior and live catalog/Stripe Tax verification remain
release gates. Existing monthly upgrade behavior is unchanged.

Added GET /api/account/purchases scoped to verified buyer email; it returns only
session IDs/status/edition/seats, never codes. Existing private receipt endpoint
still controls code access. No new public fulfillment endpoint or IAM required.

Validation: 212 Node PASS, zero skips/fails. Targeted initial Python purchase and
commerce run: 36 PASS, 36 PostgreSQL skips. After new annual/recovery tests:
19 commerce PASS, 19 PostgreSQL skips. Required PostgreSQL validation outstanding.
Browser checked Enterprise annual 29 seats: 3024/year + 999 setup = 4023 before tax.
Evidence .local-data/storefront-activation-*.log and storefront-activation-preview.png.
No Stripe charge, customer message, production deployment or account creation.

Stand-alone Time Tracker: user confirmed https://clock.superiorllc.org. Live public
bundle uses /api/create-checkout-session with companyId and Supabase identity.
Recovered source is in root .local-recovery/core-source-dev/TIME_TRACKER (read-only
inspection; not modified). It activates company_billing_2, not WZOS activation_codes.
Recovered checkout expects a setup price and one base line; it does not implement
the new 4-dollar extra-user offer. Reconcile this separate backend and validate
signed webhook lifecycle before changing its routing. Existing storefront Tracker
link retained with explicit non-automated activation notice. No full-WZOS grants.

Desktop files updated in place with originals backed up at
.local-data/storefront-before-activation. Reviewed source copy is in storefront/.
Ship app changes before publishing new storefront; annual options are unavailable
on older app releases. Rollback both together; no schema migration to undo.

## Authenticated Netlify inspection - October 31, 2026

Chrome confirms clock.superiorllc.org belongs to remarkable-muffin-a25dc8,
site 01ac459c-00de-4660-9558-7fd1a45a8724. Published CLI deploy:
69fbb890a565ad9951a85943 (May 6, 2026). Production functions listed:
create-checkout-session and stripe-webhook.

Environment variable NAMES verified, without revealing values:
SITE_URL, STRIPE_MONTHLY_PRICE_ID, STRIPE_PRODUCT_ID, STRIPE_SECRET_KEY,
STRIPE_SETUP_PRICE_ID, STRIPE_WEBHOOK_SECRET, SUPABASE_ANON_KEY,
SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL.
No additional-seat price variable was listed. Presence does not verify values,
Stripe account ownership, webhook delivery, or database permissions.

Recovered source requires a setup charge and fixes both line quantities to one.
This conflicts with the current standalone storefront's no-setup, variable-seat
offer. Deployed function source has not yet been matched to the recovery copy.
Before implementation/deployment, establish the exact deployed source baseline;
then add company-bound checkout selection, validated seat quantities and signed,
idempotent paid-event fulfillment. Keep standalone entitlement separate from WZOS.
No Netlify setting, secret, database, deployment or purchase changed in this review.

## Standalone candidate repairs - October 31, 2026

Prepared integrations/time-tracker separately from the recovered checkout.
Seat-aware authenticated checkout, no setup line, Stripe attempt idempotency,
no pending-status overwrite, paid-session binding and signature replay-window
repairs implemented. Final focused Node run: 17 PASS, zero skips/fails.
External APIs mocked; no PostgreSQL or Stripe sandbox acceptance claimed.

Candidate disabled behind TRACKER_CHECKOUT_V2_ENABLED. Remaining gates include
matching actual deployed source, server-only billing writes, durable transactional
webhook deduplication/concurrency, stored/enforced seat allowances, actual app
handoff and subscription lifecycle acceptance. See integrations/time-tracker/README.md.
User asked for the source folder location while independent local work proceeded.
No live changes, secrets, charges or customer sends. Prior WZOS tests not repeated.


## Source confirmation and candidate expansion - October 31, 2026

Owner authorized recovered source. GitHub main 14e3b1fa27a72e058e2f5cd3b3f757ac772e84b1
TIME_TRACKER compared: 58 files, zero content differences after newline normalization.
Source reviewed in .local-data/tracker-source-review; no remote mutations.

Candidate now includes the app, admin seat selection, stable request identity,
bounded server-status polling and honest payment return messaging. Proposed SQL
adds server-only billing writes, durable reservations, atomic event receipts,
subscription/session binding, stale-event protection and seat cap trigger. Server
functions invoke these RPCs; activation remains disabled until migration acceptance.
SQL is a review proposal, not an applied/generated migration. Existing NULL seat
allowances and legacy subscription metadata require reconciliation before release.

Validation: 23 JS PASS (zero skips/fails), 17 embedded PostgreSQL checks PASS,
final Vite build PASS: 1740 modules, index-DBfO5Mo4.js. External Stripe calls mocked.
Embedded PostgreSQL uses PGlite synthetic fixture, not live RLS/concurrency proof.
No unnecessary WZOS full-suite reruns. No live deployments, changes, charges or sends.
Remaining exact release gates and rollback: integrations/time-tracker/README.md.


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


## Paid Tracker verification - October 31, 2026

Supersedes the earlier unpaid-session checkpoint. One Stripe test-mode card
checkout completed: cs_test_b18C2l4BSzQBoVeqE7RETtm7dIfJzjPL2WJGHffQRsVYhAV37TIFPiwghd,
1799 USD cents, 3 seats (999 base + two 400 extras). Stripe confirmed paid/complete,
subscription sub_1UWWbGCTCYI3n5kZTZMeE6io active. No real charge.

Captured actual test session, subscription and checkout.session.completed event
were replayed through the unchanged candidate webhook and CLI-generated migration
in isolated PGlite PostgreSQL: 17 checks PASS. Covered invalid signature rejection,
active entitlement, exact three-seat allowance, period boundary, fulfilled reservation,
duplicate receipt, paid shift access, fourth-member denial, tenant isolation,
cancellation and subsequent new-shift denial. Replay signatures were locally
constructed with a synthetic secret: NOT proof of Stripe-signed network delivery.

Synthetic subscription canceled without invoice/proration and independently reread
as canceled/livemode=false. Test catalog retained for reuse. No live database,
credentials, production Stripe configuration or deployment changed.

New reproducible harness: integrations/time-tracker/tests/paid-fixture.check.mjs.
Ignored evidence: .local-data/tracker-paid-validation/lifecycle.json and
checkout-return.png. Prior 24 JS, 24 DB and Vite build passes remain valid;
no unchanged suites repeated. Browser return reached the local storefront order
review (temporary test success URL), not an activation receipt. This does not
validate the actual app return flow. The session was created through the connector,
not the candidate checkout endpoint; that endpoint remains mock-tested only.

Remaining release gates: deployed isolated checkout endpoint/app return, actual
Stripe-signed webhook delivery, multi-connection PostgreSQL concurrency, failed-payment
and refund/dispute policy coverage, then reviewed migration/config deployment.
Standalone Tracker activates company billing/seats; Core/Enterprise activation-code
redemption is a separate flow and was not verified by this Tracker test.
