#!/usr/bin/env bash
# Read existing configuration/backup metadata only. No secrets, data or IAM changes.
set -euo pipefail
umask 077
root=${1:?private evidence directory}
test -d "$root"
test "$(gcloud config get-value project 2>/dev/null)" = enterprise-gemma2
capture() {
 local name=$1; shift
 if "$@" > "$root/$name.json" 2> "$root/$name.stderr"; then
  printf 0 > "$root/$name.exit"
 else
  printf '%s' "$?" > "$root/$name.exit"
 fi
}
capture live-service gcloud run services describe wzos-v2-accounts --project=enterprise-gemma2 --region=us-central1 --format=json
capture run-services gcloud run services list --project=enterprise-gemma2 --region=us-central1 --format=json
capture schedulers gcloud scheduler jobs list --project=enterprise-gemma2 --location=us-central1 --format=json
capture sql-instance gcloud sql instances describe wzos-v2-staging-db --project=enterprise-gemma2 --format=json
capture backups gcloud sql backups list --instance=wzos-v2-staging-db --project=enterprise-gemma2 --limit=5 --format=json
capture file-bucket gcloud storage buckets describe gs://enterprise-gemma2-wzos-v2-files-staging --format=json
echo READ_ONLY_PRELAUNCH_SNAPSHOT_FINISHED
