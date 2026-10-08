#!/usr/bin/env bash
# Isolated full-suite PostgreSQL gate. No Google API, paid database, or V1 checkout.
set -euo pipefail
container="wzos-db-test-$(date +%s)-${RANDOM}"
test_password=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
cleanup() { docker rm -f "$container" >/dev/null 2>&1 || true; }
trap cleanup EXIT
# Bound remote image retrieval separately from database startup. Reuse the cached
# image when present; never let an implicit pull hang this gate indefinitely.
image=postgres:16-alpine
if ! docker image inspect "$image" >/dev/null 2>&1; then
  timeout --foreground 300 docker pull "$image" || {
    echo 'PostgreSQL gate blocked: image download failed or exceeded 300 seconds.' >&2
    exit 2
  }
fi
docker run --pull=never -d --name "$container" -e POSTGRES_PASSWORD="$test_password" -e POSTGRES_DB=wzos_test -p 127.0.0.1::5432 "$image" >/dev/null
ready=0
for attempt in $(seq 1 40); do
  if docker exec "$container" pg_isready -U postgres -d wzos_test >/dev/null 2>&1; then ready=1; break; fi
  sleep 1
done
if [ "$ready" != 1 ]; then
  echo 'PostgreSQL gate blocked: database did not become ready within 40 seconds.' >&2
  exit 2
fi
port=$(docker port "$container" 5432/tcp | cut -d: -f2)
test -x .venv-accounts-test/bin/python || python3 -m venv .venv-accounts-test
.venv-accounts-test/bin/pip -q install -r requirements-accounts.txt
export WZOS_TEST_DATABASE_URL="postgresql://postgres:${test_password}@127.0.0.1:${port}/wzos_test"
.venv-accounts-test/bin/python scripts/run_postgres_gate.py
unset WZOS_TEST_DATABASE_URL test_password
