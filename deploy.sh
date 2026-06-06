#!/bin/bash
set -e

VERSION=$1

if [ -z "$VERSION" ]; then
  echo "Usage: ./deploy.sh v14"
  exit 1
fi

PROJECT_ID=$(gcloud config get-value project)

PROJECT_NUMBER=664870102667
MODEL_REGION=us-east1
ENDPOINT_ID=mg-endpoint-938bfbf2-2bc1-4937-a058-900bc5f31758
DEDICATED_DNS=mg-endpoint-938bfbf2-2bc1-4937-a058-900bc5f31758.us-east1-702117088368.prediction.vertexai.goog
PACKAGE_BUCKET=gemma_think
SERVICE_ACCOUNT_EMAIL=664870102667-compute@developer.gserviceaccount.com

if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
  echo "GOOGLE_MAPS_API_KEY is not set"
  exit 1
fi

python3 -m py_compile main.py

gcloud builds submit . \
  --tag gcr.io/$PROJECT_ID/gemma-assistant-api:$VERSION

gcloud run deploy gemma-assistant-api \
  --image=gcr.io/$PROJECT_ID/gemma-assistant-api:$VERSION \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=4Gi \
  --cpu=2 \
  --timeout=900 \
  --set-env-vars=VERTEX_ENDPOINT_URL=https://$DEDICATED_DNS/v1/projects/$PROJECT_NUMBER/locations/$MODEL_REGION/endpoints/$ENDPOINT_ID:rawPredict,PACKAGE_BUCKET=$PACKAGE_BUCKET,SERVICE_ACCOUNT_EMAIL=$SERVICE_ACCOUNT_EMAIL,GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY
