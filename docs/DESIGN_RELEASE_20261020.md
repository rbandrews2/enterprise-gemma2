# Black glass design release

Authorized scope: publish the reviewed black-glass menu/cards, filled shared icons,
Enterprise badges/grouping, slightly wider first three mobile cards, universal
amber hover/focus glow and Enterprise-only moving edges. Messaging/Video meetings
retain their menu positions and receive Enterprise pills. Reduced motion supported.

Only five frontend assets are copied onto the current immutable live application
image: workspace-layout.css, mobile-home.js, organization-hub.js, field-voice.js,
ask-atlas.js. No Python, schema, database, model, weather, credential, IAM, billing
or resource configuration changes. Existing runtime spec is compared before/staged.

Focused validation: 16 Node checks pass across mobile Home, simulator viewport,
Ask Atlas navigation/cancellation and Voice receipt behavior. Updated fixtures
recognize the filled-mask label and MutationObserver. The added grouping assertion
checks stable ordering and lower Messaging/Video meetings positions. Browser preview
confirmed black cards, focus glow, Enterprise badges and Core-member boundaries.
No full PostgreSQL/provider suites: this release replaces static assets only.

Deployment: scripts/release_design_update.sh build/deploy. Minimal Cloud Build
context contains five assets, Dockerfile and build YAML only. Stage with no traffic;
verify unchanged runtime policy; cut over, verify asset hashes/public shell/version.
Rollback returns100% to the captured prior revision if public asset checks fail.
Final image/revision/version/evidence are recorded after actual deployment.

## Deployed and verified

- Candidate bc0f30aa440e69ca84fec056fcf3bfbe5e57f0de.
- Revision wzos-v2-accounts-ui-bc0f30a receives100% traffic.
- Image digest a730f7f0f7b3d6a6a43a88f07a915ad8c07856687e02f5e0619afab3b5d8b178.
- Cloud Build e35b254f-0cf0-400b-9cab-406e9454d92f succeeded.
- Public version f1def98aa29861b9697daeba.
- Preflight, build, drift, unchanged staged runtime, public5asset hashes, CSP,
  version and traffic PASS; deployment exit0. No rollback needed.
- Authenticated browser confirms black card gradients, icon masks, badges and menu
  order. Keyboard focus on Messaging activates atlas-orbit; Forms has no animation.
- Evidence /tmp/wzos-design-20261020.PGnPtVIs on Cloud Shell, referenced by
  $HOME/wzos-design-release-path.txt. No credentials or customer records in evidence.
- Prior revision wzos-v2-accounts-ui-3737af7 is retained for traffic rollback.

Focused16Node checks and release syntax checks passed; no full PostgreSQL/model/SMS
testing was repeated. The deployment replaced only5frontend assets and preserved
the serving backend, weather/model settings, runtime identity and secret bindings.
