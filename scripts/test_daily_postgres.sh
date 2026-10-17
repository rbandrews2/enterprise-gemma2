#!/usr/bin/env bash
# Focused Daily meeting persistence and permission checks in a disposable local cluster.
set -euo pipefail
pg_bin="$(pg_config --bindir)"
for tool in initdb pg_ctl createdb; do test -x "$pg_bin/$tool"; done
cluster=$(mktemp -d /tmp/wzos-pg-gate.XXXXXXXX)
cleanup() {
  "$pg_bin/pg_ctl" -D "$cluster/data" -m immediate -w stop >/dev/null 2>&1 || true
  case "$cluster" in /tmp/wzos-pg-gate.*) rm -rf -- "$cluster";; esac
}
trap cleanup EXIT
mkdir "$cluster/socket"
# Parent directory is mode700. No TCP listener; trust is confined to this user.
"$pg_bin/initdb" -D "$cluster/data" -A trust --no-locale --encoding=UTF8 >/dev/null
"$pg_bin/pg_ctl" -D "$cluster/data" -l "$cluster/server.log" -o "-k $cluster/socket -c listen_addresses=''" -w -t 40 start >/dev/null
"$pg_bin/createdb" -h "$cluster/socket" wzos_test
test -x .venv-accounts-test/bin/python || python3 -m venv .venv-accounts-test
.venv-accounts-test/bin/python -m pip -q install --upgrade pip==26.2.1
.venv-accounts-test/bin/python -m pip -q install -r requirements-accounts.txt
export WZOS_TEST_DATABASE_URL="postgresql:///wzos_test?host=$cluster/socket"
.venv-accounts-test/bin/python - <<'PY'
import os,sys,unittest
sys.path.insert(0,os.getcwd())
suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_daily_meetings.PostgreSQLDailyMeetingTests')
result=unittest.TextTestRunner(verbosity=2).run(suite)
passed=result.testsRun>0 and result.wasSuccessful() and not result.skipped
print('DAILY_POSTGRES_'+('PASS' if passed else 'FAIL')+' run='+str(result.testsRun)+' skipped='+str(len(result.skipped)))
raise SystemExit(0 if passed else 1)
PY
unset WZOS_TEST_DATABASE_URL

