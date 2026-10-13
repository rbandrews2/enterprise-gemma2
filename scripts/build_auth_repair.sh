#!/usr/bin/env bash
# Build only: overlay tested frontend onto the previous immutable private image.
set -euo pipefail
umask 077
revision=bf77c91202f1b59245a56a07d734d74a51fae690
evidence="$HOME/wzos-release-20261012"
repo="$HOME/wzos-auth-repair-bf77c91"
registry=us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts
test "$(git -C "$repo" rev-parse HEAD)" = "$revision"
grep -Fxq 'PostgreSQL gate: PASS; run=498, failures=0, errors=0, skipped=0' "$evidence/postgres-bf77c91.log"
if pgrep -x postgres >/dev/null; then
  printf 'Build paused: PostgreSQL processes remain; inspect cleanup without killing unrelated databases.\n' >&2
  exit 1
fi
base=$(tr -d '\r\n' < "$evidence/image-2b42560.digest")
if [[ "$base" =~ ^sha256:[a-f0-9]{64}$ ]]; then base="$registry@$base"; fi
[[ "$base" =~ ^us-central1-docker\.pkg\.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:[a-f0-9]{64}$ ]] || {
  printf 'Unexpected base image; no build submitted.\n' >&2; exit 1;
}
context=$(mktemp -d "$evidence/context-bf77c91.XXXXXXXX")
git -C "$repo" archive "$revision" services/workspace_preview/static/account.js services/workspace_preview/static/workspace.js | tar -x -C "$context"
cat > "$context/Dockerfile" <<DOCKER
FROM $base
COPY --chown=wzos:wzos services/workspace_preview/static/account.js /app/services/workspace_preview/static/account.js
COPY --chown=wzos:wzos services/workspace_preview/static/workspace.js /app/services/workspace_preview/static/workspace.js
RUN python /app/scripts/package_source_library.py --verify /app/.local-data/knowledge
DOCKER
gcloud builds submit "$context" --project=enterprise-gemma2 --tag="$registry:bf77c91-auth-repair" --async --quiet --format='value(id)' > "$evidence/build-bf77c91.id"
printf 'BUILD_SUBMITTED_ID '
cat "$evidence/build-bf77c91.id"
printf '\nBuild only; no service deployment, traffic or IAM change.\n'
