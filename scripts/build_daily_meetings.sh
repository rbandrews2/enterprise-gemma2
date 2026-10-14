#!/usr/bin/env bash
# Build only. Preserve the verified source library in the current immutable image.
set -euo pipefail
umask 077
revision=8720bbed00e91103e1dfa33ff7288ed153225473
evidence="$HOME/wzos-daily-20261014"
repo=$(cat "$evidence/gate-path.txt")
test "$(git -C "$repo" rev-parse HEAD)" = "$revision"
grep -Fxq 'PostgreSQL gate: PASS; run=575, failures=0, errors=0, skipped=0' "$evidence/final-gate-and-provider.log"
grep -Fxq 'DAILY_PRIVATE_ROOM_AND_TOKEN_PASS: no media joined' "$evidence/final-gate-and-provider.log"
grep -Fxq 'DAILY_ROOM_EXPIRY_UPDATE_PASS: active-media ejection still requires device test' "$evidence/final-gate-and-provider.log"
grep -Fxq 'DAILY_SYNTHETIC_ROOM_REMOVED' "$evidence/final-gate-and-provider.log"
if pgrep -x postgres >/dev/null; then echo 'Build paused: inspect database test cleanup';exit 1;fi
base=us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:37045d3a9076c38e76a1c900546517fffc3faac07d7778cff91757bf87a31111
context=$(mktemp -d "$evidence/context-daily.XXXXXXXX")
git -C "$repo" archive "$revision" services/workspace_preview/app.py services/workspace_preview/modules.py \
 services/workspace_preview/daily_meetings.py services/workspace_preview/static/index.html \
 services/workspace_preview/static/modules.js services/workspace_preview/static/workspace.css \
 services/workspace_preview/static/daily-meetings.js services/workspace_preview/static/vendor | tar -x -C "$context"
cat > "$context/Dockerfile" <<DOCKER
FROM $base
COPY --chown=wzos:wzos services/workspace_preview/app.py services/workspace_preview/modules.py services/workspace_preview/daily_meetings.py /app/services/workspace_preview/
COPY --chown=wzos:wzos services/workspace_preview/static/ /app/services/workspace_preview/static/
RUN python /app/scripts/package_source_library.py --verify /app/.local-data/knowledge
DOCKER
gcloud builds submit "$context" --project enterprise-gemma2 --async --quiet \
 --tag us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts:8720bbe-daily \
 --format='value(id)' > "$evidence/build.id"
printf 'DAILY_BUILD_SUBMITTED ';cat "$evidence/build.id"
