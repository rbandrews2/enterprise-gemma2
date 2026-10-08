#!/usr/bin/env bash
# Operator-only Cloud Shell preview; preserves the service's private IAM boundary.
# Refresh the explicit operator identity token before its one-hour expiration.
set -euo pipefail
proxy_bin='/usr/lib/google-cloud-sdk/bin/cloud-run-proxy'
[[ -x "$proxy_bin" ]] || { printf 'Official Cloud SDK proxy is not installed.\n' >&2; exit 1; }
host="$(gcloud run services describe wzos-v2-accounts --project=enterprise-gemma2 --region=us-central1 --format='value(status.url)')"
[[ "$host" == https://*.run.app ]] || { printf 'Unexpected staging service URL.\n' >&2; exit 1; }
host="${host#https://}"
worker=''
cleanup() {
  if [[ -n "$worker" ]]; then kill "$worker" 2>/dev/null || true; fi
}
trap 'cleanup; exit 0' INT TERM
trap cleanup EXIT
while true; do
  token="$(gcloud auth print-identity-token --project=enterprise-gemma2)"
  status=0
  "$proxy_bin" -host "$host" -bind '127.0.0.1:8080' \
    -server-up-time '45m' -token "$token" &
  worker=$!
  unset token
  wait "$worker" || status=$?
  worker=''
  if [[ "$status" != 0 ]]; then
    printf 'Preview proxy exited (%s); retrying in five seconds.\n' "$status"
    sleep 5
  fi
done
