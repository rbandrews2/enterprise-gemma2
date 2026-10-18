#!/usr/bin/env bash
# Requires a separate ongoing-hosting/production activation approval after pilot acceptance.
set -euo pipefail
umask 077
root=${1:?Private evidence directory}
project=enterprise-gemma2; region=us-central1; service=wzos-v2-accounts
test -f "$root/activation-approved"
test "$(cat "$root/node.exit")" = 0; test "$(cat "$root/postgres.exit")" = 0
test "$(cat "$root/pilot.exit")" = 0; test -f "$root/cleanup.verified"
test -f "$root/speech-setup.verified"
source_dir="$root/source"
test "$(git -C "$source_dir" rev-parse HEAD)" = "$(cat "$root/source-commit.txt")"
image=$(cat "$root/app-image.txt"); tag=$(git -C "$source_dir" rev-parse --short=7 HEAD)
[[ "$image" =~ ^us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:[a-f0-9]{64}$ ]]
python3 "$root/check_activation.py" pilot "$root"
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/activation-before.json"
python3 "$root/check_activation.py" baseline "$root"
ready_job=wzos-field-voice-ready
gcloud run services list --project="$project" --region="$region" --filter='metadata.name=wzos-atlas-inference' --format=json > "$root/hosting-preflight.json"
gcloud run jobs list --project="$project" --region="$region" --filter="metadata.name=$ready_job" --format=json > "$root/ready-job-preflight.json"
python3 "$root/check_activation.py" preflight "$root"
# New ongoing workload: same pinned model image/resources as the accepted pilot.
nonce="v20261018-$RANDOM"
printf '%s\n' "$nonce" > "$root/hosting-nonce.txt"
completed=0
cleanup_ready_job() {
 gcloud run jobs list --project="$project" --region="$region" --filter="metadata.name=$ready_job" --format=json > "$root/ready-job-cleanup-before.json"
 if python3 "$root/check_activation.py" ready-job-owner "$root"; then
  gcloud run jobs delete "$ready_job" --project="$project" --region="$region" --quiet > "$root/ready-job-delete.log" 2>&1
 fi
 gcloud run jobs list --project="$project" --region="$region" --filter="metadata.name=$ready_job" --format=json > "$root/ready-job-cleanup-after.json"
 python3 "$root/check_activation.py" ready-job-absent "$root"
}
on_exit() {
 result=$?; trap - EXIT
 if test "$completed" != 1; then
  set +e
  cleanup_ready_job > "$root/ready-job-cleanup.log" 2>&1
  # Disable processing before removing a model created by this activation only.
  if test -f "$root/voice-rollback.sh"; then bash "$root/voice-rollback.sh" > "$root/voice-rollback.log" 2>&1; fi
  gcloud run services describe wzos-atlas-inference --project="$project" --region="$region" --format=json > "$root/hosting-cleanup-before.json" 2>/dev/null
  if python3 "$root/check_activation.py" cleanup-owner "$root"; then
   gcloud run services delete wzos-atlas-inference --project="$project" --region="$region" --quiet > "$root/hosting-cleanup.log" 2>&1
   gcloud run services list --project="$project" --region="$region" --filter='metadata.name=wzos-atlas-inference' --format=json > "$root/hosting-cleanup-after.json"
   python3 "$root/check_activation.py" cleanup-absent "$root" >> "$root/hosting-cleanup.log" 2>&1
  fi
  test "$result" != 0 || result=1
 fi
 exit "$result"
}
trap on_exit EXIT
export ATLAS_TRIAL_LABEL=20261018 ATLAS_TRIAL_NONCE="$nonce"
export ATLAS_MODEL_URI=gs://enterprise-gemma2-atlas-models-us-central1/gemma-4-31B-it/
export ATLAS_RUNTIME_IDENTITY=wzos-atlas-inference@enterprise-gemma2.iam.gserviceaccount.com
export ATLAS_NETWORK=wzos-atlas-vpc ATLAS_SUBNET=wzos-atlas-us-central1
timeout 900 bash "$root/deploy_model.sh" --apply > "$root/hosting-deploy.log" 2>&1
gcloud run services add-iam-policy-binding wzos-atlas-inference --project="$project" --region="$region" \
 --member=serviceAccount:wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com --role=roles/run.invoker --condition=None --quiet > "$root/hosting-invoker.log" 2>&1
gcloud run services describe wzos-atlas-inference --project="$project" --region="$region" --format=json > "$root/hosting-ready.json"
gcloud run services get-iam-policy wzos-atlas-inference --project="$project" --region="$region" --format=json > "$root/hosting-iam.json"
python3 "$root/check_activation.py" model "$root"
origin=$(cat "$root/hosting-url.txt")
job_image=$(cat "$root/job-image.txt")
test "$job_image" = us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-field-voice-pilot@sha256:10382d00e3a792c41f17829b3262048173713711218d735c87dfa97ff29f1ed8
timeout 120 gcloud run jobs create "$ready_job" --project="$project" --region="$region" --image="$job_image" \
 --service-account=wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com --labels="wzos-pilot=$nonce" \
 --tasks=1 --parallelism=1 --max-retries=0 --task-timeout=240s --cpu=1 --memory=512Mi \
 --set-env-vars="WZOS_FIELD_VOICE_MODEL_URL=$origin" --command=python \
 --args="^~^-c~$(cat "$root/check_identity.py")" --quiet > "$root/ready-job-create.log" 2>&1
gcloud run jobs describe "$ready_job" --project="$project" --region="$region" --format=json > "$root/ready-job-config.json"
python3 "$root/check_activation.py" ready-job "$root"
timeout 360 gcloud run jobs execute "$ready_job" --project="$project" --region="$region" --wait --quiet --format=json > "$root/ready-job-execution.json" 2> "$root/ready-job-execution.log"
python3 "$root/check_activation.py" ready-execution "$root"
cleanup_ready_job > "$root/ready-job-cleanup.log" 2>&1
for mode in hold live; do
 enabled=0; test "$mode" != live || enabled=1
 gcloud run deploy "$service" --project="$project" --region="$region" --image="$image" --no-traffic \
  --revision-suffix="voice-$mode-$tag" \
  --update-env-vars="WZOS_FIELD_VOICE_ENABLED=$enabled,WZOS_FIELD_VOICE_SPEECH_ENABLED=$enabled,WZOS_FIELD_VOICE_MODEL_ENABLED=$enabled,WZOS_FIELD_VOICE_MODEL_URL=$origin" \
  --quiet > "$root/voice-$mode-stage.log" 2>&1
 gcloud run revisions describe "$service-voice-$mode-$tag" --project="$project" --region="$region" --format=json > "$root/voice-$mode-revision.json"
done
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/voice-staged.json"
python3 "$root/check_activation.py" staged "$root"
printf 'gcloud run services update-traffic %s --project=%s --region=%s --to-revisions=%s-voice-hold-%s=100 --quiet\n' "$service" "$project" "$region" "$service" "$tag" > "$root/voice-rollback.sh"
gcloud run services update-traffic "$service" --project="$project" --region="$region" --to-revisions="$service-voice-live-$tag=100" --quiet > "$root/voice-cutover.log" 2>&1
if ! python3 "$root/check_activation.py" public "$root"; then
 bash "$root/voice-rollback.sh" > "$root/voice-rollback.log" 2>&1
 echo FIELD_VOICE_DISABLED_ON_COMPATIBLE_IMAGE; exit 1
fi
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/voice-live.json"
python3 "$root/check_activation.py" traffic "$root"
completed=1
echo FIELD_VOICE_PRODUCTION_ACTIVATED
