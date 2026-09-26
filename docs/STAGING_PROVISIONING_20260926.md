# Persistent staging provisioning - September 26, 2026

Ray approved the priced configuration in STAGING_CONFIGURATION_PROPOSAL.md.
Resources below are billable now. This is restricted staging, not production acceptance.

## Created resources

- Project: enterprise-gemma2 (910004733138); region us-central1.
- Cloud SQL: wzos-v2-staging-db, PostgreSQL 16.15, Enterprise db-g1-small,
  zonal, 10 GiB SSD, automatic growth capped at 20 GiB. Database wzos, user wzos_app.
- Daily backups at 06:00, seven retained; deletion protection enabled.
  Connector enforcement REQUIRED, encrypted-only connections, authorized client networks empty.
- Files: enterprise-gemma2-wzos-v2-files-staging, regional Standard, uniform access,
  public access prevention enforced, versioning, seven-day soft delete;
  noncurrent objects expire after 30 days. Current objects retained.
- Identity Platform initialized; email/password enabled. Authorized domains:
  localhost and enterprise-gemma2.firebaseapp.com. No real sign-in acceptance yet.
- Auth browser key wzos-v2-auth-browser restricted to Identity Toolkit/Secure Token
  and localhost/127.0.0.1 port 8080 referrers. Cloud Shell preview origin still needs
  exact verification/configuration before browser acceptance.
- Secret Manager: wzos-v2-staging-database-url and wzos-v2-staging-auth-web-key.
  Values were not committed. No service-account private key created.
- Runtime: wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com;
  Cloud SQL Client, bucket-scoped object creator/viewer and bucket metadata reader,
  access to the two application secrets, custom firebaseauth.users.get role.
- Cloud Run: wzos-v2-accounts-00001-nch, image source commit
  9e03a8bf2e3995a8f2b9a096dd6fa58608787117. Build a04ac66f-2376-49ad-9fe7-8f64bf259baa.
  One CPU/512 MiB; minimum 0, maximum 2 instances, concurrency 8, timeout 60s.
  URL: https://wzos-v2-accounts-910004733138.us-central1.run.app
- Budget: WZOS project guardrail - includes existing services, $50 monthly,
  thresholds 50/80/100 percent. Project-wide including existing services; not a
  staging-only cost allocation or hard spending cap. Notification delivery untested.

## Observed validation

- Build and startup succeeded. Deployment script checked IAM has no allUsers or
  allAuthenticatedUsers invoker bindings. Anonymous GET returned 403; authorized
  tester GET returned 200 with HTML.
- SQL state RUNNABLE; queried actual server version 16.15. Seven-backup retention,
  deletion protection and empty authorizedNetworks verified live.
- Managed SQL acceptance executed all 24 account tests (12 SQLite and 12 PostgreSQL):
  18 passed, four failures and two errors. All 12 SQLite cases passed.
  Proxy logs show intermittent TCP connection refusals to the instance on port 3307;
  two errors explicitly failed at connection creation. Failures affect module
  persistence, file retrieval, membership/revocation and report persistence. Do not
  treat this run as acceptance or assume every failure has one cause.
- Tests used isolated test schemas with cleanup and synthetic identities/local file
  storage. They did NOT verify Firebase sign-in or Google object round trips.
- Cloud SQL initially granted cloudsqlsuperuser and CREATEDB/CREATEROLE to the app
  user. Removed those privileges and replaced membership with wzos_runtime, scoped
  to CONNECT/CREATE on wzos and USAGE/CREATE on public schema. App owns its tables.
  Separating schema migration credentials from runtime remains a production gate.

## Follow-up status (September 26)

Items 1 and 2 below are complete for restricted staging. See STAGING_ACCEPTANCE_20260926.md for the final passing evidence and current revision. Earlier failed runs above remain historical evidence. Next: item 3, then item 4.

## Acceptance sequence

1. Diagnose intermittent SQL proxy connection failures; repeat PostgreSQL tests from
   a stable connection and confirm deployed runtime behavior. Do not hide failures.
2. Verify browser sign-in, token refresh, verified-email enforcement, admin/member
   and cross-organization boundaries through the IAM proxy. Verify both IAM and
   Firebase tokens reach their intended validators.
3. Verify private Google file upload/download, integrity, anonymous denial and
   persistence after instance replacement. Add scanning before non-synthetic uploads.
4. Run and verify backup restoration; configured backup retention is not a restore test.
5. Configure service error/database capacity alerts and verify notifications.
6. Add Atlas/provider integrations and run the integrated September 30 scenario.

V1 service revisions, DNS and existing buckets were not changed. Supabase is not
used by the new runtime. No customer emails, SMS or MMS were sent.

Cloud Shell evidence (temporary, not Git-backed): /tmp/wzos-accounts-deploy.log,
/tmp/wzos-managed-tests.log and /tmp/wzos-sql-proxy.log. Clean isolated checkout:
/tmp/wzos-accounts-release-hgU7WBmb. Existing V1 checkout untouched.
