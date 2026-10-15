#!/usr/bin/env bash
# October15 approved synthetic pilot only. Remove exact grant even on failure.
set -euo pipefail
umask 077
evidence=${1:?Private evidence directory required}
url=${2:?Actual scanner origin required}
[[ $url =~ ^https://wzos-v2-scanner-[a-z0-9.-]+\.run\.app$ ]] || exit 2
mkdir -p "$evidence"; evidence=$(realpath "$evidence")
account=wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com
member=user:admin@workzoneos.org
role=roles/iam.serviceAccountOpenIdTokenCreator
test "$(gcloud auth list --filter=status:ACTIVE --format='value(account)')" = admin@workzoneos.org
expires=$(date -u -d '+15 minutes' +%Y-%m-%dT%H:%M:%SZ)
condition="expression=request.time < timestamp('$expires'),title=wzos-scanner-pilot-$(date -u +%Y%m%dT%H%M%SZ)"
printf '%s\n' "$condition" > "$evidence/condition.txt"
bound=0
cleanup() {
  result=$?; trap - EXIT
  if [[ $bound = 1 ]]; then
    if timeout 60 gcloud iam service-accounts remove-iam-policy-binding "$account" \
      --project=enterprise-gemma2 --member="$member" --role="$role" \
      --condition="$condition" --quiet --format=none > "$evidence/removal.log" 2>&1; then
      echo TEMPORARY_IDENTITY_ACCESS_REMOVED
    else
      echo "IDENTITY_ACCESS_REMOVAL_NEEDS_VERIFICATION expires=$expires"; result=1
    fi
  fi
  printf '%s\n' "$result" > "$evidence/test.exit"
  exit "$result"
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
bound=1
timeout 60 gcloud iam service-accounts add-iam-policy-binding "$account" \
  --project=enterprise-gemma2 --member="$member" --role="$role" \
  --condition="$condition" --quiet --format=none > "$evidence/grant.log" 2>&1
echo "TEMPORARY_IDENTITY_ACCESS_GRANTED expires=$expires"
# Allow propagation before the single test run, without extending the expiry.
sleep 90
timeout 210 python3 scripts/validate_scanner_pilot.py --url "$url" \
  --output "$evidence/acceptance.json" > "$evidence/acceptance.log" 2>&1
cat "$evidence/acceptance.log"
