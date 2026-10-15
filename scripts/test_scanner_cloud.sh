#!/usr/bin/env bash
# Existing build service only. Minimal synthetic context; no app deploy or IAM.
set -euo pipefail
umask 077
evidence=${1:?Private evidence directory required}
image=${2:?Immutable reviewed scanner image required}
base=${3:?Pinned base required}
[[ $image =~ ^us-central1-docker\.pkg\.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-scanner@sha256:[0-9a-f]{64}$ ]] || exit 2
[[ $base =~ ^ubuntu:26\.04@sha256:[0-9a-f]{64}$ ]] || exit 2
test -z "$(git status --porcelain --untracked-files=no)"
revision=$(git rev-parse HEAD)
mkdir -p "$evidence"; evidence=$(realpath "$evidence")
context=$(mktemp -d /tmp/wzos-scanner-cloud-test.XXXXXXXX)
trap 'case "$context" in /tmp/wzos-scanner-cloud-test.*) rm -rf -- "$context";; esac' EXIT
git archive HEAD cloudbuild.scanner-test.yaml scripts/test_scanner_image.sh scripts/check_scanner_container.py | tar -x -C "$context"
printf '%s\n' "$revision" > "$evidence/harness-source.txt"
printf '%s\n' "$image" > "$evidence/image.txt"
gcloud builds submit "$context" --project=enterprise-gemma2 --region=us-central1 \
  --config="$context/cloudbuild.scanner-test.yaml" --async --quiet \
  --substitutions="_SOURCE=$revision,_IMAGE=$image,_BASE=$base" --format='value(id)' > "$evidence/build.id"
printf 'SCANNER_CLOUD_GATE_SUBMITTED %s\n' "$(cat "$evidence/build.id")"
