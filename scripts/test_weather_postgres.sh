#!/usr/bin/env bash
# Focused final weather delta, using disposable PostgreSQL; does not deploy.
set -euo pipefail
pg_bin=$(pg_config --bindir)
cluster=$(mktemp -d /tmp/wzos-weather-pg.XXXXXXXX)
cleanup() {
 "$pg_bin/pg_ctl" -D "$cluster/data" -m immediate -w stop >/dev/null 2>&1 || true
 case "$cluster" in /tmp/wzos-weather-pg.*) rm -rf -- "$cluster";; esac
}
trap cleanup EXIT
mkdir "$cluster/socket"
"$pg_bin/initdb" -D "$cluster/data" -A trust --no-locale --encoding=UTF8 >/dev/null
"$pg_bin/pg_ctl" -D "$cluster/data" -l "$cluster/server.log" -o "-k $cluster/socket -c listen_addresses=''" -w -t 40 start >/dev/null
"$pg_bin/createdb" -h "$cluster/socket" wzos_weather_test
export WZOS_TEST_DATABASE_URL="postgresql:///wzos_weather_test?host=$cluster/socket"
.venv-accounts-test/bin/python - <<'PY'
import unittest
suite=unittest.TestLoader().discover('tests',pattern='test_weather.py')
result=unittest.TextTestRunner(verbosity=2).run(suite)
passed=result.wasSuccessful() and not result.skipped and result.testsRun>=20
print(f'WEATHER_POSTGRES_{"PASS" if passed else "FAIL"} run={result.testsRun} skipped={len(result.skipped)}')
raise SystemExit(0 if passed else 1)
PY
