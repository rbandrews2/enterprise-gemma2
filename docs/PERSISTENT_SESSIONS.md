# Persistent sessions implementation contract

Add browser_sessions at account workspace startup (deployment is a migration):
CREATE TABLE IF NOT EXISTS browser_sessions (hash TEXT PRIMARY KEY,user_id TEXT NOT NULL,expires_at TEXT NOT NULL);
Only SHA256 of signed session cookies is stored. No passwords, raw tokens or biometric data. Additive DDL; older app can ignore table. Rollback disables cookie authentication; invalidate rows before later re-enabling if rolling back for a security issue.

POST /api/account/session exchanges a recently authenticated, verified Firebase ID token for a 14-day HttpOnly Secure SameSite=Strict __Host-wzos-session cookie. POST /api/account/logout revokes that cookie's registry row and clears it. POST /api/account/logout-all revokes all this user's registry rows. All cookie requests and session mutations require X-WZOS-Session:1; existing same-origin/CORS boundary denies foreign origins. Membership and provider revocation checked on each request. Cookies never carry trusted roles/org selections. No new public/production deployment in this increment.

Unchecked stay-signed-in uses existing memory-only mode. Explicit logout failure remains visible. Provider/session expiry requires fresh sign-in; no indefinite sliding expiration. Passkeys remain a subsequent increment, not a claim of this migration.

Validation: full Python304 (253 passed,51 PostgreSQL skipped); Node19 passed. Four focused cookie lifecycle/security cases plus PostgreSQL equivalents added. Node tests cover checked/unchecked choice, restoration and logout. Browser sign-in dialog verified unchecked14-day option and accurate reload/reopen explanation. Actual Google cookie issuance, PostgreSQL schema gate, browser cookie restore and mobile OS lifecycle remain open. Local auth-validation server used for UI only; no real user credentials or account calls.

Reference: https://firebase.google.com/docs/auth/admin/manage-cookies

## October 8 validation follow-up

Candidate780f473: full local309tests,256passed/53PostgreSQLskipped; account JavaScript5passed. Added provider-failure preservation, session replacement and required-header tests. PostgreSQL run at4f73180 is awaiting Docker image extraction in Cloud Shell; not accepted. Inspect ~/wzos-session-gate.log before retrying. Real provider cookie and mobile lifecycle acceptance remain open. Metadata-only credential audit now handles lowercase gcloud states; both expected secrets have enabled version1, but runtime access is unverified.

PostgreSQL acceptance October8: candidate40c9439 passed all309tests with zero skips in60.034s using scripts/test_postgres_native.sh on installed PostgreSQL16 in Cloud Shell. Docker download was stopped after stalling; initial native SQL_ASCII setup was corrected to UTF8. Full Node19passed. Provider/browser/device acceptance remains separate.

Real-provider acceptance October8: scripts/validate_provider_sessions.py passed against enterprise-gemma2 using the existing authorized Cloud Shell preview origin and Secret Manager web key (not printed). Verified real ID token,14-day cookie issuance, verification and rejection after revocation; synthetic user disabled on exit. No organization membership, shared database writes, email or deployment. Empty temporary-cluster directory listing verified cleanup. Integrated browser cookie transport, reopen/logout and real phone lifecycle remain open.
