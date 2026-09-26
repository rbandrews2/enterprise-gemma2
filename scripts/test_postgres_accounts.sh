#!/usr/bin/env bash
# Isolated synthetic PostgreSQL test. No Google API, paid database, or V1 checkout.
set -euo pipefail
container="wzos-db-test-$(date +%s)-${RANDOM}"
test_password=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
cleanup() { docker rm -f "$container" >/dev/null 2>&1 || true; }
trap cleanup EXIT
docker run -d --name "$container" -e POSTGRES_PASSWORD="$test_password" -e POSTGRES_DB=wzos_test -p 127.0.0.1::5432 postgres:16-alpine >/dev/null
for attempt in $(seq 1 40); do
  if docker exec "$container" pg_isready -U postgres -d wzos_test >/dev/null 2>&1; then break; fi
  sleep 1
done
port=$(docker port "$container" 5432/tcp | cut -d: -f2)
python3 -m venv .venv-accounts-test
.venv-accounts-test/bin/pip -q install -r requirements-accounts.txt
export WZOS_TEST_DATABASE_URL="postgresql://postgres:${test_password}@127.0.0.1:${port}/wzos_test"
.venv-accounts-test/bin/python -m unittest discover -s tests -p test_accounts_storage.py -v
unset WZOS_TEST_DATABASE_URL test_password
