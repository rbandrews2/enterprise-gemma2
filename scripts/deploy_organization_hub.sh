#!/usr/bin/env bash
# Approved October 14: existing service, preserved configuration, no initial traffic.
set -euo pipefail
umask 077
evidence="$HOME/wzos-hub-rollout-20261014"
image='us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:fc87869680a0c6948d4116225ddf7ae22de6a659d0264e31351a251367465f06'
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
build=json.loads((p/'os-build-result.json').read_text())
assert build['status']=='SUCCESS' and build['results']['images'][0]['digest']=='sha256:fc87869680a0c6948d4116225ddf7ae22de6a659d0264e31351a251367465f06'
scan=json.loads((p/'os-scan.json').read_text())
assert scan.get('done') and scan.get('response',{}).get('scan') and not scan.get('error')
findings=json.loads((p/'os-vulnerabilities.json').read_text())
reviewed={'CVE-2026-9538','CVE-2026-54371','CVE-2026-85091','CVE-2026-54369','CVE-2026-54370'}
for finding in findings:
    v=finding.get('vulnerability',{});severity=v.get('effectiveSeverity',v.get('severity'))
    assert not v.get('fixAvailable'),'Available security update remains'
    assert severity!='CRITICAL','Critical finding requires review'
    if severity=='HIGH':assert finding['noteName'].rsplit('/',1)[-1] in reviewed,'New high finding requires review'
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
  --image "$image" --no-traffic --revision-suffix=hub-5a3ac86 --tag=hub-5a3ac86 --quiet
gcloud run services describe wzos-v2-accounts --project enterprise-gemma2 --region us-central1 --format=json > "$evidence/candidate-service.json"
gcloud run revisions describe wzos-v2-accounts-hub-5a3ac86 --project enterprise-gemma2 --region us-central1 --format=json > "$evidence/candidate-revision.json"
python3 scripts/verify_hub_candidate.py
