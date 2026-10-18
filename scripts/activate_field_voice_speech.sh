#!/usr/bin/env bash
# Run only after the scoped Speech permission approval in FIELD_VOICE_ACTIVATION_20261018.md.
set -euo pipefail
umask 077
root=${1:?Private evidence directory}
project=enterprise-gemma2
test "$(gcloud config get-value project 2>/dev/null)" = "$project"
test -f "$root/speech-approved"
gcloud services enable speech.googleapis.com --project="$project" --quiet > "$root/speech-enable.log" 2>&1
if gcloud iam roles describe wzosFieldVoiceSpeech --project="$project" --format=json > "$root/speech-role.json" 2> "$root/speech-role-read.log"; then
 python3 - "$root/speech-role.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1])); assert r['includedPermissions']==['speech.recognizers.recognize'] and not r.get('deleted')
PY
else
 gcloud iam roles create wzosFieldVoiceSpeech --project="$project" --file="$root/source/scripts/field-voice-speech-role.yaml" --quiet > "$root/speech-role-create.log" 2>&1
fi
gcloud projects add-iam-policy-binding "$project" --member=serviceAccount:wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com \
 --role=projects/enterprise-gemma2/roles/wzosFieldVoiceSpeech --condition=None --quiet > "$root/speech-binding.log" 2>&1
gcloud projects get-iam-policy "$project" --format=json > "$root/speech-iam.json"
python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); policy=json.loads((p/'speech-iam.json').read_text())
rows=[b for b in policy['bindings'] if b['role']=='projects/enterprise-gemma2/roles/wzosFieldVoiceSpeech']
assert len(rows)==1 and set(rows[0]['members'])=={'serviceAccount:wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com'} and not rows[0].get('condition')
(p/'speech-setup.verified').write_text('0\n'); print('FIELD_VOICE_SPEECH_SETUP_VERIFIED')
PY
