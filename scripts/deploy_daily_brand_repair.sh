#!/usr/bin/env bash
# Run only after explicit exact Daily fallback media-origin approval.
set -euo pipefail
umask 077
project=enterprise-gemma2
service=wzos-v2-accounts
region=us-central1
source_commit=${1:?Exact tested commit required}
[[ "$source_commit" =~ ^[0-9a-f]{40}$ ]]
short=${source_commit:0:7}
root=$(cat "$HOME/wzos-daily-frame-path.txt")
test "$(cat "$root/gate.exit")" = 0
test "$(cat "$root/build.exit")" = 0
cd "$root/source"
test "$(git rev-parse HEAD)" = "$source_commit"
immutable=$(cat "$root/immutable.txt")
[[ "$immutable" =~ ^us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:[0-9a-f]{64}$ ]]
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/before.json"
python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
s=json.loads((Path(sys.argv[1])/'before.json').read_text())
assert s['spec']['template']['spec']['containers'][0]['image'].endswith('@sha256:6a2312b6ca77f675398a5858621e08e0b87e7dfd878495bc25ce01b6f950a83d')
assert [(t.get('revisionName'),t.get('percent')) for t in s['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-office-8d09c4a',100)]
assert s['metadata']['annotations']['run.googleapis.com/ingress']=='internal-and-cloud-load-balancing'
PY
gcloud run deploy "$service" --project="$project" --region="$region" --image="$immutable" --no-traffic --revision-suffix="brand-$short" --quiet > "$root/stage.log" 2>&1
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/staged.json"
gcloud run revisions describe "$service-brand-$short" --project="$project" --region="$region" --format=json > "$root/revision.json"
python3 - "$root" "$immutable" <<'PY'
import copy,json,sys
from pathlib import Path
p=Path(sys.argv[1]);read=lambda n:json.loads((p/n).read_text())
b,a,r=read('before.json'),read('staged.json'),read('revision.json')
assert any(c['type']=='Ready' and c['status']=='True' for c in r['status']['conditions'])
assert r['status']['imageDigest']==sys.argv[2]
prior=b['spec']['template']['spec'];actual=copy.deepcopy(r['spec'])
assert actual['containers'][0]['image']==sys.argv[2]
actual['containers'][0]['image']=prior['containers'][0]['image']
if 'name' not in prior['containers'][0]:
 assert actual['containers'][0].pop('name',None)=='wzos-v2-accounts-1'
assert actual==prior, 'Runtime configuration changed'
ignore={'run.googleapis.com/client-name','run.googleapis.com/client-version','run.googleapis.com/operation-id'}
annotations=lambda s:{k:v for k,v in s['spec']['template']['metadata'].get('annotations',{}).items() if k not in ignore}
assert annotations(b)==annotations(a), 'Template annotations changed'
for key in ['run.googleapis.com/ingress','run.googleapis.com/invoker-iam-disabled']:
 assert b['metadata']['annotations'].get(key)==a['metadata']['annotations'].get(key)
assert [(t.get('revisionName'),t.get('percent')) for t in a['status']['traffic'] if t.get('percent')]==[(t.get('revisionName'),t.get('percent')) for t in b['status']['traffic'] if t.get('percent')]
print('STAGED_CONFIG_PRESERVED')
PY
gcloud run services update-traffic "$service" --project="$project" --region="$region" --to-revisions="$service-brand-$short=100" --quiet > "$root/cutover.log" 2>&1
if ! python3 - "$root" <<'PY'
import hashlib,sys,time,urllib.request
from pathlib import Path
root=Path(sys.argv[1]);static=Path('services/workspace_preview/static')
for name in ['workspace.js','workspace.css','organization-hub.js','training-content.js','training-media.js','navigation.js','team-modules.js','dispatch.js','forms-hub.js','forms-hub.css','review-workflows.js','install.js','phone-number.js','manifest.webmanifest','account.js','daily-meetings.js','wzos-logo.png','favicon.ico','favicon-32.png','install-icon-144.png','install-icon-180.png','install-icon-192.png','install-icon-512.png','install-maskable-192.png','install-maskable-512.png']:
 u='https://app.workzoneos.org/'+name+'?release=office-update'
 with urllib.request.urlopen(u,timeout=45) as r: data=r.read();assert r.status==200
 assert hashlib.sha256(data).digest()==hashlib.sha256((static/name).read_bytes()).digest(),name+' asset mismatch'
with urllib.request.urlopen('https://app.workzoneos.org/?release=brand-daily',timeout=30) as response:
 html=response.read().decode('utf-8');assert '/favicon.ico?brand=20261017' in html
 policies=response.headers.get_all('Content-Security-Policy',[]);assert policies
 for policy in policies:
  frame=next((part for part in policy.split(';') if part.strip().startswith('frame-src ')), '')
  for host in ('wzos.daily.co','wzos.dailywebrtc.com','wzos.dailywebrtc.net'):
   assert 'https://'+host in frame, 'Missing exact Daily frame host'
  assert '*.daily' not in frame, 'Unexpected wildcard'
 permissions=response.headers.get('Permissions-Policy','')
 for host in ('wzos.daily.co','wzos.dailywebrtc.com','wzos.dailywebrtc.net'):
  assert permissions.count('"https://'+host+'"')==2, 'Camera/microphone policy mismatch'
print('LIVE_EXACT_DAILY_POLICY_AND_LOGO_PASS')
with urllib.request.urlopen('https://app.workzoneos.org/api/app/version?release=office-update',timeout=30) as r:
 assert r.status==200;version=r.read()
(root/'live-version.json').write_bytes(version)
print('LIVE_OFFICE_SMS_PWA_ASSETS_PASS')
PY
then
 gcloud run services update-traffic "$service" --project="$project" --region="$region" --to-revisions="$service-office-8d09c4a=100" --quiet
 echo ROLLED_BACK_TO_OFFICE_8D09C4A
 exit 1
fi
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/live.json"
python3 - "$root" "$short" <<'PY'
import json,sys
from pathlib import Path
s=json.loads((Path(sys.argv[1])/'live.json').read_text());assert [(t.get('revisionName'),t.get('percent')) for t in s['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-brand-'+sys.argv[2],100)]
print('DEPLOYED_OFFICE_'+sys.argv[2]+'_100_PERCENT')
PY
