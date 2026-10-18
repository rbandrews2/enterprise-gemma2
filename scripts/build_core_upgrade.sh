#!/usr/bin/env bash
# Build the gated upgrade source on the accepted image. No deployment or billing writes.
set -euo pipefail
umask 077
root=$(cat "$HOME/wzos-core-upgrade-path.txt")
project=enterprise-gemma2
candidate=bf9f524
base=us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:edb4a3c4dde24cb6fe57d65ad79f1cfd611ab507d1d1bf03ea70e18f972e92ed
test "$(gcloud config get-value project 2>/dev/null)" = "$project"
test "$(cat "$root/validation-final.exit")" = 0
test "$(cat "$root/final-gate.exit")" = 0
cd "$root/source-final"
test "$(git rev-parse --short=7 HEAD)" = "$candidate"
test "$(git rev-parse HEAD)" = "$(cat "$root/final-tested-source.txt")"
# The disposable test environment is an explicitly excluded symlink, not source.
test -L .venv-accounts-test
test -z "$(git status --porcelain -- . ':!.venv-accounts-test')"
gcloud run services describe wzos-v2-accounts --region=us-central1 --project="$project" --format=json > "$root/build-before.json"
python3 - "$root" "$base" <<'PY'
import json,sys
from pathlib import Path
s=json.loads((Path(sys.argv[1])/'build-before.json').read_text())
assert s['spec']['template']['spec']['containers'][0]['image']==sys.argv[2], 'Live image drift'
assert [(t.get('revisionName'),t.get('percent')) for t in s['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-weather-hourly-1017',100)], 'Traffic drift'
assert s['metadata']['annotations']['run.googleapis.com/ingress']=='internal-and-cloud-load-balancing'
PY
printf 'FROM %s\nUSER root\nCOPY services /app/services\nRUN chmod -R a+rX /app/services\nUSER wzos\nRUN python -m compileall -q /app/services\n' "$base" > Dockerfile.core-upgrade
cat > cloudbuild.core-upgrade.yaml <<'YAML'
steps:
- name: gcr.io/cloud-builders/docker
  args: ['build', '--platform', 'linux/amd64', '-f', 'Dockerfile.core-upgrade', '-t', '${_IMAGE}', '.']
images: ['${_IMAGE}']
timeout: 600s
options:
  machineType: E2_MEDIUM
YAML
printf '\n.venv-accounts-test/\n' >> .gcloudignore
image=us-central1-docker.pkg.dev/$project/$project/wzos-v2-accounts:core-upgrade-$candidate
gcloud builds submit --project="$project" --config=cloudbuild.core-upgrade.yaml --substitutions="_IMAGE=$image" --async --format='value(id)' . > "$root/upgrade-build-id.txt" 2> "$root/upgrade-build.log"
printf 'CORE_UPGRADE_BUILD_SUBMITTED '
cat "$root/upgrade-build-id.txt"
