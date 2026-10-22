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
