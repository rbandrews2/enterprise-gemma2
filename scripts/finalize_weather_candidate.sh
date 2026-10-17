#!/usr/bin/env bash
# Preserve full-suite evidence, then test only the final weather delta and build.
set -euo pipefail
umask 077
source_commit=${1:?Exact final source required}
[[ "$source_commit" =~ ^[0-9a-f]{40}$ ]]
root=$(cat "$HOME/wzos-weather-path.txt")
test "$(cat "$root/gate.exit")" = 0
grep -q 'PostgreSQL gate: PASS;' "$root/postgres.log"
test ! -f "$root/full-gate.exit"
cp "$root/gate.exit" "$root/full-gate.exit"
cp "$root/postgres.log" "$root/full-postgres.log"
git -C "$root/source" rev-parse HEAD > "$root/full-tested-source.txt"
git -C "$root/source" fetch --quiet origin codex/preproduction-modules
git -C "$root/source" checkout --quiet --detach "$source_commit"
cd "$root/source"
bash -n scripts/test_weather_postgres.sh scripts/build_weather_release.sh scripts/deploy_weather_release.sh
set +e
bash scripts/test_weather_postgres.sh > "$root/weather-postgres.log" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$root/gate.exit"
test "$result" = 0
printf '%s\n' "$source_commit" > "$root/tested-source.txt"
set +e
bash scripts/build_weather_release.sh "$source_commit" > "$root/build-release.log" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$root/build.exit"
test "$result" = 0
echo WEATHER_CANDIDATE_READY
