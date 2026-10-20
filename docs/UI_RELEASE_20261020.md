# October 20 UI release

Ray authorized updating the live app. Candidate contains the reviewed layout,
mobile Home weather placement/darker glass, top account strip, Clock In copy,
Smart Field Voice instructions and public launch shell/shortcut refresh.
Weather permission/tracking configuration remains unchanged under Ray's hold.

Smart Voice and My jobs synthetic fixtures exist only in the loopback simulator
script. Deployment copies services only; no simulator fixtures, microphone bypass,
fake assignments or cloud processing activation is deployed.

Run scripts/release_ui_update.sh gate/build/deploy with a private evidence root
containing source/ and source-commit.txt. Existing verified image238ef05b is the
base. Live baseline must be voice-live-1d2da6b100%; active Voice flags must remain1.
Snapshot and compare full runtime spec/secret bindings/identity/resources/ingress;
no new workload identity, permission, provider, dependency or schema changes.
Backup/schema check is read-only; required full Node/PostgreSQL gate precedes build.
Stage existing service with no traffic; verify Ready/config; cut over and verify
exact public assets/auth boundaries. Automatic traffic rollback on public-check
failure. No model inference, SMS or customer recordings in release validation.

Public-only shell cache excludes API/private files/media. Existing update guards
remain. Explicit install-update/reload and actual Android splash/icon acceptance
remain device checks. If retiring the worker, serve a cleanup worker at its route;
never clear private browser storage. Standard image/traffic rollback is prepared.

Startup review: public navigation prefers current network HTML for update/rollback;
falls back to generic cached shell after1.5seconds or an offline error. Focused
startup/cache/update12checks PASS. No private/API cache expansion.

## Deployed and verified

- Frozen source: `6047e5ba5a70e366088c88b280e23bf6f631e1dc`.
- Full cloud Node gate:155 passed,0 failures/skips. Full disposable PostgreSQL
  gate:849 passed in367.673seconds,0 failures/errors/skips. No provider retests.
- Recent successful SQL backup/schema compatibility checks passed; no migration.
- Cloud Build `edfe4b79-a6cd-4d47-a291-e775761e3933`:SUCCESS.
- Image: `us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:2b1943521f78f9421d67003847b2723aaa24f84d69fab6a778f30761c1518561`.
- Revision `wzos-v2-accounts-ui-6047e5b` ready and100% traffic; public version
  `270e2a2ea96f733144a59d9b`. Staged runtime comparison, public asset hashes,
  anonymous API401 boundaries, exact Daily policy and final traffic checks PASS.
- Runtime identity/resources/secrets/Cloud SQL/ingress and active Voice flags
  preserved. Weather configuration hold remains in force. No new IAM or sends.
- Browser selected existing organization and opened dashboard/Smart Field Voice;
  updated instructions/controls observed. No microphone/location grant or recording.
  Private screenshots ignored under `.local-data/ui-sweep-20261020/live-*.png`.
- Rollback:100% traffic to `wzos-v2-accounts-voice-live-1d2da6b` preserves active
  Voice/base runtime. Public-shell navigation prefers current network HTML;
  explicit reload/update remains available. Device splash/icon acceptance open.

## Approved disk cleanup after deployment

Ray requested about2GB cleanup after completion. Removed only twelve explicitly
reviewed `.venv-accounts-test` dependency environments from old home release folders.
Validated canonical paths/ownership/venv structure and absence of active processes
using those release folders; compared exact plan again immediately before removal.
Deployment completion was a mandatory cleanup guard. Source, logs, credentials,
release records and scanner database retained. No laptop disk changes.

Actual reclaimed:2,128,019,456bytes (2.13GB /1.98GiB). Free home space increased
from228,122,624 to2,356,142,080bytes; `df` now52% used,2.2GiB available (was96%).
Private cleanup plan/result and release logs are in Cloud Shell evidence archive
`$HOME/wzos-ui-6047e5b-evidence.tgz` (40KB), SHA256
`07a3299a7869e72aff177ccf57097fdb8d491b2175056edb3103317da71ba960`.
Working evidence root `/tmp/wzos-ui-20261020.XC9Of8g4`, pointer
`$HOME/wzos-ui-release-path.txt`. Archive excludes source/venv/temp/package cache;
private permissions retained. Deleted dependency environments can be rebuilt from
each source checkout's requirements; their historical evidence remains available.
