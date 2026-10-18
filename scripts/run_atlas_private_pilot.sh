#!/usr/bin/env bash
# Approved synthetic pilot only. Production Atlas remains disabled.
set -euo pipefail
umask 077
mode=${1:?Use run, guard or cleanup}
root=${2:?Private evidence directory required}
project=enterprise-gemma2
region=us-central1
service=wzos-atlas-inference
identity=wzos-atlas-inference@enterprise-gemma2.iam.gserviceaccount.com
test -d "$root"
test "$(gcloud config get-value project 2>/dev/null)" = "$project"
nonce=$(cat "$root/pilot-nonce.txt")
[[ "$nonce" =~ ^p[0-9]+-[0-9]+$ ]]

cleanup() {
 gcloud run services list --project="$project" --region="$region" --filter="metadata.name=$service" --format=json > "$root/cleanup-before.json"
 python3 - "$root" "$nonce" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);services=json.loads((p/'cleanup-before.json').read_text())
assert len(services)<=1
if services:
 s=services[0]
 assert s['metadata']['name']=='wzos-atlas-inference'
 assert s['metadata']['labels'].get('wzos-trial')=='20261018'
 assert s['metadata']['labels'].get('wzos-pilot')==sys.argv[2], 'Cleanup ownership mismatch'
 assert s['spec']['template']['spec']['serviceAccountName']=='wzos-atlas-inference@enterprise-gemma2.iam.gserviceaccount.com'
PY
 if test "$(python3 -c 'import json,sys;print(len(json.load(open(sys.argv[1]))))' "$root/cleanup-before.json")" = 1; then
  gcloud run services delete "$service" --project="$project" --region="$region" --quiet > "$root/cleanup-delete.log" 2>&1
 fi
 gcloud run services list --project="$project" --region="$region" --filter="metadata.name=$service" --format=json > "$root/cleanup-after.json"
 python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);assert json.loads((p/'cleanup-after.json').read_text())==[]
(p/'cleanup.verified').write_text('0\n')
print('ATLAS_PILOT_SERVICE_ABSENT_VERIFIED')
PY
}

case "$mode" in
 cleanup) cleanup; exit;;
 guard)
  sleep 3600
  for attempt in 1 2 3; do
   if timeout 150 bash "$0" cleanup "$root"; then exit 0; fi
   sleep 15
  done
  echo ATLAS_GUARD_CLEANUP_REQUIRES_ATTENTION
  exit 1;;
 run) ;;
 *) exit 2;;
esac

source_dir=$(cat "$root/source-path.txt")
test "$(git -C "$source_dir" rev-parse --short=7 HEAD)" = bf9f524
command -v setsid >/dev/null
gcloud run services describe wzos-v2-accounts --project="$project" --region="$region" --format=json > "$root/app-before.json"
gcloud run services list --project="$project" --region="$region" --filter="metadata.name=$service" --format=json > "$root/model-before.json"
python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);assert json.loads((p/'model-before.json').read_text())==[], 'Model already exists; review ownership'
s=json.loads((p/'app-before.json').read_text());env={e['name']:e.get('value') for e in s['spec']['template']['spec']['containers'][0]['env']}
assert env['WZOS_ATLAS_VLLM_ENABLED']=='0'
assert s['spec']['template']['spec']['serviceAccountName']=='wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com'
assert [(t.get('revisionName'),t.get('percent')) for t in s['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-upgrade-live-bf9f524',100)]
PY
(cd "$source_dir" && .venv-accounts-test/bin/python scripts/verify_atlas_artifacts.py) > "$root/artifacts.json"
# Independent fallback survives the foreground deploy/evaluator process.
nohup setsid bash "$0" guard "$root" > "$root/guard.log" 2>&1 < /dev/null &
guard_pid=$!
printf '%s\n' "$guard_pid" > "$root/guard.pid"
kill -0 "$guard_pid"
date -u +%FT%TZ > "$root/guard-installed-at.txt"
echo ATLAS_ONE_HOUR_GUARD_INSTALLED
on_exit() {
 result=$?
 trap - EXIT
 set +e
 timeout 150 bash "$0" cleanup "$root" > "$root/foreground-cleanup.log" 2>&1
 cleanup_result=$?
 if test "$cleanup_result" = 0; then
  # Only the independently created guard session and its owned sleep child.
  guard_group=$(ps -o pgid= -p "$guard_pid" | tr -d ' ')
  if test "$guard_group" = "$guard_pid"; then kill -- "-$guard_pid" 2>/dev/null; fi
  wait "$guard_pid" 2>/dev/null
 else
  echo ATLAS_CLEANUP_FAILED_GUARD_REMAINS_ACTIVE
  result=1
 fi
 printf '%s\n' "$result" > "$root/pilot.exit"
 exit "$result"
}
trap on_exit EXIT
export ATLAS_TRIAL_LABEL=20261018 ATLAS_TRIAL_NONCE="$nonce"
export ATLAS_MODEL_URI=gs://enterprise-gemma2-atlas-models-us-central1/gemma-4-31B-it/
export ATLAS_RUNTIME_IDENTITY="$identity" ATLAS_NETWORK=wzos-atlas-vpc ATLAS_SUBNET=wzos-atlas-us-central1
timeout 900 bash "$root/deploy-atlas.sh" --apply > "$root/deploy.log" 2>&1
gcloud run services add-iam-policy-binding "$service" --project="$project" --region="$region" \
 --member=serviceAccount:wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com \
 --role=roles/run.invoker --condition=None --quiet > "$root/invoker.log" 2>&1
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/model-ready.json"
gcloud run services get-iam-policy "$service" --project="$project" --region="$region" --format=json > "$root/model-iam.json"
python3 - "$root" "$nonce" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);s=json.loads((p/'model-ready.json').read_text());iam=json.loads((p/'model-iam.json').read_text())
assert s['metadata']['labels']['wzos-pilot']==sys.argv[2]
spec=s['spec']['template']['spec'];c=spec['containers'][0]
assert spec['serviceAccountName']=='wzos-atlas-inference@enterprise-gemma2.iam.gserviceaccount.com'
assert c['image'].endswith('@sha256:3fbc0e08c46e7736145c9effbcc8839682c80b15b413335146f4428fc3523c8a')
assert c['resources']['limits']['cpu']=='20' and c['resources']['limits']['memory']=='80Gi'
assert c['resources']['limits']['nvidia.com/gpu']=='1'
assert not any(e.get('valueFrom') for e in c.get('env',[])), 'Unexpected secret binding'
assert s['spec']['template']['metadata']['annotations']['autoscaling.knative.dev/maxScale']=='1'
assert not any(m in ('allUsers','allAuthenticatedUsers') for b in iam.get('bindings',[]) for m in b.get('members',[]))
assert any(b['role']=='roles/run.invoker' and 'serviceAccount:wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com' in b.get('members',[]) for b in iam.get('bindings',[]))
(p/'model-url.txt').write_text(s['status']['url'])
print('ATLAS_PRIVATE_MODEL_CONFIG_VERIFIED')
PY
cd "$source_dir"
timeout 650 .venv-accounts-test/bin/python scripts/evaluate_atlas_vllm.py --live \
 --url="$(cat "$root/model-url.txt")" --limit=8 --output="$root/evaluation.jsonl" > "$root/evaluation.log" 2>&1
echo ATLAS_SYNTHETIC_EVALUATION_FINISHED
