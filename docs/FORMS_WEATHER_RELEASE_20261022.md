# Forms, weather and voice review release

Authorized: deploy the previously local signature pad; compact the weather card
using the supplied crop; fix silent Smart Field Voice/form review actions; create
prelaunch checklist. See PRELAUNCH_REQUIREMENTS_20261022.md.

Changes: optional validated signatures in existing JSON submissions (no DDL);
six static assets for signing/office preview, compact weather and visible voice
review. Weather remains location-based and retains permission/watch configuration.
Blank extra metrics omitted; populated details/forecast collapse behind disclosure.
Severe alert headlines and stale/unavailable feedback stay visible.

Office Review received form now opens a labelled on-page modal, with separate print
and download actions; close/view/account transitions remove it. Mark reviewed and
request changes have success feedback. Reopened voice drafts scroll/focus the review
editor, explain what opened and retain office receipt protections.

Release overlays six reviewed static files and form_submissions.py onto the live
immutable image. No model, secret, IAM, service resource or weather monitor changes.
Stage without traffic, verify unchanged runtime policy, then cut over with automatic
rollback to captured prior revision if public asset checks fail. Schema unchanged;
backward-compatible JSON field documented in FORM_SIGNATURES_20261020.md.

Validation: focused Node checks, SQLite submission tests and disposable PostgreSQL
signature/submission class. Browser review/phone/PDF acceptance tracked separately;
never submit a customer's draft during acceptance. Actual results recorded below.
