#!/usr/bin/env bash
# Four synthetic recognition calls only. Requires exact-image/identity approval.
set -euo pipefail
umask 077
mode=${1:?run/cleanup}; root=${2:?Private evidence directory}
project=enterprise-gemma2; region=us-central1; job=wzos-field-voice-speech-pilot
nonce=$(cat "$root/speech-pilot-nonce.txt")
[[ "$nonce" =~ ^s20261018-[0-9]+$ ]]
test "$(gcloud config get-value project 2>/dev/null)" = "$project"
cleanup() {
 gcloud run jobs list --project="$project" --region="$region" --filter="metadata.name=$job" --format=json > "$root/speech-cleanup-before.json"
 python3 - "$root" "$nonce" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); rows=json.loads((p/'speech-cleanup-before.json').read_text()); assert len(rows)<=1
if rows: assert rows[0]['metadata']['labels'].get('wzos-pilot')==sys.argv[2], 'Ownership mismatch'
PY
 if test "$(python3 -c 'import json,sys;print(len(json.load(open(sys.argv[1]))))' "$root/speech-cleanup-before.json")" = 1; then
  gcloud run jobs delete "$job" --project="$project" --region="$region" --quiet > "$root/speech-delete.log" 2>&1
 fi
 gcloud run jobs list --project="$project" --region="$region" --filter="metadata.name=$job" --format=json > "$root/speech-cleanup-after.json"
 python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); assert json.loads((p/'speech-cleanup-after.json').read_text())==[]
(p/'speech-cleanup.verified').write_text('0\n'); print('SPEECH_PILOT_CLEANUP_VERIFIED')
PY
}
if test "$mode" = cleanup; then cleanup; exit; fi
test "$mode" = run
test -f "$root/speech-pilot-approved"
test "$(cat "$root/node.exit")" = 0; test "$(cat "$root/postgres.exit")" = 0
image=$(cat "$root/job-image.txt")
[[ "$image" =~ ^us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-field-voice-pilot@sha256:[a-f0-9]{64}$ ]]
gcloud run jobs list --project="$project" --region="$region" --filter="metadata.name=$job" --format=json > "$root/speech-preflight.json"
python3 -c 'import json,sys;assert json.load(open(sys.argv[1]))==[]' "$root/speech-preflight.json"
on_exit() {
 result=$?; trap - EXIT; set +e
 timeout 180 bash "$0" cleanup "$root" > "$root/speech-cleanup.log" 2>&1 || result=1
 printf '%s\n' "$result" > "$root/speech-pilot.exit"
 if tar --exclude='./source' --exclude='./audio' --exclude='./pip-cache' -czf "$HOME/wzos-field-voice-speech-$nonce.tgz" -C "$root" .; then
  printf '%s\n' "$HOME/wzos-field-voice-speech-$nonce.tgz" > "$HOME/wzos-field-voice-evidence-latest.txt"
 fi
 exit "$result"
}
trap on_exit EXIT
timeout 120 gcloud run jobs create "$job" --project="$project" --region="$region" --image="$image" \
 --service-account=wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com --labels="wzos-pilot=$nonce" \
 --tasks=1 --parallelism=1 --max-retries=0 --task-timeout=300s --cpu=1 --memory=512Mi \
 --set-env-vars=WZOS_FIELD_VOICE_SPEECH_ENABLED=1,WZOS_FIELD_VOICE_SPEECH_MODEL=long \
 --command=python --args=/app/scripts/check_field_voice_speech.py,--audio-root,/app/pilot-audio --quiet > "$root/speech-create.log" 2>&1
gcloud run jobs describe "$job" --project="$project" --region="$region" --format=json > "$root/speech-config.json"
python3 - "$root" "$image" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);j=json.loads((p/'speech-config.json').read_text());outer=j['spec']['template']['spec'];s=outer['template']['spec'];c=s['containers'][0]
assert outer['taskCount']==1 and outer.get('parallelism',1)==1
assert s['serviceAccountName']=='wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com'
assert s['maxRetries']==0 and str(s['timeoutSeconds'])=='300'
assert c['image']==sys.argv[2] and not c.get('volumeMounts') and not s.get('volumes')
assert {e['name']:e['value'] for e in c['env']}=={'WZOS_FIELD_VOICE_SPEECH_ENABLED':'1','WZOS_FIELD_VOICE_SPEECH_MODEL':'long'}
assert c['command']==['python'] and c['args']==['/app/scripts/check_field_voice_speech.py','--audio-root','/app/pilot-audio']
assert c['resources']['limits']['cpu'] in ('1','1000m') and c['resources']['limits']['memory']=='512Mi'
print('SPEECH_PILOT_CONFIG_VERIFIED')
PY
timeout 420 gcloud run jobs execute "$job" --project="$project" --region="$region" --wait --quiet --format=json > "$root/speech-execution.json" 2> "$root/speech-execution.log" && result=0 || result=$?
# Read sanitized diagnostic output even when execution fails.
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=$job" --project="$project" --freshness=15m --order=asc --limit=100 --format=json > "$root/speech-logs.json"
test "$result" = 0
python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);e=json.loads((p/'speech-execution.json').read_text());assert e['status'].get('succeededCount')==1 and not e['status'].get('failedCount')
name=e['metadata']['name'];rows=[r for r in json.loads((p/'speech-logs.json').read_text()) if r.get('labels',{}).get('run.googleapis.com/execution_name')==name and r.get('logName','').endswith('stdout')]
values=[r['jsonPayload'] for r in rows if 'jsonPayload' in r]
value=values[0] if len(values)==1 else json.loads('\n'.join(r.get('textPayload','') for r in rows))
assert value['status']=='PASS' and value['synthetic_only'] and value['transcription_model']=='long'
assert value['speech_requests']==4 and value['model_requests']==0 and value['sms_sent']==0
assert len(value['checks'])==4 and value['raw_audio_or_transcript_logged'] is False
(p/'speech-result.json').write_text(json.dumps(value,indent=2));print('SPEECH_MULTI_SENTENCE_PASS speech=4 model=0 sms=0')
PY
