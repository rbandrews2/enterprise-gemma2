#!/usr/bin/env bash
# Synthetic-only guarded pilot. New access/workload approvals must be recorded first.
set -euo pipefail
umask 077
mode=${1:?run/guard/cleanup}; root=${2:?Private evidence directory}
project=enterprise-gemma2; region=us-central1
service=wzos-atlas-inference; job=wzos-field-voice-pilot
nonce=$(cat "$root/pilot-nonce.txt")
[[ "$nonce" =~ ^v20261018-[0-9]+$ ]]
test "$(gcloud config get-value project 2>/dev/null)" = "$project"

cleanup_job() {
 gcloud run jobs list --project="$project" --region="$region" --filter="metadata.name=$job" --format=json > "$root/job-cleanup-before.json"
 python3 - "$root" "$nonce" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); rows=json.loads((p/'job-cleanup-before.json').read_text()); assert len(rows)<=1
if rows: assert rows[0]['metadata']['labels'].get('wzos-pilot')==sys.argv[2], 'Job ownership mismatch'
PY
 if test "$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))))' "$root/job-cleanup-before.json")" = 1; then
  gcloud run jobs delete "$job" --project="$project" --region="$region" --quiet > "$root/job-delete.log" 2>&1
 fi
}
cleanup() {
 cleanup_job
 gcloud run services list --project="$project" --region="$region" --filter="metadata.name=$service" --format=json > "$root/model-cleanup-before.json"
 python3 - "$root" "$nonce" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);rows=json.loads((p/'model-cleanup-before.json').read_text());assert len(rows)<=1
if rows:
 s=rows[0];assert s['metadata']['labels'].get('wzos-pilot')==sys.argv[2], 'Model ownership mismatch'
 assert s['spec']['template']['spec']['serviceAccountName']=='wzos-atlas-inference@enterprise-gemma2.iam.gserviceaccount.com'
PY
 if test "$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))))' "$root/model-cleanup-before.json")" = 1; then
  gcloud run services delete "$service" --project="$project" --region="$region" --quiet > "$root/model-delete.log" 2>&1
 fi
 gcloud run services list --project="$project" --region="$region" --filter="metadata.name=$service" --format=json > "$root/model-cleanup-after.json"
 gcloud run jobs list --project="$project" --region="$region" --filter="metadata.name=$job" --format=json > "$root/job-cleanup-after.json"
 python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);assert json.loads((p/'model-cleanup-after.json').read_text())==[];assert json.loads((p/'job-cleanup-after.json').read_text())==[]
(p/'cleanup.verified').write_text('0\n');print('FIELD_VOICE_PILOT_CLEANUP_VERIFIED')
PY
}
case "$mode" in
 cleanup) cleanup; exit;;
 guard) sleep 3600; for attempt in 1 2 3; do timeout 180 bash "$0" cleanup "$root" && exit 0; sleep 15; done; exit 1;;
 run) ;;
 *) exit 2;;
