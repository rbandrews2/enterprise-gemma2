#!/bin/bash
set -e

VERSION=$1

if [ -z "$VERSION" ]; then
  echo "Usage: ./deploy.sh v18"
  exit 1
fi

PROJECT_ID="${PROJECT_ID:-enterprise-gemma2}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
gcloud config set project "$PROJECT_ID" >/dev/null

PROJECT_NUMBER="${PROJECT_NUMBER:-$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")}"
REGION=us-central1
AR_REPOSITORY="${AR_REPOSITORY:-enterprise-gemma2}"
IMAGE_NAME=gemma-assistant-api
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPOSITORY}/${IMAGE_NAME}:${VERSION}"
MODEL_REGION=us-east1
ENDPOINT_ID=mg-endpoint-938bfbf2-2bc1-4937-a058-900bc5f31758
DEDICATED_DNS=mg-endpoint-938bfbf2-2bc1-4937-a058-900bc5f31758.us-east1-702117088368.prediction.vertexai.goog
PACKAGE_BUCKET=gemma_think
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_EMAIL:-${PROJECT_NUMBER}-compute@developer.gserviceaccount.com}"
VERTEX_IMAGE_REGION="${VERTEX_IMAGE_REGION:-us-central1}"
VERTEX_IMAGE_MODEL="${VERTEX_IMAGE_MODEL:-imagen-4.0-generate-001}"
AUTH_PROVIDER="${AUTH_PROVIDER:-iap}"
ALLOWED_EMAIL_DOMAIN="${ALLOWED_EMAIL_DOMAIN:-workzoneos.org}"

"$PYTHON_BIN" -m py_compile main.py

gcloud artifacts repositories describe "$AR_REPOSITORY" \
  --project="$PROJECT_ID" \
  --location="$REGION" >/dev/null 2>&1 || \
gcloud artifacts repositories create "$AR_REPOSITORY" \
  --project="$PROJECT_ID" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Docker images for ${IMAGE_NAME}"

gcloud builds submit . \
  --project="$PROJECT_ID" \
  --tag "$IMAGE_URI"

gcloud run deploy gemma-assistant-api \
  --image="$IMAGE_URI" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --platform=managed \
  --no-allow-unauthenticated \
  --memory=4Gi \
  --cpu=2 \
  --timeout=900 \
  --max-instances=10 \
  --min-instances=0 \
  --cpu-throttling \
  --set-env-vars=VERTEX_ENDPOINT_URL=https://$DEDICATED_DNS/v1/projects/$PROJECT_NUMBER/locations/$MODEL_REGION/endpoints/$ENDPOINT_ID:rawPredict,PACKAGE_BUCKET=$PACKAGE_BUCKET,SERVICE_ACCOUNT_EMAIL=$SERVICE_ACCOUNT_EMAIL,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,VERTEX_IMAGE_REGION=$VERTEX_IMAGE_REGION,VERTEX_IMAGE_MODEL=$VERTEX_IMAGE_MODEL,AUTH_PROVIDER=$AUTH_PROVIDER,ALLOWED_EMAIL_DOMAIN=$ALLOWED_EMAIL_DOMAIN \
  --set-secrets=GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY:latest
