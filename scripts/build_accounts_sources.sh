#!/usr/bin/env bash
# Build only, from a verified official-source snapshot; never changes a service.
set -euo pipefail
snapshot="${1:?Pass verified snapshot directory}"
python_bin="${WZOS_BUILD_PYTHON:-python3}"
"$python_bin" scripts/package_source_library.py --verify "$snapshot"
[[ -z $(git status --porcelain) ]] || { echo 'Commit source before building'; exit 1; }
revision=$(git rev-parse --short=12 HEAD)
context=$(mktemp -d /tmp/wzos-sources-build-XXXXXX)
git archive HEAD Dockerfile.accounts requirements-v2.txt requirements-accounts.txt services shared knowledge scripts/package_source_library.py | tar -x -C "$context"
mv "$context/Dockerfile.accounts" "$context/Dockerfile"
cp -R "$snapshot" "$context/source-library"
cat >> "$context/Dockerfile" <<'DOCKER'

COPY --chown=wzos:wzos source-library /app/.local-data/knowledge
COPY scripts/package_source_library.py /app/scripts/package_source_library.py
RUN python /app/scripts/package_source_library.py --verify /app/.local-data/knowledge
DOCKER
gcloud builds submit "$context" --project enterprise-gemma2 \
  --tag "us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts:${revision}-sources" --async --quiet
