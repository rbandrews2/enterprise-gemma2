# Admin hub, security and integration API â€” October 14, 2026

## Scope and current state

Ray requested an admin landing page, application hardening and an integration API,
with heavier work in Cloud Shell while the laptop is maintained. Changes are in
Codex's integration checkout, not Claude's checkout. This is a source increment;
no public deployment or new cloud resource is authorized by this document.

## Admin dashboard

Admins land on Dashboard. Members retain their existing workspace. Existing
Core/Enterprise module entitlements remain; Work Zone Report is Enterprise-only.
Preferences hide dashboard shortcuts only, and never grant or remove API access.
Employees, team access and passkeys link to existing account controls when present.
Short shared notes are admin-only, organization-scoped, limited to 500 characters,
50 displayed / 500 retained. UUID retries are idempotent; other admins can remove
notes. Note text is rendered with textContent, never HTML. Notes are not SMS.
Preferences use optimistic version checks and apply to all admins of the organization.

Status is green only when service, account and security checks are all current and
verified OK. A current problem is red with its recorded explanation; missing,
invalid or expired observations are amber. No billing, device compromise detection,
or whole-service health is inferred from successful login/database access.
The hub_status_checks table has NO HTTP write endpoint: trusted billing/monitoring
adapters or operators must supply source, checked_at and expires_at with evidence.
These adapters are not yet integrated. Default amber is deliberate. Do not insert
sample green checks into live organizations. A website cannot establish that an
installation device is uncompromised without a suitable device-security integration.

## API v1 contract

Admin browser session endpoints:
- GET /api/admin/dashboard
- PUT /api/admin/dashboard/preferences: expected_version, hidden_modules
- POST /api/admin/dashboard/notes: request_id UUID, text
- DELETE /api/admin/dashboard/notes/{id}
- GET /api/admin/integrations
- POST /api/admin/integrations: name, scopes, expires_in_days (1â€“90, default30)
- DELETE /api/admin/integrations/{id}

Server-to-server endpoints use X-WZOS-API-Key over HTTPS:
- GET /api/integrations/v1/orders?limit=25&offset=0 â€” orders:read
- GET /api/integrations/v1/schedule?limit=25&offset=0 â€” schedule:read

API credentials contain 256 random bits, are displayed once, stored SHA256-hashed,
never in URLs or browser persistence, and cannot authenticate browser sessions.
Maximum10 active credentials per organization. All scopes are read-only. Each
request rechecks expiry/revocation and the issuing admin's active membership and
organization. Creator demotion/removal disables their credentials. Another admin
must issue a replacement after reviewing the connection; admin privileges are not
transferred. Rate limit60 requests/minute/organization, shared across credentials;
429 includes Retry-After60. POST notes/credentials additionally limited30/min/org.
limit1â€“50, offset0â€“10000; invalid requests422, bad/expired credentials401, missing
scope403. New admin/integration routes bound actual request bodies to16KiB even
without Content-Length. No cross-origin browser access/CORS exception is added.

Work-order projection: id, version, updated_at, title, address, work_type, work_date.
Schedule projection: id, version, updated_at, title, location, start, end, status.
No private notes, phone/email lists, meeting tokens, passwords or file links exported.
Pages are ordered by updated_at then id; exports are current reads, not a frozen
multi-page snapshot. Connectors must deduplicate by id/version and handle updates.
There are no write/import endpoints, webhooks or financial/payroll side effects.
An API client must store its credential server-side in its secret manager; never
ship it in a mobile/web bundle. Log identifiers/statuses only, not API headers.

This is a connection foundation, NOT a finished QuickBooks or Workday connector.
Provider OAuth applications, customer tenant authorization, scopes, mappings,
sandbox acceptance, retry/deduplication and revocation still need implementation.
There are no vendor calls or new paid services in this increment.

## Security controls and remaining evidence

Implemented: organization/role checks on all hub management routes; fixed API scopes
and field projections; active membership checks; random hashed/revocable expiring
credentials; parameterized SQL; bounded inputs/exports/rates; audit metadata without
note content/token secrets; no public status-writing route; safe text rendering;
no-store responses; CSP retained; X-Frame-Options DENY, Referrer-Policy strict-origin-when-cross-origin,
Cross-Origin-Resource-Policy same-origin; hosted HTTPS HSTS max-age31536000.
No includeSubDomains/preload change is made. Existing Daily iframe allowlist remains.

SOC2 is an independently assessed organizational program, not a code flag. This
increment provides some access-control/change-management/logging building blocks;
it does not establish SOC2 compliance or guarantee protection against all attacks.
Remaining priorities: file malware quarantine/scanning and clean-result release;
patch/vulnerability remediation; backup/restore evidence; centralized tamper-resistant
log retention; incident response/access reviews; privacy/retention/vendor controls;
credential rotation/runbooks and incident exercises. Existing PDF/image/Office type
checks and attachment-only downloads are not antivirus. Never disable existing
protection or install unreviewed cleaner/driver tools to improve performance.

## Schema / rollback

Startup applies scripts/organization_hub_schema_review.sql: six additive tables and
one audit index. No existing customer tables/records are altered or deleted. Review
and exact PostgreSQL gate precede deployment. Old runtime ignores the new tables;
rollback traffic first, revoke new integration credentials before removing API
support, retain notes/preferences/audit records. Export keys must not be restored
from backups without checking revocation intent. Audit retention/purge is an
operator policy to define before broad customer integrations; the short-lived
rate-counter table is automatically pruned. Do not drop tables during rollback.

## Dependency audit and patch candidate

Cloud pip-audit found26 raw advisory entries (including duplicates) across old pip
and Starlette0.41.3. The first cloud candidate passed594 PostgreSQL tests/no skips
and96 Node tests, but passing those does not resolve dependency vulnerabilities.
Official PyPI metadata verified FastAPI0.143.1 supports Starlette>=0.46.0 and
Starlette1.8.0 / pip26.2.1 are published. Candidate pins FastAPI0.143.1,
Starlette1.8.0; accounts Docker/test runners bootstrap pip26.2.1. Exact patched
cloud suite and repeat audit required. No local global Python install is changed.
A source-only overlay build on the previous image would retain vulnerable packages:
future deployment MUST reinstall the patched requirements and verify runtime versions,
while preserving the frozen agency source library. Do not blindly reuse old overlay
build helpers. Live public runtime is NOT patched by this source commit.

## Validation

Initial focused run exposed two test-fixture assumptions (status insert placeholders
and existing synthetic seed orders); fixtures repaired. Full cloud gates and browser
review are pending. No real organization notes, keys, SMS or customer exports have
been created. Existing Daily/Maps/Twilio/Atlas/checkout acceptance gaps remain.
