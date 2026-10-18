#!/usr/bin/env bash
# Builds a harness-only repair; keeps the fully tested application image unchanged.
set -euo pipefail
umask 077
root=${1:?Private evidence directory}; helper_dir=$(cd "$(dirname "$0")" && pwd)
test "$(cat "$root/node.exit")" = 0; test "$(cat "$root/postgres.exit")" = 0
test "$(cat "$root/cleanup.verified")" = 0
test "$(gcloud config get-value project 2>/dev/null)" = enterprise-gemma2
context=$(mktemp -d /tmp/wzos-voice-harness.XXXXXXXX)
cp "$helper_dir/check_field_voice_workflow.py" "$context/"
base=$(cat "$root/app-image.txt")
test "$base" = us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:798c479ccdae437d4929b0903379df598c26f7ac6e37f8977c9e5e354566ebf9
cp -r /tmp/wzos-field-voice.7uMHJJrD/audio "$context/pilot-audio"
printf 'FROM %s\nUSER root\nCOPY check_field_voice_workflow.py /app/scripts/check_field_voice_workflow.py\nCOPY pilot-audio /app/pilot-audio\nRUN chmod -R a+rX /app/scripts/check_field_voice_workflow.py /app/pilot-audio\nUSER wzos\nENTRYPOINT ["python","/app/scripts/check_field_voice_workflow.py"]\nCMD ["--audio-root","/app/pilot-audio"]\n' "$base" > "$context/Dockerfile"
tag=$(sha256sum "$context/check_field_voice_workflow.py" | cut -c1-12)
image=us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-field-voice-pilot:auth-ready-$tag
printf '%s\n' "$image" > "$root/retest-job-tag.txt"
gcloud builds submit "$context" --project=enterprise-gemma2 --tag="$image" --timeout=600s --async --format='value(id)' > "$root/retest-build-id.txt" 2> "$root/retest-build-submit.log"
echo FIELD_VOICE_RETEST_BUILD_SUBMITTED
cat "$root/retest-build-id.txt"
