#!/usr/bin/env bash
# Isolated public-document research only. No WZOS app identity or database access.
set -euo pipefail
project=enterprise-gemma2
region=us-central1
job=wzos-atlas-research
bucket=enterprise-gemma2-atlas-research
runtime=wzos-atlas-research@${project}.iam.gserviceaccount.com
scheduler=wzos-research-scheduler@${project}.iam.gserviceaccount.com
image=${1:?Pass the verified research image digest}
[[ "$image" == us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/atlas-research@sha256:* ]]
[[ $(gcloud config get-value project) == "$project" ]]
gcloud storage buckets describe "gs://$bucket" >/dev/null 2>&1 || gcloud storage buckets create "gs://$bucket" --project="$project" --location="$region" --uniform-bucket-level-access --public-access-prevention
gcloud iam service-accounts describe "$runtime" --project="$project" >/dev/null 2>&1 || gcloud iam service-accounts create wzos-atlas-research --project="$project" --display-name='Atlas public-source research only'
gcloud iam service-accounts describe "$scheduler" --project="$project" >/dev/null 2>&1 || gcloud iam service-accounts create wzos-research-scheduler --project="$project" --display-name='Atlas daily research invocation only'
gcloud storage buckets add-iam-policy-binding "gs://$bucket" --member="serviceAccount:$runtime" --role=roles/storage.objectUser
gcloud run jobs deploy "$job" --project="$project" --region="$region" --image="$image" --service-account="$runtime" --tasks=1 --parallelism=1 --cpu=1 --memory=1Gi --task-timeout=600s --max-retries=0 --set-env-vars="ATLAS_RESEARCH_BUCKET=$bucket"
gcloud run jobs add-iam-policy-binding "$job" --project="$project" --region="$region" --member="serviceAccount:$scheduler" --role=roles/run.invoker
# Validate one real run before enabling the schedule.
gcloud run jobs execute "$job" --project="$project" --region="$region" --wait
gcloud scheduler jobs create http wzos-atlas-research-daily --project="$project" --location="$region" --schedule='15 3 * * *' --time-zone=America/New_York --uri="https://run.googleapis.com/v2/projects/$project/locations/$region/jobs/$job:run" --http-method=POST --oauth-service-account-email="$scheduler" --oauth-token-scope=https://www.googleapis.com/auth/cloud-platform --message-body='{}' --headers=Content-Type=application/json --max-retry-attempts=0 --attempt-deadline=180s
gcloud scheduler jobs describe wzos-atlas-research-daily --project="$project" --location="$region" --format='yaml(state,schedule,timeZone,httpTarget.uri,httpTarget.oauthToken.serviceAccountEmail)'
gcloud storage cat "gs://$bucket/latest.json" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps({"status":d["status"],"checked_at":d["checked_at"],"results":[{"url":r.get("url"),"status":r["status"],"error":r.get("error")} for r in d["results"]]},indent=2))'
