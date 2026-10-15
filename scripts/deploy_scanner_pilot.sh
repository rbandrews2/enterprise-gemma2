#!/usr/bin/env bash
# Exact private synthetic pilot approved October15; no public app/config changes.
set -euo pipefail
umask 077
evidence=${1:?Private evidence directory required}
mkdir -p "$evidence"; evidence=$(realpath "$evidence")
project=enterprise-gemma2
region=us-central1
service=wzos-v2-scanner
runtime=wzos-v2-scanner-runtime@enterprise-gemma2.iam.gserviceaccount.com
caller=wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com
image=us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-scanner@sha256:6190d698438aff6ab92ea9e8de8acce9f9149cd1e94c7e374ab5e0a95903da16
# Fail rather than replace an unexpected existing service or identity.
services=$(gcloud run services list --project="$project" --region="$region" --filter="metadata.name=$service" --format='value(metadata.name)')
test -z "$services"
identities=$(gcloud iam service-accounts list --project="$project" --filter="email=$runtime" --format='value(email)')
test -z "$identities"
gcloud iam service-accounts create wzos-v2-scanner-runtime --project="$project" \
  --display-name='WZOS private scanner runtime' --quiet
# Bootstrap accepts no valid caller tokens. No invoker grant exists yet. Replace
# audience with Google's returned canonical URL before granting the app invocation.
gcloud run deploy "$service" --project="$project" --region="$region" \
  --image="$image" --service-account="$runtime" --execution-environment=gen2 \
  --no-allow-unauthenticated --ingress=all --cpu=1 --memory=4Gi --concurrency=1 \
  --min=0 --max=1 --min-instances=0 --max-instances=1 --cpu-throttling \
  --timeout=60 --port=8080 \
  --startup-probe=tcpSocket.port=8080,initialDelaySeconds=0,failureThreshold=24,timeoutSeconds=5,periodSeconds=10 \
  --set-env-vars="WZOS_SCANNER_AUDIENCE=https://bootstrap.invalid.run.app,WZOS_SCANNER_CALLER=$caller" \
  --labels=wzos-purpose=synthetic-scanner-pilot --quiet > "$evidence/deploy.log" 2>&1
url=$(gcloud run services describe "$service" --project="$project" --region="$region" --format='value(status.url)')
[[ $url =~ ^https://[a-z0-9.-]+\.run\.app$ ]]
printf '%s\n' "$url" > "$evidence/url.txt"
gcloud run services update "$service" --project="$project" --region="$region" \
  --update-env-vars="WZOS_SCANNER_AUDIENCE=$url" --quiet > "$evidence/audience.log" 2>&1
gcloud run services add-iam-policy-binding "$service" --project="$project" --region="$region" \
  --member="serviceAccount:$caller" --role=roles/run.invoker --quiet --format=none > "$evidence/invoker.log" 2>&1
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$evidence/service.json"
gcloud run services get-iam-policy "$service" --project="$project" --region="$region" --format=json > "$evidence/iam.json"
printf 'PRIVATE_SCANNER_PILOT_DEPLOYED %s\n' "$url"
