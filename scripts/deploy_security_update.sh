#!/usr/bin/env bash
# Existing service only; user-authorized October16 release. No initial traffic.
set -euo pipefail
umask 077
evidence=${1:?Private release evidence required}
image=${2:?Exact immutable application image required}
[[ $image =~ ^us-central1-docker\.pkg\.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:[a-f0-9]{64}$ ]] || exit 2
test "$(gcloud config get-value project 2>/dev/null)" = enterprise-gemma2
test "$(cat "$evidence/postgres.exit")" = 0
test "$(cat "$evidence/persistence/engine.exit")" = 0
python3 - "$evidence" "$image" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); schema=json.loads((p/'schema.json').read_text())
assert not schema['conflicts']
assert set(schema['missing_tables']) <= {'security_incidents','security_actions','security_file_states','security_alert_reads','purchase_events','purchase_requests'}
assert json.loads((p/'persistence/persistent-fixtures.json').read_text())['cleaned'] is True
backup=json.loads((p/'backup-final.json').read_text())
assert backup['status']=='SUCCESSFUL' and backup['description']=='pre-security-update-20261016'
build=json.loads((p/'repaired-build-final.json').read_text())
assert build['status']=='SUCCESS' and build['results']['images'][0]['digest']==sys.argv[2].rsplit('@',1)[1]
PY
gcloud run services describe wzos-v2-accounts --project=enterprise-gemma2 --region=us-central1 --format=json > "$evidence/at-deploy-service.json"
python3 - "$evidence" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); b=json.loads((p/'before-service.json').read_text()); a=json.loads((p/'at-deploy-service.json').read_text())
assert b['spec']==a['spec'],'Configuration drift requires review'
assert [(t.get('revisionName'),t.get('percent')) for t in a['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-hub-5a3ac86',100)]
assert a['metadata']['annotations']['run.googleapis.com/ingress']=='internal-and-cloud-load-balancing'
PY
fallback='us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:ef31216bc772a0233b7c59a9e219dcd9b17f6c6f2c8ed058270a9a009676ab9d'
scanner='https://wzos-v2-scanner-udtvm4rgca-uc.a.run.app'
# This reviewed fallback implements durable file holds. Its older30s scanner wait
# can fail closed on a cold start; it never permits an unverified held download.
gcloud run deploy wzos-v2-accounts --project=enterprise-gemma2 --region=us-central1 \
  --image="$fallback" --no-traffic --revision-suffix=security-fallback-1016 \
  --update-env-vars="WZOS_SCANNER_URL=$scanner,WZOS_FILE_SCAN_REQUIRED=1" --quiet \
  > "$evidence/fallback-deploy.log" 2>&1
gcloud run deploy wzos-v2-accounts --project=enterprise-gemma2 --region=us-central1 \
  --image="$image" --no-traffic --revision-suffix=security-update-1016 --quiet \
  > "$evidence/candidate-deploy.log" 2>&1
for revision in wzos-v2-accounts-security-fallback-1016 wzos-v2-accounts-security-update-1016; do
  gcloud run revisions describe "$revision" --project=enterprise-gemma2 --region=us-central1 --format=json > "$evidence/$revision.json"
done
gcloud run services describe wzos-v2-accounts --project=enterprise-gemma2 --region=us-central1 --format=json > "$evidence/candidate-service.json"
printf 'SECURITY_REVISIONS_STAGED_NO_TRAFFIC\n'
