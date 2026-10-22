#!/usr/bin/env bash
# One focused gate/build/deploy pipeline, with durable exit evidence.
set -euo pipefail
umask 077
root=${1:?evidence directory}
trap 'result=$?; printf "%s\n" "$result" > "$root/deploy.exit"' EXIT
cd "$root/source"
test "$(git rev-parse HEAD)" = "$(cat "$root/source-commit.txt")"
test "$(gcloud config get-value project 2>/dev/null)" = enterprise-gemma2
printf '%s\n' "$(git rev-parse HEAD)" > "$root/tested-source.txt"
node --test tests/training-links.test.cjs tests/training-media.test.cjs > "$root/node.log" 2>&1 && result=0 || result=$?
printf '%s\n' "$result" > "$root/node.exit"
test "$result" = 0
bash scripts/test_training_postgres.sh > "$root/postgres.log" 2>&1 && result=0 || result=$?
printf '%s\n' "$result" > "$root/postgres.exit"
test "$result" = 0
echo TRAINING_FOCUSED_GATES_PASS
bash scripts/release_training_update.sh build "$root"
for attempt in $(seq 1 60); do
 status=$(gcloud builds describe "$(cat "$root/build-id.txt")" --project=enterprise-gemma2 --format='value(status)')
 case "$status" in
  SUCCESS) bash scripts/release_training_update.sh deploy "$root"; exit 0;;
  FAILURE|TIMEOUT|CANCELLED|EXPIRED) echo "Build stopped: $status"; exit 1;;
 esac
 sleep 10
done
echo BUILD_WAIT_EXCEEDED
exit 1
