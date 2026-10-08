#!/usr/bin/env bash
# Operator-only Cloud Shell preview; preserves the service's private IAM boundary.
# Refresh the explicit operator identity token before its one-hour expiration.
set -euo pipefail
worker=''
cleanup() {
  if [[ -n "$worker" ]]; then kill "$worker" 2>/dev/null || true; fi
}
trap 'cleanup; exit 0' INT TERM
trap cleanup EXIT
while true; do
  token="$(gcloud auth print-identity-token --project=enterprise-gemma2)"
  status=0
  timeout --signal=TERM --kill-after=10s 2700 \
    gcloud run services proxy wzos-v2-accounts \
    --project=enterprise-gemma2 --region=us-central1 --port=8080 \
    --token="$token" &
  worker=$!
  unset token
  wait "$worker" || status=$?
  worker=''
  if [[ "$status" != 124 && "$status" != 0 ]]; then
    printf 'Preview proxy exited (%s); retrying in five seconds.\n' "$status"
    sleep 5
  fi
done
