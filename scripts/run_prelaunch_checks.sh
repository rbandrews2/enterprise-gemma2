#!/usr/bin/env bash
# Read-only cloud state is separate; these suites use synthetic/disposable data only.
set -euo pipefail
umask 077
root=${1:?existing private evidence directory}
cd "$root/source"
test "$(git rev-parse HEAD)" = "$(cat "$root/source-commit.txt")"
trap 'printf "%s\n" "$?" > "$root/checks.exit"' EXIT
node --test tests/*.test.cjs > "$root/node.log" 2>&1 && result=0 || result=$?
printf '%s\n' "$result" > "$root/node.exit"
test "$result" = 0
bash scripts/test_postgres_native.sh > "$root/postgres.log" 2>&1 && result=0 || result=$?
printf '%s\n' "$result" > "$root/postgres.exit"
test "$result" = 0
bash scripts/test_signed_form_restore.sh "$root" > "$root/restore.log" 2>&1 && result=0 || result=$?
printf '%s\n' "$result" > "$root/restore.exit"
test "$result" = 0
echo PRELAUNCH_SYNTHETIC_GATES_AND_RESTORE_PASS
