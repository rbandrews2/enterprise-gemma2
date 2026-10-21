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

Current status: candidate bc0f30aa440e69ca84fec056fcf3bfbe5e57f0de pushed. Release
script Bash/Python syntax checks PASS. Cloud Shell needs restored CLI sign-in;
SDK tab opened for the user. No build/deployment launched; live unchanged.
