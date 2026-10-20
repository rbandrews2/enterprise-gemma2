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

Status: source and release helper prepared. Gate, build and deployment pending.
