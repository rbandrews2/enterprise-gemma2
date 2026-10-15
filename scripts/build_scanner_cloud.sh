#!/usr/bin/env bash
# Build only, in existing approved project/registry. No deployment or IAM change.
set -euo pipefail
umask 077
evidence=${1:?Private evidence directory required}
base=${2:?Inspected official Ubuntu base digest required}
[[ $base =~ ^ubuntu:26\.04@sha256:[0-9a-f]{64}$ ]] || exit 2
# Explicit git archive allowlist excludes untracked test venvs and local data.
test -z "$(git status --porcelain --untracked-files=no)"
revision=$(git rev-parse HEAD)
image="us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-scanner:$revision"
mkdir -p "$evidence"; evidence=$(realpath "$evidence")
context=$(mktemp -d /tmp/wzos-scanner-cloud-build.XXXXXXXX)
trap 'case "$context" in /tmp/wzos-scanner-cloud-build.*) rm -rf -- "$context";; esac' EXIT
git archive HEAD cloudbuild.scanner.yaml Dockerfile.scanner requirements-scanner.txt \
  services/__init__.py services/workspace_preview/__init__.py \
  services/workspace_preview/archive_policy.py services/workspace_preview/clamd_scanner.py \
  services/workspace_preview/security.py services/workspace_preview/scanner_transport.py \
  services/workspace_preview/scanner_service.py services/workspace_preview/scanner_runtime.py | tar -x -C "$context"
printf '%s\n' "$revision" > "$evidence/source.txt"
printf '%s\n' "$base" > "$evidence/base.txt"
printf '%s\n' "$image" > "$evidence/image-tag.txt"
gcloud builds submit "$context" --project=enterprise-gemma2 --region=us-central1 \
  --config="$context/cloudbuild.scanner.yaml" --async --quiet \
  --substitutions="_BASE_IMAGE=$base,_IMAGE=$image" --format='value(id)' > "$evidence/build.id"
printf 'SCANNER_BUILD_SUBMITTED %s\n' "$(cat "$evidence/build.id")"
