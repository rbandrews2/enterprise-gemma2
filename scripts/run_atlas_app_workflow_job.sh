#!/usr/bin/env bash
# Approved only with the guarded parent pilot; never call from a serving app.
set -euo pipefail
umask 077
root=${1:?Private evidence directory required}
image=$(cat "$root/workflow-image.txt")
origin=$(cat "$root/model-url.txt")
nonce=$(cat "$root/pilot-nonce.txt")
[[ "$nonce" =~ ^p[0-9]+-[0-9]+$ ]]
[[ "$origin" =~ ^https://[a-z0-9.-]+\.run\.app$ ]]
[[ "$image" = 'us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-atlas-app-workflow@sha256:eaa44f814c0917c2719ba0c09a1b34849145f2cc27ba9130a16153a094d4571d' ]]
kill -0 "$(cat "$root/guard.pid")"
timeout 120 gcloud run jobs create wzos-atlas-app-workflow --project=enterprise-gemma2 --region=us-central1 \
 --image="$image" --service-account=wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com \
 --labels="wzos-pilot=$nonce" --tasks=1 --parallelism=1 --max-retries=0 \
 --task-timeout=300s --cpu=1 --memory=512Mi \
 --set-env-vars="WZOS_ATLAS_VLLM_URL=$origin" --quiet --format=json > "$root/job-created.json"
gcloud run jobs describe wzos-atlas-app-workflow --project=enterprise-gemma2 --region=us-central1 --format=json > "$root/job-config.json"
python3 - "$root" "$image" "$origin" "$nonce" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); job=json.loads((p/'job-config.json').read_text())
assert job['metadata']['labels']['wzos-pilot']==sys.argv[4]
x=job['spec']['template']['spec']; task=x['template']['spec']; c=task['containers'][0]
assert x['taskCount']==1 and x.get('parallelism',1)==1
assert task['serviceAccountName']=='wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com'
assert task['maxRetries']==0 and str(task['timeoutSeconds'])=='300'
assert len(task['containers'])==1 and c['image']==sys.argv[2]
assert not c.get('volumeMounts') and not task.get('volumes')
assert c.get('env')==[{'name':'WZOS_ATLAS_VLLM_URL','value':sys.argv[3]}]
assert c['resources']['limits']['cpu'] in ('1','1000m') and c['resources']['limits']['memory']=='512Mi'
print('ATLAS_APP_JOB_CONFIG_VERIFIED')
PY
timeout 420 gcloud run jobs execute wzos-atlas-app-workflow --project=enterprise-gemma2 --region=us-central1 \
 --wait --quiet --format=json > "$root/execution.json" 2> "$root/execution-command.log"
execution=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["metadata"]["name"])' "$root/execution.json")
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=wzos-atlas-app-workflow AND labels.\"run.googleapis.com/execution_name\"=$execution" \
 --project=enterprise-gemma2 --freshness=20m --order=asc --limit=200 --format=json > "$root/workflow-logs.json"
python3 - "$root" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); execution=json.loads((p/'execution.json').read_text())
assert execution['status'].get('succeededCount')==1 and not execution['status'].get('failedCount')
logs=json.loads((p/'workflow-logs.json').read_text())
rows=[r for r in logs if r.get('labels',{}).get('run.googleapis.com/execution_name')==execution['metadata']['name'] and r.get('logName','').endswith('stdout')]
structured=[r['jsonPayload'] for r in rows if 'jsonPayload' in r]
result=structured[0] if len(structured)==1 else json.loads('\n'.join(r.get('textPayload','') for r in rows))
assert result['mode']=='live' and result['identity']=='Google metadata'
assert result['model_requests']==2 and result['synthetic_sources_only']
assert len(result['checks'])==5
assert [r['status'] for r in result['checks'][:3]]==[409,404,403]
(p/'workflow-result.json').write_text(json.dumps(result,indent=2))
print('ATLAS_APP_WORKFLOW_PASS '+json.dumps(result))
PY
