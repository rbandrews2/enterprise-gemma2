# Core upgrade: restricted Stripe access review

Molecular live account acct_1RVoyBCTCYI3n5kZ. Existing restricted key named
WZOS V2 server checkout, stored in Secret Manager for the existing WZOS runtime.
Read-only Dashboard inspection confirmed Subscriptions=Read and Invoices=Read.
No credential was revealed, copied, rotated, or entered by the agent.

Proposed exact change: Subscriptions Read -> Write; Invoices Read -> Write.
All other resource permissions, secret versions and Google IAM stay unchanged.
Stripe documents GET as read and POST/DELETE as write in restricted-key guidance:
https://docs.stripe.com/keys/restricted-api-keys

Needed routes: POST /v1/invoices/create_preview (non-persisted estimate), and
POST /v1/subscriptions/{id} (existing paid Core subscription upgrade only after
explicit organization-admin consent). No second subscription is created.

Risk: Stripe resource permissions are account-wide, not scoped to WZOS organization
IDs. This key could modify other subscriptions/invoices in this Stripe account if
misused. WZOS constrains access to verified purchase mappings, admin role, matching
organization/customer/subscription, server-owned prices, one idempotency key and
paid signed-webhook fulfillment. No payout, refund, bank, card or other new scope.
Existing Stripe Tax configuration is retained; no registration/classification change.

Approval required before saving these expanded permissions. Agent acceptance will
not charge or modify a real subscription. Any actual paid acceptance is a user action.
Upgrade activation stays off until permission/provider and release gates are resolved.

Rollback: pause new upgrades using WZOS_CORE_UPGRADES_ENABLED=0 (preserve signed
webhook reconciliation), then restore these two permissions to Read only after
reviewing pending upgrades so already-paid fulfillment is not broken. Keep database
upgrade records, original receipts and provider invoice references; do not drop DDL.
