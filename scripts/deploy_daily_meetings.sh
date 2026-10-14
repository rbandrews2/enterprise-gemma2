#!/usr/bin/env bash
# Ray approved secret-specific Daily access and deployment. Never prints a key.
set -euo pipefail
umask 077
evidence="$HOME/wzos-daily-20261014"
grep -q '^DAILY_BACKUP_SUCCESS ' "$evidence/preflight.log"
grep -Fxq 'PostgreSQL gate: PASS; run=576, failures=0, errors=0, skipped=0' "$evidence/final-gate-and-provider.log"
grep -Fxq 'DAILY_SYNTHETIC_ROOM_REMOVED' "$evidence/final-gate-and-provider.log"
build=$(tr -d '\r\n' < "$evidence/build.id")
gcloud builds describe "$build" --project enterprise-gemma2 --format=json > "$evidence/build-result.json"
image=$(python3 - "$evidence" <<'PY'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]);b=json.loads((root/'build-result.json').read_text())
assert b['status']=='SUCCESS','Build is not successful'
i=b['results']['images'][0];assert i['name'].endswith(':748f382-daily')
assert i['digest'].startswith('sha256:') and len(i['digest'])==71
before=json.loads((root/'before-service.json').read_text())
assert before['spec']['template']['spec']['serviceAccountName']=='wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com'
print(i['name'].split(':748f382-daily')[0]+'@'+i['digest'])
PY
)
printf '%s\n' "$image" > "$evidence/image.txt"
gcloud secrets add-iam-policy-binding wzos-v2-daily-api-key --project enterprise-gemma2 \
 --member=serviceAccount:wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com \
 --role=roles/secretmanager.secretAccessor --condition=None --quiet >/dev/null
gcloud secrets get-iam-policy wzos-v2-daily-api-key --project enterprise-gemma2 --format=json > "$evidence/after-daily-policy.json"
python3 - "$evidence/after-daily-policy.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]));member='serviceAccount:wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com'
assert any(b['role']=='roles/secretmanager.secretAccessor' and member in b['members'] for b in p.get('bindings',[]))
assert not any(m in ('allUsers','allAuthenticatedUsers') for b in p.get('bindings',[]) for m in b['members'])
print('DAILY_SCOPED_SECRET_ACCESS_CONFIRMED')
PY
gcloud run deploy wzos-v2-accounts --project enterprise-gemma2 --region us-central1 \
 --image "$image" --no-traffic --revision-suffix=daily-748f382 --tag=daily-748f382 \
 --update-secrets=WZOS_DAILY_API_KEY=wzos-v2-daily-api-key:1 \
 --update-env-vars=WZOS_DAILY_DOMAIN=wzos.daily.co,WZOS_DAILY_ENABLED=1 --quiet
gcloud run services describe wzos-v2-accounts --project enterprise-gemma2 --region us-central1 --format=json > "$evidence/candidate-service.json"
python3 - "$evidence" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);before=json.loads((p/'before-service.json').read_text());after=json.loads((p/'candidate-service.json').read_text())
bs=before['spec']['template']['spec'];ns=after['spec']['template']['spec']
b=bs['containers'][0];n=ns['containers'][0]
def env(c):return {e['name']:e for e in c.get('env',[])}
be,ne=env(b),env(n);allowed={'WZOS_DAILY_API_KEY','WZOS_DAILY_DOMAIN','WZOS_DAILY_ENABLED'}
assert {k:v for k,v in be.items() if k not in allowed}=={k:v for k,v in ne.items() if k not in allowed},'Unexpected existing environment change'
assert ne['WZOS_DAILY_DOMAIN']['value']=='wzos.daily.co' and ne['WZOS_DAILY_ENABLED']['value']=='1'
ref=ne['WZOS_DAILY_API_KEY']['valueFrom']['secretKeyRef'];assert ref['name']=='wzos-v2-daily-api-key' and ref['key']=='1'
for k in ('serviceAccountName','containerConcurrency','timeoutSeconds'):assert bs.get(k)==ns.get(k),k
assert b.get('resources')==n.get('resources'),'Capacity changed'
for k in ('run.googleapis.com/ingress','run.googleapis.com/invoker-iam-disabled'):assert before['metadata'].get('annotations',{}).get(k)==after['metadata'].get('annotations',{}).get(k),k
assert after['status']['latestReadyRevisionName']=='wzos-v2-accounts-daily-748f382'
assert after['status'].get('latestCreatedRevisionName')==after['status']['latestReadyRevisionName']
print('DAILY_CANDIDATE_CONFIGURATION_PRESERVED')
PY
echo 'DAILY_CANDIDATE_READY_NO_TRAFFIC'
# Traffic is switched only after inspecting the result and performing release checks.
