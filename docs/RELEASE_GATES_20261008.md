# Release gates and authentication checkpoint — October 8, 2026

## Task 1: completed

- Exact application candidate42dd58d: Cloud Shell PostgreSQL16,337tests/61.712s, zero failures/errors/skips.
- Log: ~/wzos-release-gate-42dd58d.log; checkout /home/admin_/wzos-release-gate-HMnun7mN.
-75527e3 adds only an operator validation script. Real private GCS upload/hash, unpublished member denial, publication/member download, cross-organization denial, member delete denial and restart persistence passed. Synthetic objects removed; no /tmp/wzos-pg-gate.* directories remained.
- Prior full Node21 and local browser workflow evidence remains applicable. Fast-forwarded local and GitHub enterprise-v2 to75527e3. No deployment.
- Screenshot (ignored local): .local-data/release-gates-proof.png.

## Task 2: preflight; not accepted

Live restricted service wzos-v2-accounts remains revision00029-d6k at https://wzos-v2-accounts-udtvm4rgca-uc.a.run.app. Its service IAM policy has no public bindings. Secret Manager metadata confirms enabled database and authentication-web-config versions; secret values were not printed.
WZOS_PASSKEY_ORIGIN/RP_ID are not configured. Configured account origin remains https://8080-cs-1002772085547-default.cs-us-east1-pkhd.cloudshell.dev and auth header X-WZOS-Authorization.
Runtime wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com has project bindings wzosAuthLookup (firebaseauth.users.get only) and roles/cloudsql.client; its service-account policy has no explicit bindings. Inspected policies show no signBlob grant; no effective runtime signing test yet, and ancestor policies were not audited.

### Proposed narrow signing grant — awaiting action-time approval

Create custom role wzosPasskeySigner containing only iam.serviceAccounts.signBlob. Bind it to the runtime principal on its own service-account resource only. This permits signing custom authentication tokens; it adds no organization membership/role and grants no access to other service accounts. Do not use project-wide Token Creator.

```bash
gcloud iam roles create wzosPasskeySigner --project=enterprise-gemma2 --title='WZOS passkey token signer' --permissions=iam.serviceAccounts.signBlob --stage=GA
gcloud iam service-accounts add-iam-policy-binding wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com --project=enterprise-gemma2 --member=serviceAccount:wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com --role=projects/enterprise-gemma2/roles/wzosPasskeySigner
```

Inspect for an existing role before creation; do not overwrite conflicting definitions. Rollback removes that exact binding. After approval, verify effective signing, preserve restricted access/current settings during deployment, configure exact test origin/RP host and perform real Google/HTTPS session and authenticator tests. Real iOS/Android user gestures are required; synthetic tests do not satisfy those gates.

## Task 3: not started

User requested strict sequence. Organization setup/invitations/recovery/employee profiles and entitlements follow task2 acceptance.

## Approved signing change and live authentication follow-up

Ray approved the exact self-scoped signBlob grant. Applied and read back: wzosPasskeySigner contains only iam.serviceAccounts.signBlob; binding is runtime principal on its own service-account resource. No project-wide Token Creator grant.

Billing overview observed October8: October1-8 cost13.55USD before savings,12.05USD after savings, subject to reporting lag; this is not an exact October8-17 spend ledger. Build26seconds SUCCESS. Existing image digest used as base to preserve source binaries; current tested services/shared/knowledge plus pinned requirements copied over. Cloud Run restricted account service revision00030-c6h deployed from app candidatebcf3bc9. Only image/passkey origin/RP configuration changed; service policy still has no public binding. No GPU, V1 or DNS changes.

Live operator probe0e84c96: real Google sign-in, synthetic WebAuthn ceremony, runtime token signing and Google custom-token exchange PASSED. The first probe had a KeyError from expecting localId in Google's response; fixed by verifying the returned ID token's signed uid. Its identity was disabled/revoked but an inert public-key row may remain. Second probe removed its credential and disabled/revoked its identity.

Remembered-session endpoint FAILED503. Runtime inspected grants omit firebaseauth.users.createSession, which Google's official mapping requires for CreateSessionCookie: https://docs.cloud.google.com/identity-platform/docs/access-control . This is a identified missing prerequisite and likely cause; the generic503 alone does not prove the provider cause. Effective policy troubleshooting was unavailable because the Policy Troubleshooter API is disabled; it was not enabled.

### Next narrow permission proposal — not yet applied

Create wzosSessionIssuer with only firebaseauth.users.createSession and bind it on project enterprise-gemma2 to the staging runtime. This lets the backend issue remembered-session cookies for authenticated users. It does not grant user creation, deletion or modification. Requires action-time approval for expanded authentication access.

```bash
gcloud iam roles create wzosSessionIssuer --project=enterprise-gemma2 --title='WZOS remembered-session issuer' --permissions=firebaseauth.users.createSession --stage=GA
gcloud projects add-iam-policy-binding enterprise-gemma2 --member=serviceAccount:wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com --role=projects/enterprise-gemma2/roles/wzosSessionIssuer
```

Inspect for an existing role first. Rollback removes this exact project binding. Rerun scripts/validate_live_passkeys.py after approval; do not deploy again just for an IAM change. Android device available from Ray; real browser/device test remains pending server session acceptance. iPhone remains untested. Task3 stays queued under the requested sequence.

## Approved session-cookie grant and live acceptance
Ray approved the separate createSession grant. Created projects/enterprise-gemma2/roles/wzosSessionIssuer with exactly firebaseauth.users.createSession and verified its project binding to serviceAccount:wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com. Existing revision00030-c6h required no redeployment. scripts/validate_live_passkeys.py passed: real Google identity sign-in, runtime passkey signing/custom-token exchange, replay rejection, credential removal, Secure/HttpOnly/SameSite=strict cookie, cookie-only authenticated access, logout and subsequent401. Probe identity disabled and refresh tokens revoked; credential_removed=True. This is server integration evidence, not physical Android biometric acceptance. Screenshot outside Git: .local-data/session-cookie-live-pass.png. Rollback: remove only the wzosSessionIssuer project binding for that runtime principal. Task2 phone checks remain open; task3 held in sequence.

Restricted HTTPS preview verified rendering the WZOS sign-in page with remembered-session checkbox and passkey button at https://8080-cs-1002772085547-default.cs-us-east1-pkhd.cloudshell.dev/. Authorized Cloud Shell proxy is running on8080; link requires the authorized Google account and active shell. Next: Ray signs in on Android and checks session persistence, passkey enrollment/login/cancellation/removal. No real-device result yet.
