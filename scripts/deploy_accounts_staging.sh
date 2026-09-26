#!/usr/bin/env bash
# Approved persistent staging only. Prerequisites are provisioned separately.
set -euo pipefail
project=enterprise-gemma2
region=us-central1
service=wzos-v2-accounts
runtime="${service}@${project}.iam.gserviceaccount.com"
revision=$(git rev-parse HEAD)
image="${region}-docker.pkg.dev/${project}/enterprise-gemma2/${service}:${revision}"
if [[ -n $(git status --porcelain) ]]; then echo 'Commit changes before deploying.' >&2; exit 1; fi
context=$(mktemp -d -t wzos-accounts-build-XXXXXXXX)
git archive HEAD Dockerfile.accounts requirements-v2.txt requirements-accounts.txt services shared knowledge | tar -x -C "$context"
mv "$context/Dockerfile.accounts" "$context/Dockerfile"
gcloud builds submit "$context" --project="$project" --tag="$image" --quiet
gcloud run deploy "$service" --project="$project" --region="$region" \
  --image="$image" --service-account="$runtime" --no-allow-unauthenticated \
  --min-instances=0 --max-instances=2 --concurrency=8 --cpu=1 --memory=512Mi \
  --timeout=60 --cpu-throttling \
  --add-cloudsql-instances=enterprise-gemma2:us-central1:wzos-v2-staging-db \
  --set-env-vars=WZOS_ACCOUNT_WORKSPACE=1,WZOS_AUTH_PROJECT=enterprise-gemma2,WZOS_FILES_BUCKET=enterprise-gemma2-wzos-v2-files-staging \
  --set-secrets=WZOS_DATABASE_URL=wzos-v2-staging-database-url:latest,WZOS_AUTH_WEB_API_KEY=wzos-v2-staging-auth-web-key:latest --quiet
gcloud run services get-iam-policy "$service" --project="$project" --region="$region" --format=json > "$context/policy.json"
python3 - "$context/policy.json" <<'PY'
import json,sys
policy=json.load(open(sys.argv[1]))
assert not any(m in ('allUsers','allAuthenticatedUsers') for b in policy.get('bindings',[]) for m in b.get('members',[])), 'Unexpected public access'
PY
gcloud run services describe "$service" --project="$project" --region="$region" --format='value(status.url,status.latestReadyRevisionName)'
