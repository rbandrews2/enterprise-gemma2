#!/usr/bin/env bash
# Restricted, synthetic-only review environment. Never targets V1.
set -euo pipefail
project=enterprise-gemma2
region=us-central1
service=wzos-v2-staging
runtime=wzos-v2-staging@${project}.iam.gserviceaccount.com
revision=$(git rev-parse HEAD)
image="us-central1-docker.pkg.dev/${project}/enterprise-gemma2/${service}:${revision}"
if [[ -n $(git status --porcelain) ]]; then echo 'Commit changes before deploying.' >&2; exit 1; fi
if gcloud run services describe "$service" --project="$project" --region="$region" --format=json > /tmp/wzos-stage-service.json 2>/dev/null; then
  gcloud run services get-iam-policy "$service" --project="$project" --region="$region" --format=json > /tmp/wzos-stage-policy.json
  python3 - <<'PY'
import json
p=json.load(open('/tmp/wzos-stage-policy.json'))
assert not any(m in ('allUsers','allAuthenticatedUsers') for b in p.get('bindings',[]) for m in b.get('members',[])), 'Refusing to update publicly accessible staging'
s=json.load(open('/tmp/wzos-stage-service.json'))
assert s.get('metadata',{}).get('annotations',{}).get('run.googleapis.com/invoker-iam-disabled')!='true', 'IAM check must be enabled'
PY
fi
# This runtime identity receives no project roles, secrets or production data access.
gcloud iam service-accounts describe "$runtime" --project="$project" >/dev/null 2>&1 || gcloud iam service-accounts create wzos-v2-staging --project="$project" --display-name='WZOS V2 restricted staging'
context=$(mktemp -d -t wzos-v2-build-XXXXXXXX)
git archive HEAD Dockerfile.staging requirements-v2.txt services shared knowledge | tar -x -C "$context"
mv "$context/Dockerfile.staging" "$context/Dockerfile"
gcloud builds submit "$context" --project="$project" --tag="$image" --quiet
gcloud run deploy "$service" --project="$project" --region="$region" --image="$image" --service-account="$runtime" --no-allow-unauthenticated --min-instances=0 --max-instances=1 --concurrency=8 --cpu=1 --memory=512Mi --timeout=60 --update-env-vars=WZOS_PRIVATE_STAGING=1 --quiet
gcloud run services get-iam-policy "$service" --project="$project" --region="$region" --format=json > /tmp/wzos-stage-policy.json
python3 - <<'PY'
import json
p=json.load(open('/tmp/wzos-stage-policy.json'))
assert not any(m in ('allUsers','allAuthenticatedUsers') for b in p.get('bindings',[]) for m in b.get('members',[])), 'STOP: unexpected public staging binding'
PY
gcloud run services describe "$service" --project="$project" --region="$region" --format='value(status.url,status.latestReadyRevisionName)'
echo 'Test data resets on instance replacement. Access with gcloud run services proxy; no production DNS change.'
