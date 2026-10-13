# Purchase, installation and seat licensing — October 12, 2026

## Requested journey and decisions

workzoneos.org → choose edition/seats → Stripe-hosted Checkout → verified payment →
app.workzoneos.org → install web app → create/verify account → redeem activation →
create organization as admin → invite team within capacity. Installation does not
prove payment; a redirect alone never grants access.

Ray confirms every active login consumes a seat, including admins. Inactive
memberships and employee records without a login do not. Invitations do not reserve
seats; capacity is checked atomically at acceptance and reactivation.

Recovered liked proposal from September28 “Audit webhooks and price editions” and
local checkout-audit-20260928/AUDIT_AND_PACKAGES.md:

| | Core | Enterprise |
|---|---|---|
| Setup | $99 | $999 |
| Monthly organization fee | $59 | $249 |
| Included active logins | 15 | 25 |
| Additional active login/month | $3; maximum30 total | $7 |

Original proposal also mentioned2/5 admins,10/100 active jobs,5/50GB storage and
onboarding. Clarify those and metered AI/maps/messaging allowances before publishing.
Connected Stripe test catalog returned no WZOS products. No live prices/credentials
verified and no products, charges, website or public endpoint changed.

## Recovery and schema review

V1 has random/hash activation generators, encrypted delivery and an older offline
signed license containing plan/seats. Reuse concepts; avoid per-installation license
bypass, wildcard CORS and Supabase runtime. V2 uses verified identity/Google storage.

Startup DDL adds activation_entitlements(activation_hash primary key,positive
seat_limit,purchaser_email) and organization_entitlements(organization_id primary
key,activation_hash unique,positive seat_limit). Existing IDs/tables unchanged.
Grant issuance/redemption atomic with existing activation/membership/audit operations.
Joins/reactivations use existing BEGIN IMMEDIATE/PostgreSQL advisory lock.
GET /api/account/license: admin-only, scoped limit/used/available/status. No public
issuance endpoint. Existing pre-seat organizations explicitly legacy_unconfigured;
retain access pending reviewed migration. New CLI activations require --seats.
Paid activations must have buyer email and positive capacity.

Deploying code applies additive DDL: full Python/Node/zero-skip PostgreSQL and
concurrent final-seat tests required. Rollback ignores new tables; retain records.

## Payment and delivery gates

Approved server price mapping; raw signature/mode verification; authoritative
Checkout session/lineitems; only paid fulfillment; atomic session/event deduplication;
encrypted code at rest; verified purchaser-only retrieval. No code in URLs/logs.
Handle pending/delayed payment and recurring renewal/failure/cancellation before
live sales. Secret Manager holds provider/signing/delivery secrets. Installation
uses responsive web-app capabilities; no claim of a native app-store package.

## Candidate assembly and release boundaries

The local code includes two additional sandbox-only purchase ledger tables, whose
exact DDL is in scripts/purchase_seats_schema_review.sql. Accounts initializes only
seat tables; Purchases initializes its two tables only when explicitly constructed.
The default workspace does not mount commerce endpoints or connect Stripe. The
sandbox factory rejects production mode. Raw webhook signatures are checked with
the official SDK; signature failures return invalid-request rather than availability
errors. No live products, charges or subscription lifecycle changes were made.

Install manifest/icons and browser install guidance are included. Android installation
acceptance remains open. The approved full workspace layout retains its dimensions,
icons and colors with slightly translucent module glass and amber pressed shadows.
A native Account disclosure serves phones; desktop account controls align right.

Release requires exact-candidate full Python/Node and zero-skip PostgreSQL checks,
backup/schema compatibility, production auth origin and passkey RP, synthetic-admin
retirement, live budget verification and rollback capture. A public login screen
must not expose private organization data or substitute fixture authentication.
Atlas inference, Twilio acceptance, live purchasing and production routing remain
separate open gates; a Git push does not satisfy them.
