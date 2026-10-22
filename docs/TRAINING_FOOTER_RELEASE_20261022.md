# Training and global footer release

Authorized by Ray: update the live app with the completed numbered course link and
global footer changes. Candidate includes training save feedback, ten matching
admin fields/cards, removal of the unrelated office alert/disclaimer on Training,
tighter spacing and the shared black ownership/contact footer.

Overlay exactly seven static files plus training_content.py/training_catalog.json
on the currently serving immutable image. No new DDL, column, identity, secret,
service resources, weather configuration, model call or customer message. Existing
training tables store reserved catalog-video rows; rollback compatibility is
documented in TRAINING_COURSE_LINKS_20261022.md. Source/live evidence stays separate.

Run focused training-link/media Node checks and training-content/records PostgreSQL
checks in a disposable private socket database. Reuse already passing SQLite/browser
evidence rather than repeating unrelated suites. Build only after both gates pass.
Capture the live revision and compare runtime policy before staging without traffic.
Cut over after readiness/drift checks; public asset/footer/version/auth-denial checks
trigger automatic rollback to the captured previous revision on failure.

Run scripts/release_training_update.sh build/deploy with a private evidence directory.
Public acceptance never changes a real course, study record, report or subscription.
Actual gate/build/revision/version results will be recorded after deployment.

## Deployed results

- Source: 16d09056ccf31ee8f144b70353b0b657a527dd63.
- Revision: wzos-v2-accounts-ui-16d0905, 100% traffic; deploy.exit 0.
- Cloud Build: 083d777a-73cc-4f6e-9f39-cc7a803b27ed, SUCCESS.
- Image digest: 80c3819aa9e8d3ce38ccf47e87bd4015b40875768a54604e994da9674cb3c054.
- Public version: 5821810b858f1f58b45af012.
- 16 focused PostgreSQL tests PASS in 11.192 seconds; 10 Node tests PASS;
  zero failures/skips. Private test cluster cleanup is enforced by the test runner.
- Preflight/build/drift/staged-runtime/public-assets/footer/version/auth-denial/
  final-traffic checks PASS. Independent public footer/version readback PASS.
- Prior revision retained: wzos-v2-accounts-ui-358cf45. No rollback required.
- Cloud evidence: /tmp/wzos-training-footer-20261022.y7ej7c0f;
  pointer: $HOME/wzos-training-footer-release-path.txt.
- No customer course, study record, form, subscription or message was changed by
  release checks. Real video-provider playback remains a human acceptance item.
