# Operational integration acceptance — October 8, 2026

## Access contract

Admins manage all organization workflows and records. Admin privileges never cross
organization boundaries, bypass edition entitlements, or reveal infrastructure secrets.
Members clock their own shifts, view their own timesheets, access organization work
orders, navigate, complete assigned training, participate in meetings, and create,
edit and send permitted form submissions. Admin-only template administration is
separate from member editing of completed form instances. External delivery still
requires recipient authorization, provider configuration and audited retries.

## Candidate and actual gaps

Forms and Time Clock were combined in `codex/integration-release`, including current
Atlas help and both modules' assets. Shared conflicts were resolved without removing
either module. This candidate has not replaced staging or enterprise-v2.

| Area | Existing implementation | Remaining acceptance/work |
|---|---|---|
| Accounts | Google identity, server organization membership and admin/member checks | Invitations, recovery delivery, diverse external users, onboarding and entitlement lifecycle |
| Work orders | Versioned persisted jobs, geometry, checklist | End-to-end member/admin acceptance and full report linkage |
| Time Clock | Shifts, breaks, corrections, audit, offline review, exports | Combined PostgreSQL/browser gate; provisional policy decisions |
| Forms | Template library, admin uploads, printable worksheets; prior scoped draft API | Saved member draft UI restored and browser-verified; internal/external sending remains incomplete |
| Navigation | Google Maps handoff and limited offline notes | Current key/referrer verification, field acceptance; no offline map tiles |
| Training | Catalog and personal study progress | Authorized playable media, assessments and completion/qualification records |
| Messaging | Organization-scoped stored messages | Delivery provider, notifications, status webhooks and retries |
| Meetings | No connected provider | Provider selection, organization-scoped scheduling/join, member access |
| Schedule/dispatch | Admin schedule drafts and conflict checks | Enterprise crew proposals, review, delivery and acknowledgement |
| Atlas/report | Source-aware guidance and versioned report drafts | Live reliability, reviewed placement rules, imagery/PDF/delivery acceptance |

## Credential inventory without secret disclosure

Source verification: `deploy_accounts_staging.sh` injects Secret Manager database and
authentication web configuration. `setup_secrets.sh` provides operator setup support.
A historical setup record is not proof of current secret availability or permissions.
`python scripts/audit_credential_metadata.py` queries only secret names/version states;
it never invokes secret-version access and never prints provider errors or values.
Run this in authorized Cloud Shell to refresh current availability.

| Integration | Configuration needed | Evidence/status |
|---|---|---|
| Database | wzos-v2-staging-database-url, Cloud SQL instance, runtime IAM | Existing deployment binding; live metadata refresh pending |
| Authentication | wzos-v2-staging-auth-web-key, project ID, authorized domains, runtime identity | Existing binding; external-account and recovery delivery acceptance pending |
| Private files | Bucket name and runtime service identity | Existing GoogleFiles adapter; new Forms real-object acceptance pending |
| Maps | Restricted browser key, enabled APIs, exact allowed origins | Dedicated key documented; current restrictions must be checked |
| Twilio | Account SID, API key SID/secret or supported credential, Messaging Service SID/sender | Not verified/configured by this audit; do not assume absent from user's account |
| Email | Provider API credential and verified sending identity/domain | Provider/account capability unverified |
| Meetings | Selected provider, tenant/customer setup, OAuth client and redirect/scopes if required | Awaiting Ray's provider preference |
| Atlas | Private service URL, runtime service identity/invoker binding | Existing integration; latest concurrent live acceptance remains unresolved |

Passwords and secret keys must be entered through authorized provider/Secret Manager
flows, not committed or pasted into chat. Public browser configuration is distinct
from server-side secrets. Do not distribute service-account private keys to clients.

## Execution order

1. Complete combined database, private-files and browser acceptance.
2. Integrate saved member form submissions and internal delivery with revision checks.
3. Finish account lifecycle and organization administration.
4. Connect selected messaging/email/meeting providers using controlled test recipients.
5. Complete training/dispatch/report/Atlas gaps above.
6. Run cross-tenant admin/member and Core/Enterprise pilot; resolve launch checklist.

No module is complete merely because its menu or screen exists. Production cutover
requires separate approval; the approved staging budget remains $150 for October8–17.

## Validation for this increment

- Combined candidate before final draft-route changes: Python292 tests,245 passed,47 PostgreSQL skips; Node16 passed.
- Metadata audit:2 focused tests passed. Draft backend:7 focused tests passed after routing repair. JavaScript syntax and diff checks passed.
- Browser at127.0.0.1:8081: Enterprise member saved and reopened a synthetic incident at revision1; Enterprise admin reopened it; Core member in another organization saw no saved records. No external send occurred.
- Combined PostgreSQL gate and real private-GCS acceptance remain open. Earlier isolated module PostgreSQL passes do not replace this gate.
- Chrome Cloud Shell binding failed again with debugger unattached; no live credential metadata was retrieved and no cloud change was made.
- Loopback preview uses synthetic identities, local files and local intelligence; it is not production authentication or live Atlas acceptance.
