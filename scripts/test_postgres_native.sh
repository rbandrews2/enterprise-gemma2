#!/usr/bin/env bash
# Reuse preinstalled PostgreSQL binaries; isolated loopback-only temporary cluster.
set -euo pipefail
pg_bin=${WZOS_PG_BIN:?Set WZOS_PG_BIN to the installed PostgreSQL bin directory}
test_root=$(mktemp -d -t wzos-pg-native-XXXXXXXX)
chmod 700 "$test_root"
test_password=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
umask 077
printf '%s' "$test_password" > "$test_root/password"
port=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')
cleanup() { "$pg_bin/pg_ctl" -D "$test_root/data" -m fast -w stop >/dev/null 2>&1 || true; rm -f "$test_root/password"; }
trap cleanup EXIT
"$pg_bin/initdb" -D "$test_root/data" -U wzos_test --auth=scram-sha-256 --pwfile="$test_root/password" >/dev/null
"$pg_bin/pg_ctl" -D "$test_root/data" -l "$test_root/server.log" -o "-h 127.0.0.1 -p $port -k $test_root" -w start >/dev/null
python3 -m venv .venv-accounts-test
.venv-accounts-test/bin/pip -q install -r requirements-accounts.txt
export WZOS_TEST_DATABASE_URL="postgresql://wzos_test:${test_password}@127.0.0.1:${port}/postgres"
.venv-accounts-test/bin/python -m unittest discover -s tests -p test_accounts_storage.py -v
unset WZOS_TEST_DATABASE_URL test_password
