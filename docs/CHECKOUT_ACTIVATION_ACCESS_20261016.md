# Proposed checkout credential and webhook activation

Account: Molecular Project Development LLC, Stripe acct_1RVoyBCTCYI3n5kZ.
Destination: WZOS V2 checkout billing,
https://app.workzoneos.org/api/commerce/webhook. Your-account snapshot events,
existing account webhook version2025-05-28.basil (no account API upgrade).
Exact eight events:
checkout.session.completed, checkout.session.async_payment_succeeded,
checkout.session.async_payment_failed, customer.subscription.created,
customer.subscription.updated, customer.subscription.deleted, invoice.paid,
invoice.payment_failed. Matching events from this Stripe account can include
other products; WZOS ignores unbound subscriptions/purchases and cannot grant
access from their metadata. Existing webhook destinations remain unchanged.

Proposed secret-scoped roles/secretmanager.secretAccessor for only
wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com in enterprise-gemma2:
- Existing wzos-v2-stripe-api-keY (preserve case, verify enabled version metadata).
- New wzos-v2-stripe-webhook-secret: user enters Stripe signing secret directly.
- New wzos-v2-purchase-encryption-key: generate stable Fernet key server-side,
  transfer directly to Secret Manager without printing or putting in Git.

No project-wide secret role, key export to browser, customer charge or customer
communication. IAM grants and event destination require action-time approval under
browser-control policy. Approval is not recorded by this document alone.

After acceptance, runtime receives pinned enabled secret versions through Cloud
Run Secret Manager bindings. No live checkout until dependencies, complete tests,
registration/classification/price reads and webhook acceptance are verified.
Rollback: disable commerce and return traffic to the reviewed security-capable
fallback; retain billing/activation history and encrypted receipts. Remove only
these exact secret bindings/grants if activation is abandoned, and disable the
new webhook destination. Never disable older destinations or delete customer data.
