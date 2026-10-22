#!/usr/bin/env bash
# Numbered training links and global footer; preserve current runtime policy.
set -euo pipefail
umask 077
phase=${1:?build/deploy}; root=${2:?evidence directory}
cd "$root/source"
candidate=$(cat "$root/source-commit.txt")
test "$(git rev-parse HEAD)" = "$candidate"
project=enterprise-gemma2; service=wzos-v2-accounts; region=us-central1
tag="ui-${candidate:0:7}"; revision="$service-$tag"
test "$(gcloud config get-value project 2>/dev/null)" = "$project"
if [[ "$phase" == build ]]; then
 test "$(cat "$root/postgres.exit")" = 0
 test "$(cat "$root/node.exit")" = 0
 test "$(cat "$root/tested-source.txt")" = "$candidate"
 gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/before.json"
 python3 - "$root" <<'PY'
import json,sys,re
from pathlib import Path
p=Path(sys.argv[1]);s=json.loads((p/'before.json').read_text())
t=[t for t in s['status']['traffic'] if t.get('percent')]
assert len(t)==1 and t[0]['percent']==100
r=t[0]['revisionName'];assert re.fullmatch(r'wzos-v2-accounts-ui-[a-f0-9]{7}',r)
(p/'expected-prior.txt').write_text(r)
PY
 prior=$(cat "$root/expected-prior.txt")
 gcloud run revisions describe "$prior" --project="$project" --region="$region" --format=json > "$root/baseline-revision.json"
 python3 - "$root" <<'PY'
import json,sys,re
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads((p/'baseline-revision.json').read_text())
image=r['status']['imageDigest']
assert re.fullmatch(r'us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:[a-f0-9]{64}',image)
(p/'baseline-image.txt').write_text(image)
PY
 export WZOS_RELEASE_PRIOR="$prior" WZOS_RELEASE_BASE="$(cat "$root/baseline-image.txt")"
 python3 scripts/check_ui_release.py preflight "$root"
 # Overlay only reviewed training/footer files; no startup DDL or runtime changes.
 mkdir "$root/context"
 cp services/workspace_preview/static/{index.html,team-modules.js,training-content.js,workspace-layout.css,account.js,workspace.js,workspace.css} "$root/context/"
 cp services/workspace_preview/{training_content.py,training_catalog.json} "$root/context/"
 printf 'FROM %s\nUSER root\nCOPY *.js *.css *.html /app/services/workspace_preview/static/\nCOPY training_content.py training_catalog.json /app/services/workspace_preview/\nRUN python -m py_compile /app/services/workspace_preview/training_content.py && chmod a+r /app/services/workspace_preview/training_content.py /app/services/workspace_preview/training_catalog.json && chmod a+r /app/services/workspace_preview/static/*.js /app/services/workspace_preview/static/*.css /app/services/workspace_preview/static/*.html\nUSER wzos\n' "$WZOS_RELEASE_BASE" > "$root/context/Dockerfile"
 cat > "$root/context/cloudbuild.yaml" <<'YAML'
steps:
- name: gcr.io/cloud-builders/docker
  args: ['build', '--platform', 'linux/amd64', '-t', '${_IMAGE}', '.']
images: ['${_IMAGE}']
timeout: 600s
options:
  machineType: E2_MEDIUM
YAML
 image="us-central1-docker.pkg.dev/$project/$project/$service:$tag"
 gcloud builds submit "$root/context" --project="$project" --config="$root/context/cloudbuild.yaml" --substitutions="_IMAGE=$image" --async --format='value(id)' > "$root/build-id.txt" 2> "$root/build-submit.log"
 echo TRAINING_BUILD_SUBMITTED; cat "$root/build-id.txt"; exit 0
fi
test "$phase" = deploy
export WZOS_RELEASE_PRIOR="$(cat "$root/expected-prior.txt")" WZOS_RELEASE_BASE="$(cat "$root/baseline-image.txt")"
gcloud builds describe "$(cat "$root/build-id.txt")" --project="$project" --format=json > "$root/build.json"
python3 scripts/check_ui_release.py build "$root"
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/predeploy.json"
python3 scripts/check_ui_release.py drift "$root"
gcloud run deploy "$service" --project="$project" --region="$region" --image="$(cat "$root/immutable.txt")" --no-traffic --revision-suffix="$tag" --quiet > "$root/stage.log" 2>&1
gcloud run revisions describe "$revision" --project="$project" --region="$region" --format=json > "$root/revision.json"
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/staged.json"
python3 scripts/check_ui_release.py staged "$root"
gcloud run services update-traffic "$service" --project="$project" --region="$region" --to-revisions="$revision=100" --quiet > "$root/cutover.log" 2>&1
if ! python3 scripts/check_training_release.py "$root"; then
 gcloud run services update-traffic "$service" --project="$project" --region="$region" --to-revisions="$WZOS_RELEASE_PRIOR=100" --quiet > "$root/rollback.log" 2>&1
 echo TRAINING_RELEASE_ROLLED_BACK; exit 1
fi
gcloud run services describe "$service" --project="$project" --region="$region" --format=json > "$root/live.json"
python3 scripts/check_ui_release.py traffic "$root"
echo TRAINING_RELEASE_DEPLOYED
