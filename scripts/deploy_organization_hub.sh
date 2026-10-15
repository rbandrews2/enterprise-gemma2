#!/usr/bin/env bash
# Approved October 14: existing service, preserved configuration, no initial traffic.
set -euo pipefail
umask 077
evidence="$HOME/wzos-hub-rollout-20261014"
image='us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:4cc2f391151e1aaf00d9ad29bc68c57779b808f75ed9034f23e3bcbb3af71bdd'
python3 - "$evidence" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
assert (p/'release-gates-approved.txt').read_text().strip()=='HUB_GATES_APPROVED_20261014'
s=json.loads((p/'schema.json').read_text())
assert not s['conflicts']
hub={'hub_notes','hub_preferences','hub_status_checks','integration_credentials','integration_usage','hub_audit'}
# Static extraction also sees inactive checkout definitions. They are not mounted
# by create_app and are not part of this startup migration.
assert hub <= set(s['missing_tables']) <= hub | {'purchase_events','purchase_requests'}
b=json.loads((p/'backup.json').read_text())
assert b['status']=='SUCCESSFUL' and b['description']=='pre-hub-5a3ac86'
PY
gcloud run services describe wzos-v2-accounts --project enterprise-gemma2 --region us-central1 --format=json > "$evidence/at-deploy-service.json"
python3 - "$evidence" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);b=json.loads((p/'before-service.json').read_text());a=json.loads((p/'at-deploy-service.json').read_text())
assert b['spec']==a['spec'] and b['status']['traffic']==a['status']['traffic'],'Live service drifted; review before deployment'
assert [(t.get('revisionName'),t.get('percent')) for t in a['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-daily-748f382',100)]
PY
gcloud run deploy wzos-v2-accounts --project enterprise-gemma2 --region us-central1 \
  --image "$image" --no-traffic --revision-suffix=hub-5a3ac86 --quiet
gcloud run services describe wzos-v2-accounts --project enterprise-gemma2 --region us-central1 --format=json > "$evidence/candidate-service.json"
python3 - "$evidence" "$image" <<'PY'
import copy,json,sys
from pathlib import Path
p=Path(sys.argv[1]);b=json.loads((p/'at-deploy-service.json').read_text());a=json.loads((p/'candidate-service.json').read_text())
bs=copy.deepcopy(b['spec']['template']['spec']);ns=copy.deepcopy(a['spec']['template']['spec'])
assert ns['containers'][0]['image']==sys.argv[2]
ns['containers'][0]['image']=bs['containers'][0]['image']
assert ns==bs,'Unexpected runtime configuration change'
def annotations(x):
    return {k:v for k,v in x.items() if k not in {'run.googleapis.com/client-name','run.googleapis.com/client-version','run.googleapis.com/operation-id'}}
assert annotations(b['spec']['template']['metadata'].get('annotations',{}))==annotations(a['spec']['template']['metadata'].get('annotations',{})),'Template annotations changed'
for k in ('run.googleapis.com/ingress','run.googleapis.com/invoker-iam-disabled'):
    assert b['metadata'].get('annotations',{}).get(k)==a['metadata'].get('annotations',{}).get(k),k
assert a['status']['latestReadyRevisionName']=='wzos-v2-accounts-hub-5a3ac86'
assert a['status']['latestCreatedRevisionName']==a['status']['latestReadyRevisionName']
assert [(t.get('revisionName'),t.get('percent')) for t in a['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-daily-748f382',100)]
print('HUB_CANDIDATE_READY_CONFIGURATION_PRESERVED_NO_TRAFFIC')
PY
