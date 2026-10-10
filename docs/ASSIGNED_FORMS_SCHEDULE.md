# Assigned-job forms and schedule

Contract for the October10 internal assembly increment; no new DDL.

- A member may link a new **own** form draft to their active Enterprise dispatch
  assignment. This validates a job reference only, without granting read/edit
  access to the original work order or its private reports/files.
- A saved form freezes the referenced title/address in its own versioned JSON.
  An unchanged existing link remains editable after cancellation; changing or
  adding a link requires current authorization. Removing a link remains allowed.
  Existing own-form/admin-review and organization boundaries remain unchanged.
- `GET /api/modules/jobs` provides the bounded selectable reference list; it
  reuses the Time Clock reference policy. No public ingestion/provider calls.
- `GET /api/dispatch/schedule` is Enterprise-only, paginated25 at a time.
  Admins see assignments within their organization; members see only their own.
  An optional day is a UTC day and includes shifts overlapping its boundaries.
  Cancelled/replaced/declined assignments remain visible with their status.
- Schedule assignment cards are read-only projections, never editable schedule
  drafts. Receipt confirmation remains explicit in My jobs; viewing a schedule
  does not confirm an assignment. Core schedule/meetings remain available.

Exact-candidate PostgreSQL, full regression and real-device acceptance precede
shared staging deployment. Synthetic browser results do not establish live
provider delivery, field compliance or production readiness.

## Validation

- Focused Dispatch/Modules/Form-submission regression:59 tests in172.722s,
  34 passed,25 PostgreSQL skips,zero failures/errors. Initial schedule fixture
  incorrectly expected two assignments while one employee had unknown availability;
  corrected availability and reran the combined suite successfully.
- Atlas verified-guidance regression:5 passed in8.155s; guidance now distinguishes
  saved forms from unsaved printable worksheets and read-only dispatched schedules.
- Full Node suite:47 passed,zero failures/skips, including new read-only schedule,
  assigned form-picker and late-response/account-switch cases. Syntax/diff checks passed.
- Synthetic member browser: schedule showed own dispatched assignment and no
  New draft schedule action; saved an assigned-job incident, reloaded, reopened
  and verified persisted title/address reference. This is seeded local example
  data, not live inference or a real employee dispatch.
- Evidence: ignored .local-data/forms-schedule-final-python.log,
  forms-schedule-final-node.log, forms-schedule-atlas.log,
  assigned-form-preview.jpg and assigned-schedule-preview.jpg.

No migration, provider connection or deployment. Exact-candidate full Python,
PostgreSQL, broader admin/Core/real-device browser and private-storage cloud
acceptance remain open. Rollback is a revert of this focused candidate commit;
extra JSON reference fields in existing forms can remain as historical metadata.
