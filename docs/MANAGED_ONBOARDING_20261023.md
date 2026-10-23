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
- Existing 26 account JavaScript checks passed.
- PostgreSQL, new UI acceptance, Google provider acceptance and deployment remain open.
- Ray's live Enterprise/25 grant has not been issued yet.
