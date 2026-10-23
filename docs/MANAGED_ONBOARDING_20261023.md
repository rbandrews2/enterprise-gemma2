# Admin-managed onboarding

Requested: admins create employee identities, username/password login and
admin/member memberships directly; invitations remain optional. No third role.
Ray's organization grant: ray@workzoneos.org, Enterprise,25active logins.
Existing personal identity passwords are never overwritten by organization admins.

Google Identity Platform remains the password authority. Passwords are transient,
excluded from persistence, audit payloads and validation errors. New managed
identities start disabled at Google; membership is committed before enablement.
Failures leave a disabled identity or incomplete setup. Repeated requests resume
only the same actor/organization/username/email/role operation.

Employees change their initial password before workspace access. Managed access
does not assert email ownership: organization creation and invitation redemption
still require verified email. Username sign-in proxies Google verification without
exposing the username-to-email directory. Generic failures and rate limits apply.
Ordinary email login remains. No automatic email or SMS sends.

Additive tables: managed-onboarding-additive.sql. Rollback keeps tables and
memberships, disables new management routes, and preserves verified-user access.
Unverified managed users cannot sign in on old app versions; restore the new
revision or have those users verify email before rollback use. Provider setup
requires runtime user-create/update/get permissions, separately approved if absent.

Organization creation without a code requires an operator-issued, one-use,
email-bound grant with expiry, edition and seat limit. No hardcoded email bypass.
Ray's grant is installed separately from source code.

## Exact access proposal

Readback on October 23 confirms the runtime currently has only user lookup
and session creation authentication roles. Proposed custom role
`wzosManagedAccounts`, defined in `managed-account-role.yaml`, adds exactly
`firebaseauth.users.create` and `firebaseauth.users.update` to
`wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com` in
`enterprise-gemma2`. It is ongoing access. Google IAM applies these permissions
project-wide, not per WZOS organization: the runtime could create or update
any project authentication identity. WZOS endpoints restrict operations to
admin-created identities and the authenticated employee's own password.
No delete, token-signing, database, bucket, or secret permission is added.
Rollback removes that one role binding; preserve the existing lookup/session roles.

## Validation status

- Nine focused SQLite onboarding checks passed, including isolation, capacity,
  existing identity protection, first password change, retry and email-bound grants.
- All 181 Node checks passed on Cloud Shell; focused account checks are 28/28.
- Synthetic browser acceptance: organization selection, Team access, optional
  invitations and Create employee account fields visible. Screenshot outside Git:
  `.local-data/managed-account-ui-20261023.png`.
- User approved the exact two-permission role; created and bound to the existing
  runtime, then independently read back with only that identity bound.
- All 937 PostgreSQL checks passed in 449.875 seconds against commit 7a674b3,
  zero failures/errors/skips, in an isolated temporary cluster.
- Deployed revision `wzos-v2-accounts-ui-7a674b3` at 100% traffic; independent
  readback passed. Image `6ee61100026337be919f39ccd1d3d3a55238dfdf2d0ed4c5bd636796354887e8`,
  public version `58a02875ab79dd307750c54a`, build `cca8b84b-be79-489f-aa4e-99e8b1a5efab`.
- Schema compatibility/recent backup, staged config preservation, live assets,
  and anonymous account creation/password denial passed. Google username auth
  transport accepted the existing public key/referrer and rejected a nonexistent
  synthetic login as expected. No real credential was used or account created.
- Ray's live Enterprise/25 email-bound grant was issued, expires
  `2026-10-30T05:31:46.920605+00:00`. Ray still creates/verifies his own identity.
- First real managed-account creation and employee password change remain a human
  acceptance check; do not describe them as completed.
- Cloud evidence: `$HOME/wzos-managed-evidence-20261023`. Rollback returns traffic
  to `wzos-v2-accounts-ui-a1d24d1`, retains additive tables, and optionally removes
  only the new managed-account role binding. See compatibility warning above.
- Signed-in production browser acceptance passed: Team access shows Create employee
  account plus Optional invitation; creation form contains name/email/username,
  masked initial password and admin/member choices. No form submitted.
  Screenshot outside Git: `.local-data/managed-account-live-20261023.png`.

Operator helper `scripts/issue_organization_grant.py` reuses a pending matching
grant, refuses conflicting settings and does not overwrite a redeemed grant.
It must run after schema deployment, through the existing authorized SQL proxy.
Only the email-bound seven-day entitlement is written; Ray creates and verifies
his own Google identity. No password or account is created by the operator.

If Google account creation succeeds but the first database commit fails, the
provider account remains disabled with no membership. Contact support for that
reserved email; no automatic deletion or existing-password overwrite occurs.
