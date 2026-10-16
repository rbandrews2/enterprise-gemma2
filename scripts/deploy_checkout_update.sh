#!/usr/bin/env bash
# Authorized existing-service release; stages only, never changes traffic.
set -euo pipefail
umask 077
evidence=${1:?Private evidence directory required}
image='us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:53f9348a618430d823067748ce0958ef084b6d73565780ffcb4a1195dda76a22'
test "$(gcloud config get-value project 2>/dev/null)" = enterprise-gemma2
test "$(cat "$evidence/final-gate.exit")" = 0
test "$(cat "$evidence/stripe-preflight-final.exit")" = 0
python3 - "$evidence" "$image" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);load=lambda n:json.loads((p/n).read_text())
assert not load('schema.json')['conflicts']
assert set(load('schema.json')['missing_tables']) <= {'security_incidents','security_actions','security_file_states','security_alert_reads','purchase_events','purchase_requests','purchase_subscriptions'}
assert any(x['status']=='SUCCESSFUL' and x['description']=='pre-final-checkout-20261016' for x in load('backup-final.json'))
b=load('final-build-final.json');assert b['status']=='SUCCESS' and b['results']['images'][0]['digest']==sys.argv[2].split('@')[1]
op=load('final-image-scan-operation.json');assert op.get('done') and not op.get('error')
findings=load('final-image-findings.json')
known={'CVE-2026-54369','CVE-2026-54370','CVE-2026-54371','CVE-2026-85091','CVE-2026-9538'}
for finding in findings:
 v=finding.get('vulnerability',{});severity=v.get('effectiveSeverity',v.get('severity','UNKNOWN'))
 assert severity!='CRITICAL'
 if severity=='HIGH':
  assert v.get('shortDescription') in known
  issues=v.get('packageIssue',[])
  assert issues and all(i.get('packageType')=='OS' and i.get('fixedVersion',{}).get('kind')=='MAXIMUM' for i in issues)
bucket=load('bucket.json');assert bucket['public_access_prevention']=='enforced' and bucket['uniform_bucket_level_access'] is True
assert not any(m in ('allUsers','allAuthenticatedUsers') for b in load('bucket-iam.json').get('bindings',[]) for m in b.get('members',[]))
PY
gcloud run services describe wzos-v2-accounts --project=enterprise-gemma2 --region=us-central1 --format=json > "$evidence/at-final-deploy-service.json"
python3 - "$evidence" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);b=json.loads((p/'before-service.json').read_text());a=json.loads((p/'at-final-deploy-service.json').read_text())
assert b['spec']==a['spec'],'Configuration drift requires review'
assert [(t.get('revisionName'),t.get('percent')) for t in a['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-hub-5a3ac86',100)]
assert a['metadata']['annotations']['run.googleapis.com/ingress']=='internal-and-cloud-load-balancing'
PY
common='WZOS_SCANNER_URL=https://wzos-v2-scanner-udtvm4rgca-uc.a.run.app,WZOS_FILE_SCAN_REQUIRED=1,WZOS_COMMERCE_ENABLED=1,WZOS_STRIPE_MODE=live,WZOS_STRIPE_TAX_VERIFIED=1'
secrets='WZOS_STRIPE_API_KEY=wzos-v2-stripe-api-keY:3,WZOS_STRIPE_WEBHOOK_SECRET=wzos-v2-stripe-webhook-secret:1,WZOS_PURCHASE_ENCRYPTION_KEY=wzos-v2-purchase-encryption-key:1'
for mode in hold live; do
 pause=1; test "$mode" != live || pause=0
 gcloud run deploy wzos-v2-accounts --project=enterprise-gemma2 --region=us-central1 \
  --image="$image" --no-traffic --revision-suffix="checkout-$mode-1016" \
  --update-env-vars="$common,WZOS_COMMERCE_CHECKOUT_PAUSED=$pause" \
  --update-secrets="$secrets" --quiet > "$evidence/checkout-$mode-deploy.log" 2>&1
 gcloud run revisions describe "wzos-v2-accounts-checkout-$mode-1016" --project=enterprise-gemma2 --region=us-central1 --format=json > "$evidence/checkout-$mode-revision.json"
done
gcloud run services describe wzos-v2-accounts --project=enterprise-gemma2 --region=us-central1 --format=json > "$evidence/checkout-staged-service.json"
python3 scripts/verify_checkout_update.py "$evidence"
