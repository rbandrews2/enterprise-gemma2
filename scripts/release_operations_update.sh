#!/usr/bin/env bash
# Preserve current runtime policy. No IAM, new workloads or DOT activation.
set -euo pipefail
umask 077
phase=${1:?gate/build/deploy}; root=${2:?evidence directory}
cd "$root/source"
test "$(git rev-parse HEAD)" = "$(cat "$root/source-commit.txt")"
if [[ "$phase" == gate ]]; then
 exec bash scripts/release_ui_update.sh gate "$root"
fi
if [[ "$phase" == build ]]; then
 gcloud run revisions describe wzos-v2-accounts-ui-6047e5b --project=enterprise-gemma2 --region=us-central1 --format=json > "$root/baseline-revision.json"
 python3 - "$root" <<'PY'
import json,re,sys
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads((p/'baseline-revision.json').read_text())
assert r['metadata']['name']=='wzos-v2-accounts-ui-6047e5b'
image=r['status']['imageDigest']
assert re.fullmatch(r'us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:[a-f0-9]{64}',image)
(p/'baseline-image.txt').write_text(image)
PY
fi
export WZOS_RELEASE_PRIOR=wzos-v2-accounts-ui-6047e5b
export WZOS_RELEASE_BASE=$(cat "$root/baseline-image.txt")
exec bash scripts/release_ui_update.sh "$phase" "$root"
