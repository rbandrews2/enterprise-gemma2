#!/usr/bin/env bash
# Private, disposable databases only. Does not restore or connect to production.
set -euo pipefail
umask 077
evidence=${1:?existing private evidence directory}
test -d "$evidence"
test -x .venv-accounts-test/bin/python
pg_bin=$(pg_config --bindir)
for tool in initdb pg_ctl createdb pg_dump pg_restore; do test -x "$pg_bin/$tool"; done
cluster=$(mktemp -d /tmp/wzos-pg-restore.XXXXXXXX)
cleanup() {
 "$pg_bin/pg_ctl" -D "$cluster/data" -m immediate -w stop >/dev/null 2>&1 || true
 case "$cluster" in /tmp/wzos-pg-restore.*) rm -rf -- "$cluster";; esac
}
trap cleanup EXIT
mkdir "$cluster/socket"
"$pg_bin/initdb" -D "$cluster/data" -A trust --no-locale --encoding=UTF8 >/dev/null
"$pg_bin/pg_ctl" -D "$cluster/data" -l "$cluster/server.log" -o "-k $cluster/socket -c listen_addresses=''" -w -t 40 start >/dev/null
"$pg_bin/createdb" -h "$cluster/socket" wzos_restore_source
export WZOS_TEST_DATABASE_URL="postgresql:///wzos_restore_source?host=$cluster/socket"
.venv-accounts-test/bin/python scripts/check_signed_form_restore.py seed "$evidence/signed-restore.json"
"$pg_bin/pg_dump" --no-owner --no-acl --format=custom --file="$cluster/synthetic.dump" --dbname="$WZOS_TEST_DATABASE_URL"
"$pg_bin/createdb" -h "$cluster/socket" wzos_restore_target
export WZOS_TEST_DATABASE_URL="postgresql:///wzos_restore_target?host=$cluster/socket"
"$pg_bin/pg_restore" --no-owner --no-acl --exit-on-error --dbname="$WZOS_TEST_DATABASE_URL" "$cluster/synthetic.dump"
.venv-accounts-test/bin/python scripts/check_signed_form_restore.py check "$evidence/signed-restore.json"
unset WZOS_TEST_DATABASE_URL
echo SIGNED_FORM_DISPOSABLE_RESTORE_PASS
