#!/usr/bin/env bash
# Existing-service, approved upgrade release. Rollback pauses new upgrades on the SAME code.
set -euo pipefail
umask 077
root=$(cat "$HOME/wzos-core-upgrade-path.txt")
project=enterprise-gemma2
region=us-central1
service=wzos-v2-accounts
resume=${1:-}
[[ "$resume" == '' || "$resume" == --resume-staged ]]
image=us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:f347f6901acb223b412ae729aa52afc47a1210804b861916ecfc18f46f5e3873
test "$(gcloud config get-value project 2>/dev/null)" = "$project"
test "$(cat "$root/validation-final.exit")" = 0
test "$(cat "$root/upgrade-preflight.exit")" = 0
test "$(cat "$root/upgrade-provider-preview.exit")" = 0
if [[ "$resume" != --resume-staged ]]; then
 gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/upgrade-before-deploy.json"
fi
python3 - "$root" "$image" <<'PY'
import datetime,json,sys
from pathlib import Path
p=Path(sys.argv[1]);read=lambda n:json.loads((p/n).read_text())
b=read('upgrade-build.json');assert b['status']=='SUCCESS'
assert any(i['digest']==sys.argv[2].split('@')[1] and i['name'].endswith(':core-upgrade-bf9f524') for i in b['results']['images'])
assert (p/'final-tested-source.txt').read_text().strip().startswith('bf9f524')
s=read('upgrade-schema.json');assert not s['conflicts'] and set(s['missing_tables']) <= {'organization_upgrades'}
backups=read('upgrade-backups.json');now=datetime.datetime.now(datetime.timezone.utc)
assert any(x['status']=='SUCCESSFUL' and (now-datetime.datetime.fromisoformat(x['startTime'].replace('Z','+00:00'))).total_seconds()<86400 for x in backups), 'Refresh backup review'
before=read('upgrade-before-deploy.json');prior=read('upgrade-current.json')
assert before['spec']==prior['spec'], 'Service configuration drift'
assert [(t.get('revisionName'),t.get('percent')) for t in before['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-weather-hourly-1017',100)]
assert before['spec']['template']['spec']['containers'][0]['image'].endswith('@sha256:edb4a3c4dde24cb6fe57d65ad79f1cfd611ab507d1d1bf03ea70e18f972e92ed')
assert before['metadata']['annotations']['run.googleapis.com/ingress']=='internal-and-cloud-load-balancing'
assert read('upgrade-provider-preview.json')['payment_attempted'] is False
PY
if [[ "$resume" != --resume-staged ]]; then
for mode in hold live; do
 enabled=0; test "$mode" != live || enabled=1
 gcloud run deploy "$service" --project="$project" --region="$region" --image="$image" --no-traffic \
  --revision-suffix="upgrade-$mode-bf9f524" --update-env-vars="WZOS_CORE_UPGRADES_ENABLED=$enabled" --quiet > "$root/upgrade-$mode-stage.log" 2>&1
 gcloud run revisions describe "$service-upgrade-$mode-bf9f524" --project="$project" --region="$region" --format=json > "$root/upgrade-$mode-revision.json"
done
fi
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/upgrade-staged-service.json"
python3 - "$root" "$image" <<'PY'
import copy,json,sys
from pathlib import Path
p=Path(sys.argv[1]);read=lambda n:json.loads((p/n).read_text())
before=read('upgrade-before-deploy.json');staged=read('upgrade-staged-service.json')
prior=before['spec']['template']['spec']
for mode,value in [('hold','0'),('live','1')]:
 r=read('upgrade-'+mode+'-revision.json')
 assert r['status']['imageDigest']==sys.argv[2]
 assert any(c['type']=='Ready' and c['status']=='True' for c in r['status']['conditions'])
 actual=copy.deepcopy(r['spec']);expected=copy.deepcopy(prior)
 actual['containers'][0]['image']=expected['containers'][0]['image']
 if 'name' not in expected['containers'][0]:actual['containers'][0].pop('name',None)
 env={x['name']:x for x in actual['containers'][0].pop('env')}
 assert env.pop('WZOS_CORE_UPGRADES_ENABLED')=={'name':'WZOS_CORE_UPGRADES_ENABLED','value':value}
 old={x['name']:x for x in expected['containers'][0].pop('env')};old.pop('WZOS_CORE_UPGRADES_ENABLED',None)
 assert env==old,'Existing runtime flags/secret bindings changed'
 assert actual==expected,'Runtime resource/identity/storage configuration changed'
 assert r['metadata'].get('annotations',{}).get('serving.knative.dev/creator')=='admin@workzoneos.org'
 ignored={'run.googleapis.com/client-name','run.googleapis.com/client-version','run.googleapis.com/operation-id','serving.knative.dev/creator'}
 annotations=lambda d:{k:v for k,v in d.get('annotations',{}).items() if k not in ignored}
 assert annotations(r['metadata'])==annotations(before['spec']['template']['metadata']), 'Template annotations changed'
