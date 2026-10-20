# Smart Field Voice office receipt repair

## User acceptance and reported problem

The user reports a real recording produced correct objects and counts. They pressed
Send to office but saw no receipt and no administrator notification. This confirms
generation quality for that recording, not successful persistence or delivery.

## Current delivery contract

Reviewed reports are stored atomically in organization-scoped form_submissions.
Admins read them in Forms hub > Office received forms. A deterministic in-app
message and receipt are inserted for each organization admin, including the sender
when the sender is an admin. This path deliberately never queues SMS or email.
Do not claim the user's individual submission was received until its saved state
has been verified. The browser organization chooser remained busy during the
read-only inspection; no real report contents or submission state were obtained.

## Local repair

- Show progress, validation errors and acknowledgement beside submission controls.
- Restore dated receipt and bundle identifier when reopening a sent report.
- Disable submitted report editing/resending on reopen.
- Preserve confirmed receipt if refreshing the saved-report list fails.
- Add an admin-only count of received forms awaiting review, linked to Forms hub.
  The alert refreshes on session, submission, review, foreground and each minute.
  Responses from a previous account cannot appear after an account switch.
- GET /api/form-submissions/summary returns only the signed-in admin's tenant count.

No new DDL, permissions, providers, secret bindings, weather settings or paid model
requests. Rollback is the prior application image; existing submissions and messages
remain compatible. Source/manual refinements are separate uncommitted work.

## Validation

Four focused Node checks passed: visible receipt despite list failure, persistent
reopened receipt/read-only controls, visible failure without false success, and
admin alert refresh/account-switch isolation. Two focused Python workflow checks
passed: atomic/idempotent submission with zero SMS and admin self-notification,
tenant/member summary isolation, review-count update and persisted submission IDs.
Eleven DOT reasoning regressions also passed in the same 13-test Python run.

These changes are local, not yet deployed. Previous full cloud gates at bc7394d
do not validate this subsequent repair. Final PostgreSQL/Node release gates,
browser acceptance and exact image deployment remain required.
