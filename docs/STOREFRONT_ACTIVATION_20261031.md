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
