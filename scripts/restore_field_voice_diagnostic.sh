#!/usr/bin/env bash
# Restore reviewed operations after /tmp loss; never invent fresh gate results.
set -euo pipefail
umask 077
root=${1:?New private evidence directory}
project=enterprise-gemma2
test "$(gcloud config get-value project 2>/dev/null)" = "$project"
helper_commit=$(git -C "$root/source" rev-parse HEAD)
for pair in run_field_voice_pilot.sh:run_pilot.sh deploy_atlas_vllm.sh:deploy_model.sh check_field_voice_runtime.py:check_runtime.py deploy_field_voice_activation.sh:deploy_activation.sh check_field_voice_activation.py:check_activation.py check_field_voice_identity.py:check_identity.py activate_field_voice_speech.sh:activate_speech.sh; do
 source_name=${pair%%:*};target_name=${pair#*:}
 git -C "$root/source" show "$helper_commit:scripts/$source_name" > "$root/$target_name"
done
git -C "$root/source" show "$helper_commit:docs/FIELD_VOICE_RUNTIME_ACCEPTANCE_20261018.json" > "$root/accepted-runtime.json"
git -C "$root/source" fetch --quiet --depth 1 origin 95bc0f80e51ae1ce0344db4d6606b3bb4b9ca3a6
git -C "$root/source" checkout --quiet --detach 95bc0f80e51ae1ce0344db4d6606b3bb4b9ca3a6
python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);a=json.loads((p/'accepted-runtime.json').read_text())
(p/'source-commit.txt').write_text(a['runtime_commit'])
(p/'app-image.txt').write_text(a['application_image'])
PY
gcloud builds describe 0b19c5a6-5fbe-4700-88e5-bf2ee6d8b39b --project="$project" --format=json > "$root/original-app-build.json"
gcloud builds describe 8c532f56-e430-4220-9beb-d927496c5732 --project="$project" --format=json > "$root/diagnostic-build.json"
python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);b=json.loads((p/'diagnostic-build.json').read_text());assert b['status']=='SUCCESS'
images=b['results']['images'];assert len(images)==1;i=images[0]
value=i['name'].rsplit(':',1)[0]+'@'+i['digest']
assert value=='us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-field-voice-pilot@sha256:eb8cd6d7ea2230d48d1b0aee91f3f11d998fbbfada30ad81a7f3283cab17959a'
(p/'job-image.txt').write_text(value)
PY
python3 "$root/check_runtime.py" "$root"
gcloud run services describe wzos-v2-accounts --project="$project" --region=us-central1 --format=json > "$root/app-before.json"
printf 'Restored existing scoped Speech authorization; see committed activation scope.\n' > "$root/speech-approved"
bash "$root/activate_speech.sh" "$root" > "$root/speech-setup.log" 2>&1
date -u +%FT%TZ > "$root/model-approved"
date -u +%FT%TZ > "$root/job-approved"
printf 'v20261018-%s\n' "$RANDOM" > "$root/pilot-nonce.txt"
bash -n "$root/run_pilot.sh" "$root/deploy_model.sh"
echo FIELD_VOICE_DIAGNOSTIC_RESTORED
bash "$root/run_pilot.sh" run "$root"
