#!/usr/bin/env bash
# Gate/build only. Does not grant access, activate providers or change public traffic.
set -euo pipefail
umask 077
phase=${1:?gate/build}; root=${2:?Private evidence directory}
project=enterprise-gemma2
base=us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:e9b8085ca49aa6d8236df0b3174ce57c82f2d86d15b72caf0063a1d31c7ea852
cd "$root/source"
test "$(git rev-parse HEAD)" = "$(cat "$root/source-commit.txt")"
test "$(gcloud config get-value project 2>/dev/null)" = "$project"
if test "$phase" = gate; then
 node --test tests/*.test.cjs > "$root/node.log" 2>&1 && result=0 || result=$?
 printf '%s\n' "$result" > "$root/node.exit"
 bash scripts/test_postgres_native.sh > "$root/postgres.log" 2>&1 && result=0 || result=$?
 printf '%s\n' "$result" > "$root/postgres.exit"
 test "$(cat "$root/node.exit")" = 0; test "$result" = 0
 .venv-accounts-test/bin/python scripts/check_field_voice_workflow.py --mode mocked --audio-root "$root/audio" > "$root/harness-dryrun.json" 2> "$root/harness-dryrun.log"
 echo FIELD_VOICE_GATES_PASS; exit 0
fi
test "$phase" = build
test "$(cat "$root/node.exit")" = 0; test "$(cat "$root/postgres.exit")" = 0
test -s "$root/harness-dryrun.json"
gcloud run services describe wzos-v2-accounts --project="$project" --region=us-central1 --format=json > "$root/app-before.json"
python3 - "$root" "$base" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);s=json.loads((p/'app-before.json').read_text())
assert s['spec']['template']['spec']['containers'][0]['image']==sys.argv[2]
assert [(t.get('revisionName'),t.get('percent')) for t in s['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-mobile-c944173',100)]
env={e['name']:e.get('value') for e in s['spec']['template']['spec']['containers'][0]['env']}
assert env.get('WZOS_ATLAS_VLLM_ENABLED','0')=='0'
assert env.get('WZOS_FIELD_VOICE_ENABLED','0')=='0'
assert json.loads((p/'harness-dryrun.json').read_text())['status']=='PASS'
PY
tag=$(git rev-parse --short=7 HEAD)
appimage=us-central1-docker.pkg.dev/$project/$project/wzos-v2-accounts:field-voice-$tag
jobimage=us-central1-docker.pkg.dev/$project/$project/wzos-v2-field-voice-pilot:$tag
printf 'FROM %s\nUSER root\nCOPY services /app/services\nRUN python -m compileall -q /app/services && chmod -R a+rX /app/services\nUSER wzos\n' "$base" > Dockerfile.field-voice
mkdir pilot-audio
cp "$root"/audio/*.wav pilot-audio/
printf 'FROM %s\nUSER root\nCOPY scripts/check_field_voice_workflow.py /app/scripts/check_field_voice_workflow.py\nCOPY pilot-audio /app/pilot-audio\n' "$appimage" > Dockerfile.field-voice-pilot
if test -f "$root/check_speech.py"; then
 cp "$root/check_speech.py" scripts/check_field_voice_speech.py
 printf 'COPY scripts/check_field_voice_speech.py /app/scripts/check_field_voice_speech.py\n' >> Dockerfile.field-voice-pilot
fi
printf 'RUN chmod -R a+rX /app/scripts /app/pilot-audio\nUSER wzos\nENTRYPOINT ["python","/app/scripts/check_field_voice_workflow.py"]\nCMD ["--audio-root","/app/pilot-audio"]\n' >> Dockerfile.field-voice-pilot
cat > cloudbuild.field-voice.yaml <<'YAML'
steps:
- name: gcr.io/cloud-builders/docker
  args: ['build','--platform','linux/amd64','-f','Dockerfile.field-voice','-t','${_APP_IMAGE}', '.']
- name: gcr.io/cloud-builders/docker
  args: ['build','--platform','linux/amd64','-f','Dockerfile.field-voice-pilot','-t','${_JOB_IMAGE}', '.']
images: ['${_APP_IMAGE}','${_JOB_IMAGE}']
timeout: 600s
options:
  machineType: E2_MEDIUM
YAML
printf '\n.venv-accounts-test/\n' >> .gcloudignore
gcloud builds submit --project="$project" --config=cloudbuild.field-voice.yaml --substitutions="_APP_IMAGE=$appimage,_JOB_IMAGE=$jobimage" --async --format='value(id)' . > "$root/build-id.txt" 2> "$root/build-submit.log"
echo FIELD_VOICE_BUILD_SUBMITTED; cat "$root/build-id.txt"
