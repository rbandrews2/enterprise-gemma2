#!/usr/bin/env bash
# OS security updates only; preserve the already tested application and sources.
set -euo pipefail
umask 077
evidence="$HOME/wzos-hub-rollout-20261014"
context=$(mktemp -d "$evidence/os-context.XXXXXXXX")
cat > "$context/Dockerfile" <<'DOCKER'
FROM us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:4cc2f391151e1aaf00d9ad29bc68c57779b808f75ed9034f23e3bcbb3af71bdd
USER root
RUN apt-get update && apt-get -y upgrade && rm -rf /var/lib/apt/lists/* \
    && dpkg --compare-versions "$(dpkg-query -W -f='${Version}' libpcre2-8-0)" ge '10.46-1~deb13u3'
USER wzos
RUN python /app/scripts/package_source_library.py --verify /app/.local-data/knowledge
DOCKER
python3 - "$context/cloudbuild.json" <<'PY'
import json,sys
image='us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts:5a3ac86-hub-os'
steps=[
 {'name':'gcr.io/cloud-builders/docker','args':['build','--tag',image,'.']},
 {'name':'gcr.io/cloud-builders/docker','args':['run','--rm','--entrypoint','python',image,'/app/scripts/check_hub_image.py']},
 {'name':'gcr.io/cloud-builders/docker','args':['run','--rm','--entrypoint','sh',image,'-c',
  'python -m pip check; python -m pip freeze --all; dpkg-query -W; python -c "import zlib; print(\"ZLIB_RUNTIME\",zlib.ZLIB_RUNTIME_VERSION)"; if perl -MArchive::Tar -e 1 >/dev/null 2>&1; then echo PERL_ARCHIVE_TAR_PRESENT; else echo PERL_ARCHIVE_TAR_ABSENT; fi; for tool in getfattr setfattr getfacl setfacl; do if command -v "$tool" >/dev/null; then echo "ACL_ATTR_TOOL_PRESENT $tool"; else echo "ACL_ATTR_TOOL_ABSENT $tool"; fi; done'.replace('$','$$')]},
]
json.dump({'steps':steps,'images':[image],'timeout':'1200s'},open(sys.argv[1],'w'),indent=2)
PY
gcloud builds submit "$context" --project enterprise-gemma2 --config "$context/cloudbuild.json" --async --quiet --format='value(id)' > "$evidence/os-build.id"
printf 'HUB_OS_BUILD_SUBMITTED ';cat "$evidence/os-build.id"
