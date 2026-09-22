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

Prepared locally; live deployment verification pending.
