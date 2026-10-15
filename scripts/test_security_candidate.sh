#!/usr/bin/env bash
# Disposable exact-source regression run. No cloud provisioning or deployment.
set -euo pipefail
umask 077
candidate=${1:?Pass the exact 40-character commit SHA}
[[ $candidate =~ ^[0-9a-f]{40}$ ]] || { echo 'Invalid candidate SHA'; exit 2; }
run_dir=$(mktemp -d "$HOME/wzos-security-20261015.XXXXXXXX")
printf '%s\n' "$run_dir" > "$HOME/wzos-security-latest-path.txt"
printf 'SECURITY_GATE_DIRECTORY %s\n' "$run_dir"
trap 'result=$?; printf "%s\n" "$result" > "$run_dir/gate.exit"' EXIT
git clone --quiet --single-branch --branch codex/preproduction-modules \
  https://github.com/rbandrews2/enterprise-gemma2.git "$run_dir/repo"
cd "$run_dir/repo"
git checkout --quiet --detach "$candidate"
test "$(git rev-parse HEAD)" = "$candidate"
git rev-parse HEAD > "$run_dir/source.txt"
timeout 120 node --test tests/*.test.cjs > "$run_dir/node.log" 2>&1
timeout 900 bash scripts/test_postgres_native.sh > "$run_dir/postgres.log" 2>&1
tail -n 10 "$run_dir/node.log"
tail -n 8 "$run_dir/postgres.log"
printf 'SECURITY_CANDIDATE_GATE_PASS\n'