esac
for approved in model-approved job-approved speech-setup.verified; do test -f "$root/$approved"; done
test "$(cat "$root/node.exit")" = 0; test "$(cat "$root/postgres.exit")" = 0
source_dir="$root/source"
test "$(git -C "$source_dir" rev-parse HEAD)" = "$(cat "$root/source-commit.txt")"
image=$(cat "$root/job-image.txt")
[[ "$image" =~ ^us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-field-voice-pilot@sha256:[a-f0-9]{64}$ ]]
gcloud run services list --project="$project" --region="$region" --filter="metadata.name=$service" --format=json > "$root/model-preflight.json"
gcloud run jobs list --project="$project" --region="$region" --filter="metadata.name=$job" --format=json > "$root/job-preflight.json"
python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);assert json.loads((p/'model-preflight.json').read_text())==[];assert json.loads((p/'job-preflight.json').read_text())==[]
PY
"$source_dir/.venv-accounts-test/bin/python" "$source_dir/scripts/verify_atlas_artifacts.py" > "$root/model-artifacts.json"
nohup setsid bash "$0" guard "$root" > "$root/guard.log" 2>&1 < /dev/null & guard_pid=$!
printf '%s\n' "$guard_pid" > "$root/guard.pid"; kill -0 "$guard_pid"
on_exit() {
 result=$?; trap - EXIT; set +e
 timeout 180 bash "$0" cleanup "$root" > "$root/cleanup.log" 2>&1; cleaned=$?
 if test "$cleaned" = 0; then
  group=$(ps -o pgid= -p "$guard_pid" | tr -d ' ')
  if test "$group" = "$guard_pid"; then kill -- "-$guard_pid" 2>/dev/null; fi
  wait "$guard_pid" 2>/dev/null
 else result=1; echo CLEANUP_FAILED_GUARD_REMAINS; fi
 printf '%s\n' "$result" > "$root/pilot.exit"; exit "$result"
}
trap on_exit EXIT
export ATLAS_TRIAL_LABEL=20261018 ATLAS_TRIAL_NONCE="$nonce"
export ATLAS_MODEL_URI=gs://enterprise-gemma2-atlas-models-us-central1/gemma-4-31B-it/
export ATLAS_RUNTIME_IDENTITY=wzos-atlas-inference@enterprise-gemma2.iam.gserviceaccount.com
export ATLAS_NETWORK=wzos-atlas-vpc ATLAS_SUBNET=wzos-atlas-us-central1
timeout 900 bash "$source_dir/scripts/deploy_atlas_vllm.sh" --apply > "$root/model-deploy.log" 2>&1
gcloud run services add-iam-policy-binding "$service" --project="$project" --region="$region" \
 --member=serviceAccount:wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com --role=roles/run.invoker --condition=None --quiet > "$root/model-invoker.log" 2>&1
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/model-ready.json"
gcloud run services get-iam-policy "$service" --project="$project" --region="$region" --format=json > "$root/model-iam.json"
python3 - "$root" "$nonce" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);s=json.loads((p/'model-ready.json').read_text()); iam=json.loads((p/'model-iam.json').read_text())
assert s['metadata']['labels']['wzos-pilot']==sys.argv[2]
spec=s['spec']['template']['spec'];c=spec['containers'][0]
assert spec['serviceAccountName']=='wzos-atlas-inference@enterprise-gemma2.iam.gserviceaccount.com'
assert c['image'].endswith('@sha256:3fbc0e08c46e7736145c9effbcc8839682c80b15b413335146f4428fc3523c8a')
assert c['resources']['limits']=={'cpu':'20','memory':'80Gi','nvidia.com/gpu':'1'}
assert '--disable-log-requests' in c['args']
assert not any(e.get('valueFrom') for e in c.get('env',[]))
assert s['spec']['template']['metadata']['annotations']['autoscaling.knative.dev/maxScale']=='1'
assert not any(m in ('allUsers','allAuthenticatedUsers') for b in iam.get('bindings',[]) for m in b.get('members',[]))
members={m for b in iam.get('bindings',[]) if b['role']=='roles/run.invoker' for m in b.get('members',[])}
assert members=={'serviceAccount:wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com'}
(p/'model-url.txt').write_text(s['status']['url']); print('FIELD_VOICE_PRIVATE_MODEL_VERIFIED')
PY
origin=$(cat "$root/model-url.txt")
timeout 120 gcloud run jobs create "$job" --project="$project" --region="$region" --image="$image" \
 --service-account=wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com --labels="wzos-pilot=$nonce" \
 --tasks=1 --parallelism=1 --max-retries=0 --task-timeout=900s --cpu=1 --memory=512Mi \
 --set-env-vars="WZOS_FIELD_VOICE_MODEL_URL=$origin" --quiet > "$root/job-create.log" 2>&1
gcloud run jobs describe "$job" --project="$project" --region="$region" --format=json > "$root/job-config.json"
python3 - "$root" "$image" "$origin" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);j=json.loads((p/'job-config.json').read_text());outer=j['spec']['template']['spec'];s=outer['template']['spec'];c=s['containers'][0]
assert outer['taskCount']==1 and outer.get('parallelism',1)==1
assert s['serviceAccountName']=='wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com'
assert s['maxRetries']==0 and str(s['timeoutSeconds'])=='900'
assert c['image']==sys.argv[2] and not c.get('volumeMounts') and not s.get('volumes')
assert c.get('env')==[{'name':'WZOS_FIELD_VOICE_MODEL_URL','value':sys.argv[3]}]
assert c['resources']['limits']['cpu'] in ('1','1000m') and c['resources']['limits']['memory']=='512Mi'
print('FIELD_VOICE_JOB_CONFIG_VERIFIED')
PY
timeout 1000 gcloud run jobs execute "$job" --project="$project" --region="$region" --wait --quiet --format=json > "$root/execution.json" 2> "$root/execution.log"
execution=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["metadata"]["name"])' "$root/execution.json")
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=$job AND labels.\"run.googleapis.com/execution_name\"=$execution" \
 --project="$project" --freshness=30m --order=asc --limit=200 --format=json > "$root/job-logs.json"
python3 - "$root" "$execution" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);e=json.loads((p/'execution.json').read_text());assert e['status'].get('succeededCount')==1 and not e['status'].get('failedCount')
rows=[r for r in json.loads((p/'job-logs.json').read_text()) if r.get('labels',{}).get('run.googleapis.com/execution_name')==sys.argv[2] and r.get('logName','').endswith('stdout')]
values=[r['jsonPayload'] for r in rows if 'jsonPayload' in r]
value=values[0] if len(values)==1 else json.loads('\n'.join(r.get('textPayload','') for r in rows))
assert value['status']=='PASS' and value['mode']=='live' and value['synthetic_only']
assert value['speech_requests']==10 and 8<=value['model_requests']<=10 and value['sms_sent']==0
assert len(value['checks'])==10 and value['raw_audio_or_transcript_logged'] is False
(p/'pilot-result.json').write_text(json.dumps(value,indent=2)); print('FIELD_VOICE_LIVE_PILOT_PASS speech=10 model='+str(value['model_requests'])+' sms=0')
PY
