#!/usr/bin/env bash
# Separately approved sequence: prove vocabulary recognition before any GPU spend.
set -euo pipefail
umask 077
root=${1:?Private evidence directory}
test -f "$root/combined-pilot-approved"
test ! -f "$root/combined-pilot.started"
test -f "$root/speech-pilot-approved"; test -f "$root/model-approved"; test -f "$root/job-approved"
test "$(cat "$root/speech-model.txt")" = long
date -u > "$root/combined-pilot.started"
bash "$root/run_speech.sh" run "$root"
test "$(cat "$root/speech-pilot.exit")" = 0
test "$(cat "$root/speech-cleanup.verified")" = 0
# This helper owns its one-hour guard, exact identity/config checks and cleanup.
bash "$root/run_pilot.sh" run "$root"
test "$(cat "$root/pilot.exit")" = 0
test "$(cat "$root/cleanup.verified")" = 0
echo FIELD_VOICE_PROVIDER_ACCEPTANCE_PASS
