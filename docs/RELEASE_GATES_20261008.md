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
