#!/usr/bin/env bash
# Existing-service release only. No new identity, secret, provider or SMS activation.
set -euo pipefail
umask 077
phase=${1:?gate/build/deploy}; root=${2:?private evidence directory}
candidate=c944173ed419ca664a3c11283af2c200ef8587bf
project=enterprise-gemma2; service=wzos-v2-accounts; region=us-central1
base=us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:f347f6901acb223b412ae729aa52afc47a1210804b861916ecfc18f46f5e3873
prior=wzos-v2-accounts-upgrade-live-bf9f524
revision=wzos-v2-accounts-mobile-c944173
cd "$root/source"
test "$(git rev-parse HEAD)" = "$candidate"
test "$(gcloud config get-value project 2>/dev/null)" = "$project"
if [[ "$phase" == gate ]]; then
 printf '%s\n' "$candidate" > "$root/tested-source.txt"
 node --test tests/*.test.cjs > "$root/node.log" 2>&1 && result=0 || result=$?
 printf '%s\n' "$result" > "$root/node.exit"
 bash scripts/test_postgres_native.sh > "$root/postgres.log" 2>&1 && result=0 || result=$?
 printf '%s\n' "$result" > "$root/postgres.exit"
 echo GATES_FINISHED; exit 0
fi
test "$(cat "$root/node.exit")" = 0
test "$(cat "$root/postgres.exit")" = 0
test "$(cat "$root/tested-source.txt")" = "$candidate"
if [[ "$phase" == build ]]; then
 gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/before.json"
 python3 "$root/check_release.py" preflight "$root"
 instance=$(cat "$root/sql-instance.txt")
 gcloud sql backups list --instance="${instance##*:}" --project="$project" --limit=5 --format=json > "$root/backups.json"
 cloud-sql-proxy "$instance" --address=127.0.0.1 --port=5544 > "$root/proxy.log" 2>&1 & proxy_pid=$!
 trap 'kill "$proxy_pid" 2>/dev/null || true' EXIT
 for attempt in $(seq 1 20); do grep -q 'Ready for new connections' "$root/proxy.log" && break; kill -0 "$proxy_pid"; sleep 1; done
 .venv-accounts-test/bin/python scripts/check_staging_schema.py --output "$root/schema.json" > "$root/schema.log" 2>&1
 python3 "$root/check_release.py" schema "$root"
 kill "$proxy_pid"; wait "$proxy_pid" 2>/dev/null || true; trap - EXIT
 printf 'FROM %s\nUSER root\nCOPY services /app/services\nRUN python -m compileall -q /app/services && chmod -R a+rX /app/services\nUSER wzos\n' "$base" > Dockerfile.mobile-release
 cat > cloudbuild.mobile-release.yaml <<'YAML'
steps:
- name: gcr.io/cloud-builders/docker
  args: ['build', '--platform', 'linux/amd64', '-f', 'Dockerfile.mobile-release', '-t', '${_IMAGE}', '.']
images: ['${_IMAGE}']
timeout: 600s
options:
  machineType: E2_MEDIUM
YAML
 printf '\n.venv-accounts-test/\n' >> .gcloudignore
 image=us-central1-docker.pkg.dev/$project/$project/wzos-v2-accounts:mobile-c944173
 gcloud builds submit --project="$project" --config=cloudbuild.mobile-release.yaml --substitutions="_IMAGE=$image" --async --format='value(id)' . > "$root/build-id.txt" 2> "$root/build-submit.log"
 echo BUILD_SUBMITTED; cat "$root/build-id.txt"; exit 0
fi
test "$phase" = deploy
gcloud builds describe "$(cat "$root/build-id.txt")" --project="$project" --format=json > "$root/build.json"
python3 "$root/check_release.py" build "$root"
image=$(cat "$root/immutable.txt")
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/predeploy.json"
python3 "$root/check_release.py" drift "$root"
gcloud run deploy "$service" --project="$project" --region="$region" --image="$image" --no-traffic --revision-suffix=mobile-c944173 --quiet > "$root/stage.log" 2>&1
gcloud run revisions describe "$revision" --project="$project" --region="$region" --format=json > "$root/revision.json"
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/staged.json"
python3 "$root/check_release.py" staged "$root"
gcloud run services update-traffic "$service" --project="$project" --region="$region" --to-revisions="$revision=100" --quiet > "$root/cutover.log" 2>&1
if ! python3 "$root/check_release.py" live "$root"; then
 gcloud run services update-traffic "$service" --project="$project" --region="$region" --to-revisions="$prior=100" --quiet > "$root/rollback.log" 2>&1
 echo MOBILE_RELEASE_ROLLED_BACK; exit 1
fi
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/live.json"
python3 "$root/check_release.py" traffic "$root"
echo MOBILE_RELEASE_DEPLOYED
