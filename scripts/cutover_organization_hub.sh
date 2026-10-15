#!/usr/bin/env bash
# Run only after inspecting the zero-traffic candidate and the approved gates.
set -euo pipefail
umask 077
evidence="$HOME/wzos-hub-rollout-20261014"
grep -Fxq HUB_CANDIDATE_READY_CONFIGURATION_PRESERVED_NO_TRAFFIC "$evidence/deploy.log"
rollback() {
  gcloud run services update-traffic wzos-v2-accounts --project enterprise-gemma2 --region us-central1 \
    --to-revisions=wzos-v2-accounts-daily-748f382=100 --quiet > "$evidence/rollback.log" 2>&1
  echo 'HUB_ROLLBACK_APPLIED: inspect rollback.log and verify public baseline'
}
trap 'rollback' ERR
gcloud run services update-traffic wzos-v2-accounts --project enterprise-gemma2 --region us-central1 \
  --to-revisions=wzos-v2-accounts-hub-5a3ac86=100 --quiet
accepted=0
for attempt in 1 2 3; do
  if python3 scripts/check_hub_public_release.py > "$evidence/public-check.log" 2>&1; then accepted=1; break; fi
  sleep 4
done
test "$accepted" = 1
python3 scripts/check_auth_origin.py --origin=https://app.workzoneos.org > "$evidence/auth-check.log" 2>&1
gcloud run services describe wzos-v2-accounts --project enterprise-gemma2 --region us-central1 --format=json > "$evidence/public-service.json"
python3 - "$evidence" <<'PY'
import json,sys
from pathlib import Path
s=json.loads((Path(sys.argv[1])/'public-service.json').read_text())
assert [(t.get('revisionName'),t.get('percent')) for t in s['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-hub-5a3ac86',100)]
print('HUB_PUBLIC_TRAFFIC_CONFIRMED_100_PERCENT')
PY
trap - ERR
cat "$evidence/public-check.log"
tail -n 1 "$evidence/auth-check.log"
echo HUB_PUBLIC_RELEASE_ACCEPTED
