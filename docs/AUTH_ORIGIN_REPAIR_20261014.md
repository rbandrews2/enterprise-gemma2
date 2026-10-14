# Production authentication origin repair — October 14, 2026

## Verified failure

Live `/api/identities` returns verified_accounts with an authentication key present.
Three empty invalid provider requests, using the exact production Referer/Origin,
returned HTTP403 and `API_KEY_HTTP_REFERRER_BLOCKED`: signInWithPassword, signUp,
and sendOobCode/PASSWORD_RESET. No account was created, email sent, password used,
or key printed. This proves the shared configuration failure before user credentials
are evaluated. The public-release acceptance checked app/API access boundaries but
did not validate provider-origin acceptance; that release gate was incomplete.

## Narrow repair

Inspect existing key metadata and verify it corresponds to the running browser
configuration without logging its value. Preserve every existing referrer and both
API restrictions (identitytoolkit.googleapis.com, securetoken.googleapis.com).
Append only `https://app.workzoneos.org/*` to that existing authentication key's
browser referrers. Save original metadata privately for rollback. Do not loosen
restrictions to unrestricted/wildcard domains or modify Maps/Routes keys.
Browser-control policy requires confirmation before expanding the key's origin.
The console currently requires admin@workzoneos.org to verify sign-in again.

## Acceptance

Repeat the three invalid requests: they must reach normal provider validation
(HTTP400), not referrer denial. Check refresh-token API with an invalid token;
it likewise must reach validation rather than HTTP403 origin denial. Verify a
different unrelated origin remains HTTP403. Confirm app protected APIs remain401.
User performs real password sign-in/reset and any new-account credentials; do not
claim a real account lifecycle passed from invalid-input tests alone.

## Rollback

Restore the prior exact allowed-referrer list from private metadata, preserving
the existing key, API allowlist and all identities. No deployment/DDL is needed
for the key configuration repair.

## Applied and independently verified

Ray approved the exact production referrer and completed Google reauthentication.
Fresh Shell confirmed admin@workzoneos.org and enterprise-gemma2. Read-back key
metadata showed the four historical referrers, with the production host absent.
The running app's key was compared to the named key only in memory and matched.
Patched restrictions with the current etag, preserving the complete API target list
and appending only the approved referrer. Operation completed; exact restrictions
read-back matched. Private before/after metadata: Cloud Shell home
`wzos-auth-origin-before.json` and `wzos-auth-origin-after.json`, mode600.

`scripts/check_auth_origin.py --origin https://app.workzoneos.org`: PASS, all six
checks. Sign-in, sign-up, reset and refresh reached normal invalid-input HTTP400;
untrusted-origin HTTP403 and protected-account HTTP401 remain enforced. No real
password, user account creation or email delivery occurred in these probes.
Five targeted gate unit tests passed. No runtime image/DDL/traffic change required.
User real sign-in/organization acceptance is pending; do not call negative probes
a completed real-account lifecycle. Previous release-origin validation was incomplete.

Require this bounded provider-origin gate after future origin/credential changes
and before declaring authentication accepted. Never substitute a page200 check.

References: [Firebase Auth REST API](https://firebase.google.com/docs/reference/rest/auth/),
[Google API key restrictions](https://docs.cloud.google.com/api-keys/docs/add-restrictions-api-keys).

## Real admin access accepted

Ray reports successful real password sign-in on app.workzoneos.org, organization
available for selection, and workspace entrance after selecting it. This resolves
the pending real-admin login/organization acceptance above. Fresh account creation
and reset-email delivery were not independently exercised; their shared referrer
block is resolved by the provider-origin probes, not claimed as full lifecycle tests.
