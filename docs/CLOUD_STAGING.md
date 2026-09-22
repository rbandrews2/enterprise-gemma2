# Restricted WZOS V2 Cloud Run staging

Ray approved restricted staging before production replacement. The deployment targets only `wzos-v2-staging` in `enterprise-gemma2`, `us-central1`, using the existing `enterprise-gemma2` Artifact Registry repository. The previous V1 deployment scripts are not used.

## Access and data boundary

Cloud Run IAM must remain enabled with no allUsers or allAuthenticatedUsers invoker bindings. A dedicated runtime service account receives no project roles. The staging app uses one shared synthetic Enterprise reviewer, ignores client-supplied role headers and hides the identity selector. This is an authenticated developer review environment, not customer identity/tenant infrastructure. An IAM-authorized developer can exercise the synthetic fixtures; do not grant customer access.

Use `gcloud run services proxy wzos-v2-staging --project=enterprise-gemma2 --region=us-central1 --port=8080` to review privately. The default run.app URL will reject unauthenticated browser access. If a browser proxy uses a different Origin than the service Host, add only that exact trusted development origin to WZOS_STAGING_ORIGINS; never use wildcard origins. Public browser sign-in via IAP or application identity remains future work.

The database is in `/tmp` and resets on instance replacement, new revisions or scale-to-zero. No real time entries, attendance, customer jobs or employee data may be entered. This is deliberate staging-only behavior, not a production persistence solution. Original local data stays on the local machine. Source documents are not included; the catalog can report missing local revisions. Atlas quick guides work, but cloud model conversation reports unavailable. No local model or old broken inference endpoint is silently substituted.

## Build and deploy

Run `bash scripts/deploy_staging.sh` from a clean, committed checkout. It builds a minimal archive of tracked application files, pins the image tag to the Git commit, uses 1 CPU/512 MiB, max one instance and min zero, and deploys without public invoker access. Temporary build files contain no local recovery archives, keys, model weights or database. Build and runtime usage can incur Google Cloud charges; these scale settings are controls, not a billing cap.

After deployment verify: latestReadyRevisionName; IAM policy and invoker-IAM enabled; unauthenticated HTTP denied; authenticated status and time-clock requests work; browser layout and mutations through authenticated proxy; no changes to V1 service or DNS. Record the exact service URL, image revision and any blockers below. Retain the previous staging image/revision for rollback; staging resets are not data migrations.

## Before real users

Durable database and backup/restore, server-verified user and organization roles, provider policy tests, cloud inference/cost controls, document library, migration, monitoring and production acceptance remain required. The local factory still rejects cloud markers by default. Only the explicit staging factory can run in the dedicated service with WZOS_PRIVATE_STAGING=1.

## Deployment record

Initial deployment succeeded in Google Cloud:

- Service: `wzos-v2-staging`, project `enterprise-gemma2`, region `us-central1`.
- Service URL: https://wzos-v2-staging-910004733138.us-central1.run.app (IAM authentication required).
- Initial code: `15587c1ab7e89fd25108f8850716e94862b164dd`; Cloud Build `7ecf0909-2fbf-49df-bcf4-5fad4a2ec0ff` succeeded.
- Initial revision: `wzos-v2-staging-00001-sd9`.
- Anonymous `/` and `/api/session`: HTTP 403. Authenticated `/api/session` and `/api/time/status`: HTTP 200; fixed staging identity confirmed.
- No public service IAM binding; dedicated runtime identity `wzos-v2-staging@enterprise-gemma2.iam.gserviceaccount.com` created without role grants.
- 110 tests passed before initial deploy. Two focused staging tests passed after the browser navigation/origin adjustment (`83ad543`).
- A Cloud Shell authenticated proxy runs on port 8080; its preview is session-dependent. Browser-origin verification succeeded using the exact Cloud Shell preview origin. A synthetic clock-in and clock-out both saved successfully through the browser. No V1 service or DNS changes were made.

Cloud Shell uses isolated checkout `/tmp/wzos-v2-staging-sV48jaJS`; the historical checkout was not modified. Local Git, GitHub and the image commit are tracked explicitly; subsequent docs-only commits need not trigger another image build.

Browser access verified on revision `wzos-v2-staging-00003-ctz` (code `83ad543e0e8776f3147bc59174a0aa7760366ae0`, build `8be971e7-c334-47db-9d90-c8969a81ef2c`). The exact session origin is https://8080-cs-1002772085547-default.cs-us-east1-pkhd.cloudshell.dev . This address depends on the active authenticated Cloud Shell session and may change. Final label/UTF-8 correction deployed successfully as revision `wzos-v2-staging-00004-swh`, image source commit `3a69b4200ff664dc79fcca71cd913f46fded8ee9`. Browser reload verified the final revision renders the staging banner and Atlas greeting correctly.


## 2026-09-22 module and report revision rollout

Current ready revision: `wzos-v2-staging-00006-2nx`, app image commit `cf14a40`. This includes the animated road-work background, report black-card presentation, Forms hub incident drafts, Schedule management drafts, dedicated Work Zone Report and creator-scoped immutable report revisions. Deployed from isolated `/tmp/wzos-v2-staging-SNTUgzHm`; historical checkout and production apps/DNS untouched. Authenticated browser saved and reopened a synthetic cloud report; anonymous session request returns 403. The authenticated Cloud Shell proxy is running on port 8080 for this session.

Cloud source documents and model conversation remain unavailable. Snapshot storage uses the same temporary staging SQLite database; snapshots are not durable cloud backups. New deployments/instance replacement can reset them. Local Git/GitHub include source and documentation, not local test records or agency document binaries. Docs-only follow-up commit does not require another image build.
