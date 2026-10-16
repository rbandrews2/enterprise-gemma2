# Final checkout release validation - October 16, 2026

## Verified in this release session

- Application/test source: `638d467`. Packaging repair: `39b3fcb`.
  No services, shared, tests or commerce_tests changes between those commits.
- Disposable native PostgreSQL gate: 737 tests, failures0, errors0, skipped0;
  294.954 seconds. JavaScript gate: 123 PASS, no failures/skips.
- Official Stripe SDK and read-only configuration fixture gates: 6 PASS.
  These fixtures do not establish live payment acceptance.
- Actual Cloud SQL schema: zero conflicts. Missing additive tables reviewed:
  security_incidents, security_actions, security_file_states, security_alert_reads,
  purchase_events, purchase_requests, purchase_subscriptions. Deployment applies
  startup DDL; no destructive migration is authorized or needed.
- Fresh Cloud SQL backup1792177616406: SUCCESSFUL,
  description `pre-final-checkout-20261016`.
- Private files bucket: public-access prevention enforced, uniform bucket access
  enabled; no allUsers/allAuthenticatedUsers IAM member.
- Private scanner remains nonpublic; WZOS application identity has service-scoped
  invocation. No new scanner IAM permission was created in this session.
- Security/file/storage/shared implementation unchanged from the earlier scoped
  persistence acceptance9a74d19. Earlier managed-persistence29 and metadata/private
  scanner29 remain historical scoped evidence, not a new deployed-browser result.

Cloud evidence pointer: `$HOME/wzos-final-20261016-path.txt`.
Local private evidence: `.local-data/release-20261016/`.

## Authorized Stripe configuration applied

Molecular account `acct_1RVoyBCTCYI3n5kZ`; existing destinations unchanged.
New webhook `we_1URGPxCTCYI3n5kZ0ga45o1D`, WZOS V2 checkout billing,
https://app.workzoneos.org/api/commerce/webhook; eight events exactly as approved
in CHECKOUT_ACTIVATION_ACCESS_20261016.md. Account-default snapshot API
2025-05-28.basil retained; no account-wide API version upgrade. Application uses
the separately pinned SDK API2026-08-26.dahlia and retrieves authoritative objects.

Virginia existing-registration collection is active, registration
`taxreg_1URGYgCTCYI3n5kZhcald5cC`; no filing service enrolled. This verifies collection
configuration, not a legal taxability conclusion or per-product tax calculation.

User saved webhook signing secret as version1. Stable encryption secret generated
directly into Secret Manager without displaying its value. Only the existing WZOS
runtime received approved secret-scoped reader access to the exact three names in
the access document. No secret value is stored in this repository or screenshots.

## Credential handoff blocking checkout activation

Existing `wzos-v2-stripe-api-keY:1` is a publishable live browser key, not a server
API key. Read-only preflight correctly rejected it. It must not be bound as the
checkout server credential. A custom restricted live-key form is prepared for user
creation and entry as a new version of that same secret (case preserved).
Prepared permissions: Products, Prices, Coupons, Invoices, Subscriptions and Tax
Settings/Registrations Read; Checkout Sessions Write; other permissions None.
User must create/copy/enter the credential directly, never in chat.

After entry, verify enabled version metadata, repeat bounded read-only catalog
preflight for six exact prices, coupon restriction, txcd_10103001 and active VA
registration. Do not set WZOS_STRIPE_TAX_VERIFIED until its actual checks pass.
No charges, Checkout Sessions, customer messages or subscription changes occurred.

## Build and remaining release gates

Code-only build3039d7e7-a971-411c-8163-05c137e2fe06 succeeded, image
`sha256:a72d0bf7b606a47a82d52e2586f0e993dee6c8e0ea9f31ecf15b0443ce88a826`.
It does not contain the Stripe SDK/catalog and cannot enable commerce.

First billing build4c3cbc48-264c-46f1-a25f-e0f40a047721 built the image but failed
its isolated test because its non-root user could not read a private synthetic
test fixture. No application test ran in that failed step. Packaging39b3fcb makes
only that synthetic test file readable; runtime permission settings are unchanged.
Repaired buildfb9a3478-3185-4446-a9fa-96b99c1fce25 SUCCESS, including isolated
official SDK tests. Submitted from a fresh9.4MiB git archive without the generated
test virtualenv. Immutable image:
`us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:254b7fef478cabf57a65237a5fa520e5276c6bd47b04b3a1d566b1717f8ab742`.

User saved API secret version2; type-only verification found a webhook signing
secret there, not a restricted API key. No value was displayed. Corrective user
handoff is pending: Stripe's "Your new API key" window contains the API credential;
save it as another version of the API secret, leaving webhook secret unchanged.

Before traffic: successful immutable billing image and dependency review; credential
preflight; preserved auth/ingress/runtime/secret configuration comparison; candidate
and security/billing-capable rollback staged without traffic; actual public and
signed-in browser validation. Never roll back to a version bypassing persisted
file holds or paid-subscription access checks. Retain database/activation history.

Live remains wzos-v2-accounts-hub-5a3ac86 at100percent; no application deployment
or traffic change has occurred in this session. Atlas model inference remains
disabled and is not accepted by these checkout/security checks. Existing-Core
subscription upgrade and once-credit eligibility remain separate unfinished work;
the new-customer checkout deliberately rejects existing organization members.
