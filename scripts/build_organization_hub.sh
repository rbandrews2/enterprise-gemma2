#!/usr/bin/env bash
# Build only: patch actual packages, preserve frozen sources, audit before publication.
set -euo pipefail
umask 077
evidence="$HOME/wzos-hub-build-20261014"
gate="$HOME/wzos-hub-20261014"
mkdir -p "$evidence"
repo=$(git rev-parse --show-toplevel)
revision=5a3ac868085685a5e71169ceac21fa618cc405e9
base=us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:648516f7dd97505a1c7f5d2feb40bc013b2aea572ca84fd589dd8c51914cd2fb
image=us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts:5a3ac86-hub
test "$(gcloud config get-value project 2>/dev/null)" = enterprise-gemma2
test "$(tr -d '\r\n' < "$gate/final-gate-source.txt")" = "$revision"
grep -Fxq 'PostgreSQL gate: PASS; run=596, failures=0, errors=0, skipped=0' "$gate/final-gate.log"
git diff --quiet 650aa5a "$revision" -- requirements-v2.txt requirements-accounts.txt
grep -Fxq 'HUB_REAL_HTTP_PASS checks=7; synthetic loopback only; no provider calls' "$gate/http-check.log"
python3 - "$gate/patched-dependency-audit.json" <<'PY'
import json,sys
a=json.load(open(sys.argv[1]));assert a['dependencies']
assert not any(d.get('vulns') or d.get('skip_reason') for d in a['dependencies'])
PY
if pgrep -f '[r]un_postgres_gate.py|[p]ostgres.*wzos-pg-gate' >/dev/null; then
  echo 'Build paused: inspect database test cleanup';exit 1
fi
gcloud run services describe wzos-v2-accounts --project enterprise-gemma2 --region us-central1 --format=json > "$evidence/before-service.json"
python3 - "$evidence/before-service.json" "$base" <<'PY'
import json,sys
s=json.load(open(sys.argv[1]));traffic=s['status'].get('traffic',[])
assert [(r['revisionName'],r['percent']) for r in traffic if r.get('percent',0)]==[('wzos-v2-accounts-daily-748f382',100)],'Live traffic changed: inspect before building'
assert s['spec']['template']['spec']['serviceAccountName']=='wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com'
assert s['spec']['template']['spec']['containers'][0]['image']==sys.argv[2],'Live base image changed'
print('HUB_BUILD_BASE_AND_RUNTIME_CONFIRMED')
PY
context=$(mktemp -d "$evidence/context.XXXXXXXX")
git archive "$revision" services shared knowledge requirements-v2.txt requirements-accounts.txt scripts/package_source_library.py | tar -x -C "$context"
cp "$repo/scripts/check_hub_image.py" "$context/scripts/check_hub_image.py"
cat > "$context/Dockerfile" <<DOCKER
FROM $base
USER root
COPY requirements-v2.txt requirements-accounts.txt /app/
RUN python -m pip install --no-cache-dir --upgrade pip==26.2.1 \\
    && python -m pip install --no-cache-dir -r /app/requirements-accounts.txt \\
    && python -m pip check
COPY --chown=root:root services /app/services
COPY --chown=root:root shared /app/shared
COPY --chown=root:root knowledge /app/knowledge
COPY --chown=root:root scripts/package_source_library.py scripts/check_hub_image.py /app/scripts/
RUN chown -R root:root /app/services /app/shared /app/knowledge \\
    && chmod -R u=rwX,go=rX /app/services /app/shared /app/knowledge \\
    && chown root:root /app/scripts && chmod 755 /app/scripts \\
    && chmod 644 /app/scripts/package_source_library.py /app/scripts/check_hub_image.py
LABEL org.opencontainers.image.revision="$revision"
USER wzos
RUN python /app/scripts/package_source_library.py --verify /app/.local-data/knowledge
DOCKER
python3 - "$context/cloudbuild.json" "$image" <<'PY'
import json,sys
path,image=sys.argv[1:]
audit='''set -eu
site_dir=$(python -c 'import sysconfig; print(sysconfig.get_path("purelib"))')
python -m venv /tmp/audit-tool
/tmp/audit-tool/bin/python -m pip -q install --upgrade pip==26.2.1
/tmp/audit-tool/bin/pip -q install pip-audit
/tmp/audit-tool/bin/pip-audit --path "$site_dir" --format json --output /evidence/image-audit.json
python -c 'import json; a=json.load(open("/evidence/image-audit.json")); assert a["dependencies"]; assert not any(d.get("vulns") or d.get("skip_reason") for d in a["dependencies"]); print("IMAGE_AUDITED_PACKAGES",len(a["dependencies"]))'
'''
audit = audit.replace('$', '$$')  # Cloud Build must pass shell dollars literally.
steps=[
 {'name':'gcr.io/cloud-builders/docker','args':['build','--tag',image,'.']},
 {'name':'gcr.io/cloud-builders/docker','args':['run','--rm','--entrypoint','python',image,'/app/scripts/check_hub_image.py']},
 {'name':'gcr.io/cloud-builders/docker','entrypoint':'bash','args':['-c','docker run --rm --entrypoint python '+image+' -m pip freeze --all > /workspace/runtime-inventory.txt']},
 {'name':'gcr.io/cloud-builders/docker','args':['run','--rm','--user','0','--volume','/workspace:/evidence','--entrypoint','sh',image,'-c',audit]},
 {'name':'gcr.io/cloud-builders/docker','entrypoint':'bash','args':['-c','cat /workspace/image-audit.json; echo HUB_IMAGE_AUDIT_PASS; cat /workspace/runtime-inventory.txt']},
]
json.dump({'steps':steps,'images':[image],'timeout':'1200s'},open(path,'w'),indent=2)
PY
printf '%s\n' "$revision" > "$evidence/source.txt"
printf '%s\n' "$image" > "$evidence/image-tag.txt"
gcloud builds submit "$context" --project enterprise-gemma2 --config "$context/cloudbuild.json" --async --quiet --format='value(id)' > "$evidence/build.id"
printf 'HUB_BUILD_SUBMITTED ';cat "$evidence/build.id"
