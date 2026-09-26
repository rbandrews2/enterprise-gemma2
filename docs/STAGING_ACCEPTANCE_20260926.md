# Restricted staging database and identity acceptance - September 26, 2026

Scope: first two follow-up items from STAGING_PROVISIONING_20260926.md.
No public cutover, V1 edits, SMS, MMS or email delivery.

## Database connection repair

The initial run opened a new connection for each operation and encountered
intermittent Cloud Shell-to-Cloud SQL TCP refusals. Added a bounded psycopg pool:
zero minimum/four maximum per instance, health check on checkout, 15-second
acquisition bound, five-second connect bound and bounded waiting queue. Connection
creation can retry before work starts; application transactions are never replayed.
The pool closes on application shutdown. Statement/lock limits are transaction-local.

Moved identity lookup outside the order/checklist database checkout so simultaneous
readers cannot hold every connection while waiting for another one to authenticate.
A single-connection test exercises both routes. Added actual database tests for
connection reuse, rollback after an error, and replacement of closed connections.
Test schema creation/cleanup now use the same bounded adapter: an intermediate
28-test run passed application assertions but failed one raw-connection cleanup.

Reference: [Psycopg pool documentation](https://www.psycopg.org/psycopg3/docs/api/pool.html).

## Real identity and browser validation

- Created four explicitly synthetic Firebase users and two synthetic organizations.
  Verified flags were set by the operator for fixtures; email delivery was not tested.
- Real password sign-in and Secure Token refresh succeeded in provider checks.
- Requests require both Cloud Run IAM and a verified Firebase token. Missing IAM,
  forged app token, unverified email and cross-organization access were rejected.
- Member access cannot list/administer membership or create admin invitations.
  Disabling/demoting the last active administrator is rejected.
- Browser verified unverified-email message, admin organization selection, team
  access controls and the last-admin protection message. Sign-out returns to sign-in.
- Cloud Shell intercepted the standard Authorization header before requests reached
  the app: wrong passwords returned a normal provider error, valid passwords failed
  on the following workspace request. Staging now explicitly configures
  WZOS_ACCOUNT_AUTH_HEADER=X-WZOS-Authorization; default remains Authorization.
  Both options verify identical provider tokens. No fallback to unsigned identity.
- Exact Cloud Shell origin is allowed in staging configuration and the restricted
  Auth browser key. No wildcard cloudshell domain was allowed. The Google proxy
  uses X-Serverless-Authorization for IAM, separate from the app token.
- Two JavaScript tests cover concurrent refresh deduplication, retained organization,
  refresh failure and recovery for both supported header modes.

## Operator workflow

Use scripts/validate_managed_accounts.py only for this named restricted staging
service. Run prepare with WZOS_SYNTHETIC_PASSWORD set, state outside Git, and a
loopback SQL proxy on 5544. The state file is created with mode 0600 and includes
credentials. resume completes interrupted fixtures; verify checks actual provider
and app boundaries; disable revokes tokens and disables fixtures without deleting
records. No API for ingestion, fixture creation or administrator bypass was exposed.

## Remaining separate gates

Private Google object round trips/integrity and instance replacement; malware
scanning before real uploads; backup restoration; real email verification/recovery
delivery; operational alerts; final customer ingress/domain; Atlas and module
acceptance. These checks do not establish full production readiness or load capacity.

## Final evidence and release checkpoint

- Deployed revision: wzos-v2-accounts-00004-fc6.
- Image/source: 0e47a14; build 202fb025-eb2a-40be-a3b0-b9a72c61c13b.
- Managed account suite: 29 passed (13 SQLite + 16 PostgreSQL), no skips,
  130.061 seconds. Includes single-connection reads, real rollback and closed
  connection replacement. Final log: /tmp/wzos-accepted-managed-tests.log.
- Final local regression: 138 passed, 16 PostgreSQL cases skipped locally (154
  collected). Those 16 ran successfully against managed PostgreSQL as above.
- JavaScript token refresh: two tests passed, one for each header configuration.
- Final deployed real-provider checks: PASS after revision 00004-fc6; log
  /tmp/wzos-accepted-provider-tests.log. IAM, refresh, verified-email enforcement,
  admin/member, cross-organization and last-admin boundaries exercised.
- Browser: unverified account blocked; admin has Team access; last-admin disable
  rejected; member has no Team access; sign-out works. Member created and reloaded
  a synthetic work order through the deployed service. Existing test memberships
  survived deployment to the new revision.
- The staging UI still has historical "Saved locally", "Local development" and
  synthetic labels. These do not describe its managed storage; replace those
  labels during customer-facing release cleanup. No claim of production-ready UI.

The two selected checklist items are accepted for restricted synthetic staging.
This is not a throughput benchmark or proof that the underlying network can never
fail. Pool failures remain bounded and return storage-unavailable responses.

Cleanup completed: four synthetic provider users disabled, refresh tokens revoked,
and both test organizations disabled. The browser was signed out and left at the
restricted sign-in page. Sensitive tokens were removed from the operator state file.
One abandoned test schema from the earlier failed cleanup was removed after all
tests finished; only app-owned names matching the isolated test UUID pattern were
eligible. Synthetic work-order evidence remains in the disabled organization.
