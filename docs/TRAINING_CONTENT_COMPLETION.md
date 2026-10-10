# Training: organization content, assignments, scored assessments and completions

October 9, 2026. Claude increment for review. Local synthetic preview only. No cloud
deployment, no shared-database migration and no third-party media.

- **Branch:** `claude/training`, cut from `enterprise-v2` at `2dc5935` (independent of
  the other Claude branches)
- **Commit:** the branch head
- **PR:** `claude/training` into `enterprise-v2` (link added when opened)

## Three records, kept separate

| Record | Source | Meaning |
|---|---|---|
| Self-reported study (`training_records`, existing) | Member statement, optional admin review | "I studied this." Not verified. |
| Assessment completion (`training_completions`, new) | WZOS scored a passing attempt on a published module version | "Passed this organization's assessment, version N, score X%." Not a certificate. |
| Verified qualification (`employee_qualifications`, Codex) | Admin review with issuer and evidence in Employees | The only record dispatch accepts as verified. |

Every training API response carries `certificate_issued: false` and
`qualification_issued: false`. The UI repeats the distinction at the top of the panel.

## What it does now

- **Authoring (admin, both editions).**
  - Organization modules have a stable identifier, title, summary, content sections,
    optional https media links, multiple-choice questions, a pass mark (50–100%) and
    attempts per version (1–10).
  - Every media link requires `rights_confirmed: true` and a rights note (source,
    license or owner). WZOS links out; it doesn't host or embed the media. The recovered
    V1 catalog stays `content_review_pending` and isn't playable.
  - Drafts are versioned with optimistic concurrency.
  - Publishing creates an **immutable version** and requires content and at least one
    question.
  - Retiring a module hides it and cancels open assignments.
- **Assignments (admin).** Assign the current published version to distinct active
  members, with an optional due date. Re-assigning is idempotent. Assignments can be
  cancelled; completed ones stay on record.
- **Assessments (member).**
  - Members see published content and questions. The server never sends the answers,
    and results don't reveal which answers were correct, so retakes stay meaningful.
  - Attempts are scored on the server against the exact published version. Each attempt
    is idempotent by `request_id`, and the attempt limit is enforced.
  - A version that changed after loading is refused (409).
  - A pass creates the completion and marks the matching assignment completed.
- **Path to a qualification (admin, account workspace only).** On a completion, "Add as
  unreviewed qualification" calls Codex's existing
  `PUT /api/account/employees/{user}/qualifications/training-<module>`. The record has:
  - `review_status: unreviewed`;
  - issuer `<organization> internal training`;
  - an evidence reference naming the completion ID, version and score.

  Verification remains a separate admin action in Employees, and dispatch keeps treating
  unreviewed qualifications as ineligible. The button appears only when the employee
  API responds; there are no server-side writes to Codex tables.
- **Visibility.** Members see their own assignments and completions; admins see the
  organization's. Everything is organization-scoped (cross-organization returns 404 or
  an empty list).

## API

`GET /api/training-modules` (admin: drafts and status; member: published learner views);
`PUT /api/training-modules/{id}`; `POST /api/training-modules/{id}/publish`;
`POST /api/training-modules/{id}/retire`; `GET /api/training-modules/{id}/versions/{n}`;
`POST /api/training-modules/{id}/attempts`; `POST /api/training-assignments`;
`POST /api/training-assignments/{id}/cancel`; `GET /api/training-assignments`;
`GET /api/training-completions`. The existing `/api/training` study planner and
`/api/training-records` are unchanged.

## Schema (startup DDL, needs review)

Five additive tables: `training_modules`, `training_module_versions`,
`training_assignments`, `training_attempts`, `training_completions`. The SQL is in
[migrations/20261009_training_content.sql](migrations/20261009_training_content.sql).
Rollback means deploying the previous code and keeping the tables as history.

## Changed files

- `services/workspace_preview/training_content.py` (new)
- `services/workspace_preview/static/training-content.js` (new; same panel pattern as
  `review-workflows.js`)
- `tests/test_training_content.py` (new)
- `docs/migrations/20261009_training_content.sql` (new), this document
- **Shared, narrow:**
  - `app.py`: a register call after `training_records`, plus a `/training-content.js`
    route;
  - `static/index.html`: one script tag.

## Validation (actual results)

- `tests.test_training_content`: **6 pass**, 6 PostgreSQL counterparts **skipped** (no
  test database). Coverage:
  - admin-only authoring;
  - media rights required, https only, distinct options, valid answer index;
  - publish requirements and immutable versions;
  - answers never sent; cross-organization isolation;
  - scoring, retry idempotency and conflicts, attempt limits, version-change refusal;
  - completion separate from self-reported records;
  - assignment scope, idempotency, cancellation and retirement.
- Full Python suite: **349 tests, 1 error, 73 skipped** (all PostgreSQL). The error was
  in Codex's Atlas test
  `test_vllm_socket_reliability.test_disconnect_closes_real_socket_and_next_request_recovers`,
  which this branch doesn't touch. It occurred while two full suites ran at once on
  this machine; rerun alone, that module passed 2/2. Codex should confirm on the
  integrated candidate.
- **Node: 21/21.** `node --check` passes on `training-content.js`.
- **Browser** (local synthetic preview, in-app browser):
  - The Enterprise admin created a module in the editor (two sections, a rights-attested
    link, two questions, 100% pass mark), saved, published and assigned it to the member
    with a due date. The status showed "assigned · due … · attempts 0".
  - At 375×812, the member saw the assignment, opened the content (rights note shown)
    and submitted answers.
  - A failed attempt was saved, and a passing attempt showed "Passed with 100%. This is
    an assessment completion record, not a certificate or verified qualification." The
    assignment changed to Completed.
  - **Defect found and fixed:** the result message was being cleared by the
    post-submit refresh; it is now set from the server response.
  - The in-app browser pane was hidden during the member half, so those steps used DOM
    clicks on the real controls and **no screenshots** were possible. The employee
    qualification button is unexercised in the browser (synthetic preview has no
    Employees API); its API contract is Codex's existing one.

## Remaining gaps

- Uploading or hosting training video and documents (needs Codex's private file storage
  and rights workflow).
- Question types other than single-answer multiple choice; question banks or
  randomization.
- Recertification intervals and expiry reminders, and messaging notifications for
  assignments (could use the Messaging outbox once merged).
- Bulk reporting and export of training status.
- Adding a recovered V1 course requires the organization to author it with confirmed
  rights.
- The Atlas training-help wording is unchanged and should mention assessment
  completions. Proposed text for Codex: "Admins can publish organization training with
  assessments. Passing records an assessment completion, not a certificate; only an
  admin-verified qualification counts for dispatch."

## Product questions for Ray (current behavior in brackets)

1. Who may author training: any organization admin? [Yes.]
2. Should results show which answers were wrong? [No; score only.]
3. Should passing automatically suggest a qualification? [No; the admin chooses "Add as
   unreviewed qualification" and verifies separately.]
4. Default pass mark and attempts? [80% and 3 per version; adjustable per module.]
5. Should Core organizations get training authoring? [Yes; both editions.]

## Integration and rollback

Merge after review. Codex then runs the PostgreSQL class with `WZOS_TEST_DATABASE_URL`,
plus browser acceptance with accounts, including the Employees qualification button.
Rollback means reverting the commit; the tables become inert.
