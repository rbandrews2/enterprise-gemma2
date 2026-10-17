#!/usr/bin/env bash
# Build only: exact weather candidate after its focused gate. No deploy or policy activation.
set -euo pipefail
umask 077
project=enterprise-gemma2
service=wzos-v2-accounts
region=us-central1
base=us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:14b89663d97726b12f5173163ba31aa94ebf8bb7be85da3c4fb2be06fda51da1
source_commit=${1:?Exact tested candidate commit required}
[[ "$source_commit" =~ ^[0-9a-f]{40}$ ]]
short=${source_commit:0:7}
root=$(cat "$HOME/wzos-weather-path.txt")
test "$(gcloud config get-value project 2>/dev/null)" = "$project"
gcloud auth print-access-token >/dev/null
for attempt in $(seq 1 30); do test ! -f "$root/gate.exit" || break; sleep 5; done
test "$(cat "$root/gate.exit")" = 0
cd "$root/source"
test "$(git rev-parse HEAD)" = "$source_commit"
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/before.json"
python3 - "$root" "$base" <<'PY'
import json,sys
from pathlib import Path
s=json.loads((Path(sys.argv[1])/'before.json').read_text())
assert s['spec']['template']['spec']['containers'][0]['image']==sys.argv[2], 'Live image drift: review first'
t=[t for t in s['status']['traffic'] if t.get('percent')]
assert len(t)==1 and t[0]['percent']==100 and t[0]['revisionName']=='wzos-v2-accounts-brand-4e281c6', 'Traffic drift: review first'
assert s['metadata']['annotations']['run.googleapis.com/ingress']=='internal-and-cloud-load-balancing'
PY
printf 'FROM %s\nUSER root\nCOPY services /app/services\nCOPY scripts/poll_weather.py /app/scripts/poll_weather.py\nRUN chmod -R a+rX /app/services /app/scripts/poll_weather.py\nUSER wzos\n' "$base" > Dockerfile.module-flow
cat > cloudbuild.module-flow.yaml <<'YAML'
steps:
- name: gcr.io/cloud-builders/docker
  args: ['build', '--platform', 'linux/amd64', '-f', 'Dockerfile.module-flow', '-t', '${_IMAGE}', '.']
images: ['${_IMAGE}']
timeout: 600s
options:
  machineType: E2_MEDIUM
YAML
printf '\n.venv-accounts-test/\n' >> .gcloudignore
image=us-central1-docker.pkg.dev/$project/$project/wzos-v2-accounts:weather-$short
if ! gcloud builds submit --project="$project" --config=cloudbuild.module-flow.yaml --substitutions="_IMAGE=$image" --async --format='value(id)' . > "$root/build-id.txt" 2> "$root/build.log"; then tail -n 12 "$root/build.log"; exit 1; fi
build_id=$(cat "$root/build-id.txt")
for attempt in $(seq 1 70); do
 gcloud builds describe "$build_id" --project="$project" --format=json > "$root/build.json"
 status=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["status"])' "$root/build.json")
 case "$status" in SUCCESS) break;; QUEUED|WORKING|PENDING) sleep 10;; *) echo "BUILD_FAILED $status"; exit 1;; esac
done
python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);b=json.loads((p/'build.json').read_text());assert b['status']=='SUCCESS'
(p/'digest.txt').write_text(b['results']['images'][0]['digest'])
PY
immutable="${image%:*}@$(cat "$root/digest.txt")"
printf '%s\n' "$immutable" > "$root/immutable.txt"
printf 'WEATHER_BUILD_READY %s\n' "$immutable"
