# Final checkout release validation - October 16, 2026

## LIVE - completed release

100percent traffic now serves `wzos-v2-accounts-checkout-live-1016` at
https://app.workzoneos.org/. Application source d47033b, immutable image
`sha256:53f9348a618430d823067748ce0958ef084b6d73565780ffcb4a1195dda76a22`.
Full PostgreSQL739 PASS/0 failures/errors/skips; JavaScript123 PASS unchanged;
final buildc10cf15e-5cf7-4625-a40e-9ed5e8b64e55 SUCCESS. Read-only coupon preflight
repair b9f8889 passed3 focused fixtures and actual six-price/coupon/VA readback.
The product-restricted coupon was correct; its applies_to field required expansion.
All six approved V2 prices now explicitly exclude applicable tax, retaining the
same IDs, amounts and intervals. Older products/subscriptions remain unchanged.

Exact-image scan completed: critical0, high5, medium1, low36, minimal25. The five
high findings match the previously reviewed distro issues; every affected package
has fixedVersion.kind=MAXIMUM in this inventory. They remain tracked, not fixed or
suppressed. No new Stripe-package finding was identified. Scan operation
6547f6eb-651c-420f-b0ef-ea836e7d181f; findings under final-image-findings.json.
No temporary IAM grant was needed: existing operator permissions performed scans.

Both hold/live revisions passed preserved-configuration comparison: existing
identity/resources/SQL/ingress and prior secret bindings retained; only approved
scanner and commerce additions. gcloud added the single container display name;
the verifier explicitly checks that harmless normalization. Deployment tooling
4e95e9c records that comparison; no new app rebuild was required for tooling fixes.

Pinned new secret bindings: API3, webhook1, purchase encryption1. API3 is restricted
live and passed actual provider reads. No key value was printed or committed.
Payment mode is live; no real Checkout Session, charge, subscription change or
customer message was created during acceptance. Real end-to-end payment remains
untested. Paid activation/subscription lifecycle are covered by739 automated checks.
Existing-Core upgrade/once-credit eligibility remains unfinished; existing members
cannot accidentally create a second subscription through new-customer checkout.

Live confirmation passed: exact shipped frontend assets, release fingerprint,
protected account/admin/commerce APIs, foreign-origin denial and security headers.
Existing verified admin session selected the organization and opened Guided
Workspace B successfully. Local screenshot live-guided-workspace.jpg is ignored.
Root already-open older clients need a refresh to load the new updater initially.

Rollback target `wzos-v2-accounts-checkout-hold-1016` uses the same accepted image
with new checkout paused, preserving webhook delivery, paid activation, billing
enforcement and file holds. This is a payment/configuration rollback; a shared-code
fault requires fail-closed maintenance and repair, never the older unguarded hub.
Cloud evidence pointer remains $HOME/wzos-final-20261016-path.txt. Retain private
receipts and backup1792177616406. No new testing is running; final work is recording
the release and verifying cleanup of this session's owned SQL proxy.

## Earlier validation history - superseded by completed release above

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

## Checkout pause safeguard

Restricted live server key version3 now verifies. Read-only catalog inspection
reached the provider and blocked on price tax behavior; verify each exact V2 price
before selecting the approved exclusive-tax setup. Do not alter older products.

The release adds WZOS_COMMERCE_CHECKOUT_PAUSED=1 as a runtime pause. It hides new
customer offers and returns503 before creating another session. Existing receipts,
paid activation, webhooks and authoritative subscription access checks stay active.
The focused test verifies pending payment completion, cancellation blocking and
recovery while paused; local17 PASS/17 PostgreSQL skipped. The initial sandbox
attempt failed before application execution because of Windows temporary-directory
permissions; the normal-access focused run passed. Exact new full PostgreSQL/image
gates must pass before deployment. This introduces no schema changes.

Stage the new billing-aware image with checkout paused as the fallback, then the
same accepted image with new checkout enabled as the candidate. This is a safe
payment/configuration rollback, not an independent older-code rollback. For a
shared-code fault, fail closed/maintenance and repair; never serve an older version
that bypasses persisted file holds or subscription access restrictions.

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
