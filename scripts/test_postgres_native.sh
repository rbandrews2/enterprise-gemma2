#!/usr/bin/env bash
# Disposable private Unix-socket PostgreSQL cluster using an existing installation.
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
.venv-accounts-test/bin/pip -q install -r requirements-accounts.txt
export WZOS_TEST_DATABASE_URL="postgresql:///wzos_test?host=$cluster/socket"
.venv-accounts-test/bin/python scripts/run_postgres_gate.py
unset WZOS_TEST_DATABASE_URL

