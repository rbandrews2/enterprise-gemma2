#!/usr/bin/env bash
# Existing-service source-only update. No IAM, credentials, schema or dependency changes.
set -euo pipefail
umask 077
project=enterprise-gemma2
service=wzos-v2-accounts
region=us-central1
base=us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:ec8f4243e411d4f6a1d96e1a8daec3b2f81ca2a0c0447c835314442664ca6ccb
source_commit=${1:?Exact tested candidate commit required}
[[ "$source_commit" =~ ^[0-9a-f]{40}$ ]]
short=${source_commit:0:7}
root=$(mktemp -d "$HOME/wzos-office-20261016.XXXXXXXX")
printf '%s\n' "$root" > "$HOME/wzos-office-latest-path.txt"
test "$(gcloud config get-value project 2>/dev/null)" = "$project"
gcloud auth print-access-token >/dev/null
git clone --quiet --single-branch --branch codex/preproduction-modules https://github.com/rbandrews2/enterprise-gemma2.git "$root/source"
cd "$root/source"
git checkout --quiet --detach "$source_commit"
bash scripts/test_office_sms_postgres.sh > "$root/postgres.log" 2>&1
printf "OFFICE_SMS_POSTGRES_COMPLETE\n"
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/before.json"
python3 - "$root" "$base" <<'PY'
import json,sys
from pathlib import Path
s=json.loads((Path(sys.argv[1])/'before.json').read_text())
assert s['spec']['template']['spec']['containers'][0]['image']==sys.argv[2], 'Live image drift: review first'
t=[t for t in s['status']['traffic'] if t.get('percent')]
assert len(t)==1 and t[0]['percent']==100 and t[0]['revisionName']=='wzos-v2-accounts-flow-354f7a9', 'Traffic drift: review first'
assert s['metadata']['annotations']['run.googleapis.com/ingress']=='internal-and-cloud-load-balancing'
PY
printf 'FROM %s\nUSER root\nCOPY services /app/services\nRUN chmod -R a+rX /app/services\nUSER wzos\n' "$base" > Dockerfile.module-flow
cat > cloudbuild.module-flow.yaml <<'YAML'
steps:
- name: gcr.io/cloud-builders/docker
  args: ['build', '--platform', 'linux/amd64', '-f', 'Dockerfile.module-flow', '-t', '${_IMAGE}', '.']
images: ['${_IMAGE}']
timeout: 600s
options:
  machineType: E2_MEDIUM
YAML
image=us-central1-docker.pkg.dev/$project/$project/wzos-v2-accounts:office-$short
if ! gcloud builds submit --project="$project" --config=cloudbuild.module-flow.yaml --substitutions="_IMAGE=$image" --async --format='value(id)' . > "$root/build-id.txt" 2> "$root/build.log"; then tail -n 12 "$root/build.log"; exit 1; fi
build_id=$(cat "$root/build-id.txt")
for attempt in $(seq 1 70); do
 gcloud builds describe "$build_id" --project="$project" --format=json > "$root/build.json"
 status=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["status"])' "$root/build.json")
 case "$status" in SUCCESS) break;; QUEUED|WORKING|PENDING) sleep 10;; *) echo "BUILD_FAILED $status"; exit 1;; esac
done
python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);b=json.loads((p/'build.json').read_text());assert b['status']=='SUCCESS'
(p/'digest.txt').write_text(b['results']['images'][0]['digest'])
PY
immutable="${image%:*}@$(cat "$root/digest.txt")"
gcloud run deploy "$service" --project="$project" --region="$region" --image="$immutable" --no-traffic --revision-suffix="office-$short" --quiet > "$root/stage.log" 2>&1
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/staged.json"
gcloud run revisions describe "$service-office-$short" --project="$project" --region="$region" --format=json > "$root/revision.json"
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
gcloud run services update-traffic "$service" --project="$project" --region="$region" --to-revisions="$service-office-$short=100" --quiet > "$root/cutover.log" 2>&1
if ! python3 - "$root" <<'PY'
import hashlib,sys,time,urllib.request
from pathlib import Path
root=Path(sys.argv[1]);static=Path('services/workspace_preview/static')
for name in ['workspace.js','workspace.css','organization-hub.js','training-content.js','training-media.js','navigation.js','team-modules.js','dispatch.js','forms-hub.js','forms-hub.css','review-workflows.js','install.js','phone-number.js','manifest.webmanifest']:
 u='https://app.workzoneos.org/'+name+'?release=office-update'
 with urllib.request.urlopen(u,timeout=45) as r: data=r.read();assert r.status==200
 assert hashlib.sha256(data).digest()==hashlib.sha256((static/name).read_bytes()).digest(),name+' asset mismatch'
with urllib.request.urlopen('https://app.workzoneos.org/api/app/version?release=office-update',timeout=30) as r:
 assert r.status==200;version=r.read()
(root/'live-version.json').write_bytes(version)
print('LIVE_OFFICE_SMS_PWA_ASSETS_PASS')
PY
then
 gcloud run services update-traffic "$service" --project="$project" --region="$region" --to-revisions="$service-flow-354f7a9=100" --quiet
 echo ROLLED_BACK_TO_FLOW_354F7A9
 exit 1
fi
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/live.json"
python3 - "$root" "$short" <<'PY'
import json,sys
from pathlib import Path
s=json.loads((Path(sys.argv[1])/'live.json').read_text());assert [(t.get('revisionName'),t.get('percent')) for t in s['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-office-'+sys.argv[2],100)]
print('DEPLOYED_OFFICE_'+sys.argv[2]+'_100_PERCENT')
PY
