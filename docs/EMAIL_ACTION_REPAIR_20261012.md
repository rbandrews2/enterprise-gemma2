# Firebase email-action repair proposal — October 12, 2026

Not applied. Owner: Molecular Project Development LLC; project enterprise-gemma2.

## Observed failure

Ray reports existing admin@workzoneos.org account, reset email received and newest
email link clicked directly. Firebase returns selected page mode invalid. Ray confirms
apiKey query parameter blank; mode metadata resetPassword. No reset code or key is
stored here. Do not open/read the mailbox or print reset URL/title.

Read-only project configuration:
- Email/password enabled. Current reset template uses %LINK% (two occurrences),
  no literal reset URL or blank apiKey. callbackUri is the stock
  https://enterprise-gemma2.firebaseapp.com/__/auth/action, no query parameters.
- client.apiKey matches the current WZOS authentication secret, 39characters.
- Firebase web app count0. Default Hosting site enterprise-gemma2 exists with no appId.
- Public /__/firebase/init.json returned404. This is an incomplete Hosting/web-app
  linkage, not by itself proof of every part of the reset error.
- Key wzos-v2-auth-browser UID27528ede-260b-4af7-bfcf-6b688bd8630d is restricted to
  identitytoolkit.googleapis.com and securetoken.googleapis.com. Allowed referrers:
  http://localhost:8080/*, http://127.0.0.1:8080/* and
  https://8080-cs-1002772085547-default.cs-us-east1-pkhd.cloudshell.dev/*.
  Firebase email-action origin is absent; provider calls there are not authorized.

## Concrete proposed changes, subject to action-time approval

1. Preserve both API restrictions and all three existing referrers. Append only
   https://enterprise-gemma2.firebaseapp.com/* to wzos-v2-auth-browser.
2. Register a WebApp named WZOS email actions in projects/enterprise-gemma2 using
   apiKeyId27528ede-260b-4af7-bfcf-6b688bd8630d. Explicitly reuse this key; do not
   allow automatic key creation or request any new API, IAM role or database.
   POST https://firebase.googleapis.com/v1beta1/projects/enterprise-gemma2/webApps
   body: displayName=WZOS email actions, apiKeyId=the existing key UID.
   Wait for the bounded create operation and verify its final apiKeyId.
3. Link only projects/enterprise-gemma2/sites/enterprise-gemma2 to the returned appId.
   PATCH https://firebasehosting.googleapis.com/v1beta1/projects/enterprise-gemma2/sites/enterprise-gemma2?updateMask=appId
   body: appId=the verified WZOS WebApp ID.

Before applying, save restricted-key metadata and existing site metadata with
private file permissions in the persistent Cloud Shell evidence directory. Abort
on unexpected existing app linkage/key association or any request for new terms.
No account deletion, password entry, email-verification bypass, application DNS/
Cloud Run exposure or production traffic change is part of this repair.

## Acceptance and rollback

Read back API/referrer restrictions, WebApp apiKeyId and Hosting appId. Recheck
public init.json200 and compare project/key only in memory; never print keys.
Ray requests a fresh reset email, confirms the new link has a populated apiKey,
and enters the new password himself. Successful WZOS password sign-in and normal
verified-email gating required before calling recovery accepted. If unsuccessful,
record the remaining exact failure; do not bypass identity checks.

Rollback restores the exact prior referrer list and clears only the Hosting appId
if it was initially absent. Keep the registered WebApp as unused metadata pending
review; do not delete the shared key, account or project. No authentication data
migration or new persistent paid server is involved.

## Reference documentation

- https://firebase.google.com/docs/auth/custom-email-handler
- https://firebase.google.com/docs/reference/firebase-management/rest/v1beta1/projects.webApps/create
- https://firebase.google.com/docs/reference/firebase-management/rest/v1beta1/projects.webApps
- https://firebase.google.com/docs/reference/hosting/rest/v1beta1/projects.sites

## Approval-review limitations

Automatic approval review blocked mailbox access due to private email/reset-token
risk, and blocked transmitting the stored key in an API-key lookup URL. Neither
blocked action is needed for this proposal; metadata-only resource listing and
key restrictions were used instead. Explicit approval is needed for the proposed
authentication-key origin expansion and public Hosting client configuration.

## Applied and accepted — October 12, 2026

Ray approved the narrow Firebase repair. Existing auth key kept both API
restrictions and three referrers; only Firebase email-action origin added.
WebApp1:910004733138:web:4637cebf8f530a453d990b reuses the existing key UID.
Default Hosting site linked to it. The site had no releases; an empty bootstrap
release activated reserved SDK configuration without replacing app content.
Release sites/enterprise-gemma2/releases/1791840839205000. Fresh init.json HTTP200,
project and key comparisons true, API key present; no secret value printed.
Prior metadata and release evidence saved privately in Cloud Shell release folder.
Ray successfully reset his password himself and reached the organization chooser.
Password recovery accepted; organization membership still pending separately.
No WZOS public cutover, verification bypass, new key or IAM change.
The proposal and pending-approval wording above are historical, superseded here.
