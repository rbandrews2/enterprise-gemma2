#!/bin/bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-enterprise-gemma2}"
SERVICE_NAME="${SERVICE_NAME:-gemma-assistant-api}"
REGION="${REGION:-us-central1}"
DOMAIN="${DOMAIN:-workzoneos.org}"

gcloud config set project "${PROJECT_ID}" >/dev/null
PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")"
IAP_SERVICE_AGENT="service-${PROJECT_NUMBER}@gcp-sa-iap.iam.gserviceaccount.com"

if command -v curl >/dev/null 2>&1; then
  ACCESS_TOKEN="$(gcloud auth print-access-token)"
  curl -fsS -X POST \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{}" \
    "https://serviceusage.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/services/iap.googleapis.com:generateServiceIdentity" \
    >/dev/null || true
fi

for member in allUsers allAuthenticatedUsers "domain:${DOMAIN}"; do
  gcloud run services remove-iam-policy-binding "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --member="${member}" \
    --role="roles/run.invoker" \
    --condition=None >/dev/null 2>&1 || true
done

gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --member="serviceAccount:${IAP_SERVICE_AGENT}" \
  --role="roles/run.invoker" \
  --condition=None

echo "Cloud Run invoker access is restricted to IAP for ${SERVICE_NAME}."
echo "Configure IAP to allow users in ${DOMAIN}."
