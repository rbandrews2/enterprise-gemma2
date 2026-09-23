# Accounts and storage: replacing Supabase

Ray requested this work on 2026-09-23 ahead of further module expansion. Supabase
is not part of the new runtime. Existing Supabase data has NOT been recovered or
migrated; keep those exports/recovery requests separate from building the replacement.

## Historical evidence and role contract

Recovered Core `src/contexts/AuthContext.tsx` loads `organization_members` and
recognizes owner/admin. `pages/organization/Index.tsx` displays Owner, Admin,
Member and creates organizations with purchased activation codes.
`components/auth/AuthLandingCard.tsx` uses email/password sign-up/sign-in.
An older `lib/auth/AdminGuard.tsx` instead depends on `org_creator`. We preserve
the organization model and remove this conflicting browser-only authorization.
These originals remain in ignored `.local-recovery/core-build-baseline`.

| Capability | Member | Admin | Owner |
|---|---|---|---|
| Own clock, forms, orders, study status | Yes | Yes | Yes |
| Organization forms/orders and team attendance | No | Yes | Yes |
| Read team schedule | Yes | Yes | Yes |
| Edit schedule/assign members | No | Yes | Yes |
| Read private messages | Participant only | Participant only | Participant only |
| Invite members | No | Yes | Yes |
| Invite admins/change roles/disable membership | No | No | Yes |
| Remove last active owner | No | No | No |
| Access another organization | No | No | No |

Owner is an organization role, not unrestricted WZOS platform administration.
Core/Enterprise is a separate server-owned entitlement. New sign-ups get no
membership automatically. Organization creation consumes a random, hashed,
expiring operator-issued activation code. Invitations bind to verified email;
subsequent access is by verified UID, never email matching. Role changes are audited.
Suspended memberships are checked on every API request. An already-authorized
in-flight request may finish; this is not a retroactive transaction cancellation.

## Storage decision

- Cloud SQL PostgreSQL: all workspace records, clock events/idempotency receipts,
  forms and revision history, schedules, report snapshots, personal study states,
  internal messages, accounts, memberships, invitations and attachment metadata.
- Private Cloud Storage: original PDF/PNG/JPEG attachments, linked to authorized
  orders/forms. Bucket must enforce uniform access and public-access prevention.
  Originals are immutable, bounded to 10 MiB and SHA-256 checked. No public URLs.
- Google Firebase Authentication: account creation, password reset, verified
  email sign-in, Admin SDK token validation with revocation checks. No passwords
  stored in WZOS. Browser tokens stay in memory, not localStorage.
- Cloud Run FastAPI: replaces application edge functions. Existing source index
  remains a separate rebuildable local cache; durable agency-source archival and
  cloud index rebuild still need deployment wiring.
- Secret Manager: intended database credential and future Twilio secrets.

PostgreSQL keeps existing SQL workflows and transaction guarantees. A global
transaction advisory lock initially preserves SQLite's serialized writes for
multi-instance safety; this favors correctness at small scale. Replace with
tested organization/record locks before high throughput. No SQLite database may
be mounted on a Cloud Storage filesystem or used as durable Cloud Run state.

## Runtime and testing

The new `account_app:application` factory is separate from synthetic staging.
Hosted accounts refuse missing PostgreSQL/private cloud file storage and any
Cloud Run service other than `wzos-v2-accounts`. It never seeds synthetic records.
Install `requirements-accounts.txt`; build with `Dockerfile.accounts`.
Environment: `WZOS_ACCOUNT_WORKSPACE=1`, `WZOS_AUTH_PROJECT`,
`WZOS_AUTH_WEB_API_KEY` (public, restricted Auth API key), `WZOS_DATABASE_URL`
(secret), `WZOS_FILES_BUCKET`, and exact `WZOS_ACCOUNT_ORIGINS` if behind a proxy.
Existing restricted staging is unchanged.

`scripts/test_postgres_accounts.sh` uses an isolated disposable Docker PostgreSQL
container and synthetic records only, with per-test schemas. It removes its own
container on exit. `scripts/issue_workspace_activation.py` is operator-only and
writes activation material to an exclusive output file; do not commit that file.

Backend file APIs: PUT `/api/files/{uuid}` with raw binary and entity_kind,
entity_id, filename query fields; GET `/api/files` for scoped metadata; GET
`/api/files/{uuid}` for an authorized attachment download. A magic-byte check
is not malware scanning. Scanner/quarantine and UI attachment controls remain
required before accepting customer uploads. Failed DB commits can leave orphan
objects; same-ID retries recover them, and reconciliation is still needed.

## Twilio

Ray has a Twilio account. Planned delivery is SMS/report links through Twilio,
and email through a verified email provider (Twilio SendGrid if available in his
account). An SMS account does not prove SendGrid/domain configuration exists.
No Twilio credentials were accessed and no external messages were sent. Add an
organization-scoped delivery outbox, recipient consent/preferences, provider IDs,
signed callback verification, status history and ambiguous-timeout handling before
enabling delivery. Do not blindly retry a provider timeout and double-send.

## Live setup status and remaining acceptance

Cloud Shell authenticated as admin@workzoneos.org after initial session delay.
Bucket inventory: `enterprise-gemma2_cloudbuild`, `gemma_think_v2`, both US.
SQL inventory could not run: Cloud SQL Admin API disabled. API list showed no
enabled SQL Admin/Identity Toolkit/Firestore entry. This does not prove absence
of historical resources. No existing buckets were changed.

Cloud provisioning awaits the requested monthly operating budget. Still needed:
enable APIs; choose/price database tier and backups; dedicated runtime identity;
database/user/Secret Manager; private versioned bucket; authentication provider
and authorized domains; verified sign-up/login/recovery; cloud restart/restore
drill; attachment UI and scanning; durable source library; V1-data import if
recoverable; real-user permission/browser acceptance; Twilio configuration.
No production cutover, real customer migration, or completed durable cloud
deployment is claimed by the local implementation.

Official design references:
- https://docs.cloud.google.com/sql/docs/postgres/connect-run
- https://firebase.google.com/docs/auth/admin/verify-id-tokens
- https://firebase.google.com/docs/auth/admin/manage-sessions
- https://docs.cloud.google.com/storage/docs/uniform-bucket-level-access
