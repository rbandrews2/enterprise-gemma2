# Passkey integration contract

Opt-in configuration: WZOS_PASSKEY_ORIGIN must be an exact HTTPS origin (http://localhost allowed only outside hosted runtime), and WZOS_PASSKEY_RP_ID must match that origin host exactly. Defaults disabled. No automatic IAM grants or deployment.

Routes: POST /api/account/passkeys/register/options and /register/verify; POST /api/account/passkeys/login/options and /login/verify; GET /api/account/passkeys; DELETE /api/account/passkeys/{credential_id}. Enrollment and removal require recent verified Google authentication. Authentication yields a Firebase custom token only after WebAuthn verification and a live enabled/verified Firebase user check; the browser exchanges it using the existing Google flow. Organization and edition checks remain unchanged. User verification is required; fingerprint/face/PIN stays on the authenticator.

Startup DDL (deploying enabled code applies migration):
```sql
CREATE TABLE IF NOT EXISTS passkeys (id TEXT PRIMARY KEY,user_id TEXT NOT NULL,public_key TEXT NOT NULL,sign_count INTEGER NOT NULL,label TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS passkey_challenges (hash TEXT PRIMARY KEY,challenge TEXT NOT NULL,kind TEXT NOT NULL,user_id TEXT NOT NULL,expires_at INTEGER NOT NULL);
```
Challenges expire in five minutes, are bound to a Secure HttpOnly SameSite=Strict host cookie, and are atomically consumed before verification. Check exact origin, RP ID, challenge, signature, user handle and user verification. Credentials have no role or organization grants. Removal revokes remembered sessions for the account. No biometric templates stored. Additive schema; rollback disables feature and leaves inert public-key records. Password recovery remains available.

Acceptance: cryptographically signed test ceremonies (including bad origin/challenge/signature and replay), cross-account deletion and stale auth, concurrent/expired challenges, disabled provider user, PostgreSQL gate, browser cancel/fallback, iOS/Android/desktop authenticator and recovery. Production rollout requires bounded edge rate limits and real token-signing IAM verification. Local/synthetic success does not satisfy device acceptance.

## Validation October 8

Candidate447b240: full Python323tests,263passed/60PostgreSQLskipped; Node21passed. Seven real cryptographic ceremony tests plus PostgreSQL equivalents are included. Google provider token signing, PostgreSQL execution of these new tables, browser authenticator behavior and real phones remain unverified. Browser/Cloud Shell connection timed out twice; no deploy or configuration enablement. Install requirements-accounts.txt for the complete suite. Enrollment, removal, login/cancel/password fallback controls are wired in account.js but hidden when configuration or browser support is absent.

## Real Android acceptance October 8
Ray reported successful passkey creation and sign-in with the key on his Android phone against restricted staging. Android remembered-session refresh and closing/reopening were also user-observed passes. Cancellation/password fallback, device key removal/recovery, iOS coverage and desktop reload follow-up remain open. Server signing/exchange/replay/removal and secure cookies separately passed the real-provider probe on revision00030-c6h; the broader PostgreSQL gate passed337tests with zero skips. Preserve the working device credential.
