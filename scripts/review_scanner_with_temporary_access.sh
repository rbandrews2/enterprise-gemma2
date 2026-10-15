#!/usr/bin/env bash
# Exact one-hour scan-only grant approved by Ray October15. No runtime deployment.
set -euo pipefail
umask 077
evidence=${1:?Private evidence directory required}
image=${WZOS_SCANNER_REVIEW_IMAGE:?Set exact approved immutable scanner image}
[[ $image =~ ^us-central1-docker\.pkg\.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-scanner@sha256:[0-9a-f]{64}$ ]] || exit 2
mkdir -p "$evidence"; evidence=$(realpath "$evidence")
role=projects/enterprise-gemma2/roles/wzosImageReview
member=serviceAccount:910004733138-compute@developer.gserviceaccount.com
expires=$(date -u -d '+1 hour' +%Y-%m-%dT%H:%M:%SZ)
condition="expression=request.time < timestamp('$expires'),title=wzos-image-review-$(date -u +%Y%m%dT%H%M%SZ)"
if [[ -n ${2:-} ]]; then
  condition=$(cat "$2")
  expires=$(python3 - "$condition" <<'CHECK'
import re,sys
from datetime import datetime,timezone,timedelta
m=re.fullmatch(r"expression=request.time < timestamp\('([0-9T:Z-]+)'\),title=wzos-image-review-[0-9]{8}T[0-9]{6}Z",sys.argv[1])
assert m
expires=datetime.fromisoformat(m[1].replace('Z','+00:00'))
assert timedelta(minutes=20)<expires-datetime.now(timezone.utc)<=timedelta(hours=1)
print(m[1])
CHECK
)
fi
printf '%s\n' "$condition" > "$evidence/condition.txt"
printf '%s\n' "$expires" > "$evidence/expires.txt"
bound=0
context=''
cleanup() {
  result=$?
  trap - EXIT
  if [[ $bound = 1 ]]; then
    if timeout 90 gcloud projects remove-iam-policy-binding enterprise-gemma2 --member="$member" --role="$role" --condition="$condition" --quiet --format=none > "$evidence/access-removal.log" 2>&1; then
      printf 'TEMPORARY_ACCESS_REMOVED\n'
    else
      printf 'TEMPORARY_ACCESS_REMOVAL_NEEDS_VERIFICATION expires=%s\n' "$expires"
      result=1
    fi
  fi
  case "$context" in /tmp/wzos-scanner-review.*) rm -rf -- "$context";; esac
  printf '%s\n' "$result" > "$evidence/review.exit"
  exit "$result"
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
existing=$(timeout 60 gcloud iam roles list --project=enterprise-gemma2 --filter="name=$role" --format='value(name)')
if [[ -z $existing ]]; then
  timeout 90 gcloud iam roles create wzosImageReview --project=enterprise-gemma2 --file=scanner-image-review-role.yaml --quiet --format=none
else
  test "$existing" = "$role"
fi
timeout 60 gcloud iam roles describe wzosImageReview --project=enterprise-gemma2 --format=json > "$evidence/role.json"
python3 - "$evidence/role.json" <<'PYCODE'
import json,sys
x=json.load(open(sys.argv[1]))
assert not x.get('deleted')
assert set(x['includedPermissions'])=={'ondemandscanning.scans.analyzePackages','ondemandscanning.scans.listVulnerabilities','ondemandscanning.operations.get','ondemandscanning.operations.wait'}
PYCODE
bound=1
timeout 90 gcloud projects add-iam-policy-binding enterprise-gemma2 --member="$member" --role="$role" --condition="$condition" --quiet --format=none > "$evidence/access-grant.log" 2>&1
printf 'TEMPORARY_SCAN_ACCESS_GRANTED expires=%s\n' "$expires"
# Give IAM policy propagation time; never extend the approved expiry.
sleep 90
context=$(mktemp -d /tmp/wzos-scanner-review.XXXXXXXX)
git archive HEAD cloudbuild.scanner-review.yaml | tar -x -C "$context"
timeout 90 gcloud builds submit "$context" --project=enterprise-gemma2 --region=us-central1 --config="$context/cloudbuild.scanner-review.yaml" --substitutions="_IMAGE=$image" --async --quiet --format='value(id)' > "$evidence/build.id"
build=$(cat "$evidence/build.id")
printf 'SCANNER_REVIEW_BUILD %s\n' "$build"
for ((i=0;i<36;i++)); do
  status=$(timeout 45 gcloud builds describe "$build" --project=enterprise-gemma2 --region=us-central1 --format='value(status)')
  case "$status" in QUEUED|WORKING|PENDING) sleep 30;; *) break;; esac
done
timeout 60 gcloud builds log "$build" --project=enterprise-gemma2 --region=us-central1 > "$evidence/build.log" 2>&1
printf 'SCANNER_REVIEW_BUILD_STATUS %s\n' "$status"
tail -n 14 "$evidence/build.log"
test "$status" = SUCCESS