for key in ['run.googleapis.com/ingress','run.googleapis.com/invoker-iam-disabled']:
 assert staged['metadata']['annotations'].get(key)==before['metadata']['annotations'].get(key)
assert [(t.get('revisionName'),t.get('percent')) for t in staged['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-weather-hourly-1017',100)]
assert staged['status']['latestCreatedRevisionName']=='wzos-v2-accounts-upgrade-live-bf9f524'
assert staged['status']['latestReadyRevisionName']=='wzos-v2-accounts-upgrade-live-bf9f524'
print('UPGRADE_STAGED_CONFIG_PRESERVED')
PY
gcloud run services update-traffic "$service" --project="$project" --region="$region" --to-revisions="$service-upgrade-live-bf9f524=100" --quiet > "$root/upgrade-cutover.log" 2>&1
if ! python3 - "$root" <<'PY'
import hashlib,json,sys,urllib.request,urllib.error
from pathlib import Path
p=Path(sys.argv[1]);static=p/'source-final/services/workspace_preview/static'
for name in ['organization-hub.js','workspace.css','workspace.js','weather.js','daily-meetings.js','account.js','install.js','manifest.webmanifest']:
 with urllib.request.urlopen('https://app.workzoneos.org/'+name+'?upgrade=bf9f524',timeout=30) as r:data=r.read();assert r.status==200
 assert hashlib.sha256(data).digest()==hashlib.sha256((static/name).read_bytes()).digest(),name+' mismatch'
for path in ['/api/account/upgrade','/api/weather/notices','/api/weather/sites']:
 try:
  urllib.request.urlopen('https://app.workzoneos.org'+path,timeout=30)
  raise AssertionError('Unexpected anonymous account access')
 except urllib.error.HTTPError as error:assert error.code==401
with urllib.request.urlopen('https://app.workzoneos.org/',timeout=30) as r:
 assert 'id="weather-card"' in r.read().decode()
 csp=r.headers.get('Content-Security-Policy','');permissions=r.headers.get('Permissions-Policy','')
 frame=next(x for x in csp.split(';') if x.strip().startswith('frame-src '))
 for host in ['wzos.daily.co','wzos.dailywebrtc.com','wzos.dailywebrtc.net']:
  assert 'https://'+host in frame and permissions.count('"https://'+host+'"')==2
 assert '*.daily' not in frame
with urllib.request.urlopen('https://app.workzoneos.org/api/app/version?upgrade=bf9f524',timeout=30) as r:
 (p/'upgrade-live-version.json').write_bytes(r.read())
print('UPGRADE_PUBLIC_ASSETS_AUTH_MEDIA_PASS')
PY
then
 gcloud run services update-traffic "$service" --project="$project" --region="$region" --to-revisions="$service-upgrade-hold-bf9f524=100" --quiet
 echo UPGRADE_ROLLBACK_PAUSED_SAME_IMAGE
 exit 1
fi
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/upgrade-live-service.json"
python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
s=json.loads((Path(sys.argv[1])/'upgrade-live-service.json').read_text())
assert [(t.get('revisionName'),t.get('percent')) for t in s['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-upgrade-live-bf9f524',100)]
print('CORE_UPGRADE_DEPLOYED_100_PERCENT')
PY
