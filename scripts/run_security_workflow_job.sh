#!/usr/bin/env bash
# Requires action-time approval: new job uses the existing app runtime identity.
# No new IAM grants, secret bindings, public endpoint or production schema writes.
set -euo pipefail
umask 077
evidence=${1:?Private evidence directory required}
image=${WZOS_SECURITY_WORKFLOW_IMAGE:?Reviewed immutable test image required}
[[ $image =~ ^us-central1-docker\.pkg\.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-security-workflow@sha256:[0-9a-f]{64}$ ]] || exit 2
test "$(gcloud config get-value project 2>/dev/null)" = enterprise-gemma2
mkdir -p "$evidence"; evidence=$(realpath "$evidence")
printf '%s\n' "$image" > "$evidence/image.txt"
job=wzos-security-workflow
existing=$(timeout 60 gcloud run jobs list --project=enterprise-gemma2 --region=us-central1 --filter="metadata.name=$job" --format='value(metadata.name)')
test -z "$existing" || { printf 'EXISTING_JOB_REQUIRES_REVIEW\n'; exit 2; }
created=0
cleanup() {
  result=$?
  trap - EXIT
  if [[ $created = 1 ]]; then
    if timeout 90 gcloud run jobs delete "$job" --project=enterprise-gemma2 --region=us-central1 --quiet --format=none > "$evidence/job-removal.log" 2>&1; then
      printf 'WORKFLOW_JOB_REMOVED\n'
    else
      printf 'WORKFLOW_JOB_REMOVAL_NEEDS_VERIFICATION\n'
      result=1
    fi
  fi
  printf '%s\n' "$result" > "$evidence/job.exit"
  exit "$result"
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
# Set before creation so an uncertain CLI outcome still triggers cleanup of this
# newly reserved name. Pre-existing jobs were rejected above.
created=1
timeout 120 gcloud run jobs create "$job" --project=enterprise-gemma2 --region=us-central1 \
  --image="$image" --service-account=wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com \
  --tasks=1 --parallelism=1 --max-retries=0 --task-timeout=300s --cpu=1 --memory=512Mi \
  --quiet --format=json > "$evidence/job-created.json"
timeout 60 gcloud run jobs describe "$job" --project=enterprise-gemma2 --region=us-central1 --format=json > "$evidence/job-config.json"
python3 - "$evidence/job-config.json" "$image" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))['spec']['template']['spec']
task=x['template']['spec']
assert x['taskCount']==1 and x.get('parallelism',1)==1
assert task['serviceAccountName']=='wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com'
# Cloud Run v1 serializes its int64 timeout as a JSON string.
assert task['maxRetries']==0 and str(task['timeoutSeconds'])=='300'
c=task['containers'][0]
assert len(task['containers'])==1 and c['image']==sys.argv[2]
assert not c.get('env') and not c.get('volumeMounts') and not task.get('volumes')
assert c['resources']['limits']['cpu'] in ('1','1000m')
assert c['resources']['limits']['memory']=='512Mi'
PY
printf 'WORKFLOW_JOB_CONFIG_VERIFIED\n'
timeout 420 gcloud run jobs execute "$job" --project=enterprise-gemma2 --region=us-central1 --wait --quiet --format=json > "$evidence/execution.json" 2> "$evidence/execution-command.log"
timeout 60 gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="wzos-security-workflow"' \
  --project=enterprise-gemma2 --freshness=20m --limit=100 --format=json > "$evidence/logs.json"
python3 - "$evidence/logs.json" "$evidence/execution.json" <<'PY'
import json,sys
logs=json.load(open(sys.argv[1])); execution=json.load(open(sys.argv[2]))
name=execution['metadata']['name']
entries=[x for x in logs if x.get('labels',{}).get('run.googleapis.com/execution_name')==name]
lines=[x.get('textPayload','') for x in entries]
passed=[line for line in lines if line.startswith('SECURITY_WORKFLOW_PASS ')]
assert len(passed)==1,'Missing live workflow result; inspect preserved evidence'
result=json.loads(passed[0].split(' ',1)[1])
assert result['mode']=='live' and result['identity']=='Google metadata' and result['passed']==29
assert execution['status'].get('succeededCount')==1 and not execution['status'].get('failedCount')
print(passed[0])
PY
