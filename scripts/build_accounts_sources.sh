#!/usr/bin/env bash
# Build only, from a verified official-source snapshot; never changes a service.
set -euo pipefail
snapshot="${1:?Pass verified snapshot directory}"
python_bin="${WZOS_BUILD_PYTHON:-python3}"
source_image=${WZOS_SOURCE_LIBRARY_IMAGE:-}
if [[ -n $source_image ]]; then
  [[ $source_image =~ ^us-central1-docker\.pkg\.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:[0-9a-f]{64}$ ]] || exit 2
fi
"$python_bin" scripts/package_source_library.py --verify "$snapshot"
manifest_sha=$("$python_bin" -c 'import hashlib,sys; from pathlib import Path; print(hashlib.sha256((Path(sys.argv[1])/"snapshot.json").read_bytes()).hexdigest())' "$snapshot")
[[ -z $(git status --porcelain) ]] || { echo 'Commit source before building'; exit 1; }
revision=$(git rev-parse --short=12 HEAD)
context=$(mktemp -d /tmp/wzos-sources-build-XXXXXX)
cleanup() {
  case "$context" in /tmp/wzos-sources-build-*) rm -rf -- "$context";; esac
}
trap cleanup EXIT
git archive HEAD Dockerfile.accounts requirements-v2.txt requirements-accounts.txt services shared knowledge scripts/package_source_library.py | tar -x -C "$context"
mv "$context/Dockerfile.accounts" "$context/Dockerfile"
if [[ -n $source_image ]]; then
  # Reuse ONLY the official reference library, never old executable code/config.
  # Exact manifest equality plus the full file verifier below prevents stale data.
  { printf 'FROM %s AS verified_source_library\n' "$source_image"; cat "$context/Dockerfile"; } > "$context/Dockerfile.next"
  mv "$context/Dockerfile.next" "$context/Dockerfile"
  printf '\nCOPY --from=verified_source_library --chown=wzos:wzos /app/.local-data/knowledge /app/.local-data/knowledge\n' >> "$context/Dockerfile"
else
  cp -R "$snapshot" "$context/source-library"
  printf '\nCOPY --chown=wzos:wzos source-library /app/.local-data/knowledge\n' >> "$context/Dockerfile"
fi
printf "RUN python -c 'import hashlib; from pathlib import Path; assert hashlib.sha256(Path(\"/app/.local-data/knowledge/snapshot.json\").read_bytes()).hexdigest() == \"%s\"'\n" "$manifest_sha" >> "$context/Dockerfile"
cat >> "$context/Dockerfile" <<'DOCKER'

COPY scripts/package_source_library.py /app/scripts/package_source_library.py
RUN python /app/scripts/package_source_library.py --verify /app/.local-data/knowledge
DOCKER
timeout 300 gcloud builds submit "$context" --project enterprise-gemma2 --region=us-central1 --timeout=900s \
  --tag "us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts:${revision}-sources" --async --quiet
