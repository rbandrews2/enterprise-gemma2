#!/bin/bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-enterprise-gemma2}"
SERVICE_NAME="${SERVICE_NAME:-gemma-assistant-api}"
REGION="${REGION:-us-central1}"
SECRET_NAME="${GOOGLE_MAPS_API_KEY_SECRET:-GOOGLE_MAPS_API_KEY}"
PROJECT_NUMBER="${PROJECT_NUMBER:-$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")}"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_EMAIL:-${PROJECT_NUMBER}-compute@developer.gserviceaccount.com}"

if [ -z "${PROJECT_ID}" ]; then
  echo "No active GCP project found. Run: gcloud config set project PROJECT_ID"
  exit 1
fi

gcloud config set project "${PROJECT_ID}" >/dev/null

if [ -z "${GOOGLE_MAPS_API_KEY:-}" ]; then
  echo "GOOGLE_MAPS_API_KEY is not set in the shell. Export it before running this script."
  exit 1
fi

gcloud services enable secretmanager.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  --project="${PROJECT_ID}"

if ! gcloud secrets describe "${SECRET_NAME}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud secrets create "${SECRET_NAME}" \
    --project="${PROJECT_ID}" \
    --replication-policy=automatic
fi

printf "%s" "${GOOGLE_MAPS_API_KEY}" | gcloud secrets versions add "${SECRET_NAME}" \
  --project="${PROJECT_ID}" \
  --data-file=-

gcloud secrets add-iam-policy-binding "${SECRET_NAME}" \
  --project="${PROJECT_ID}" \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/secretmanager.secretAccessor" >/dev/null

gcloud run services update "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --update-secrets="GOOGLE_MAPS_API_KEY=${SECRET_NAME}:latest" \
  --min-instances=0 \
  --max-instances=10 \
  --cpu-throttling

echo "Secret Manager is configured for ${SERVICE_NAME} in ${PROJECT_ID}/${REGION}."
