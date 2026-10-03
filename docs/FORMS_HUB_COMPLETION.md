# Forms Hub completion — Claude module handoff

The branch is `claude/forms-hub`. It was cut from `origin/enterprise-v2` at `3247a18`, which contains AGENTS.md and the revised collaboration contract. The work lives in a separate worktree. The Time Clock worktree and PR #1 are unchanged, and Codex's checkout is untouched.

## Plan (written before implementation)

### What exists today
- **Backend** (`services/workspace_preview/modules.py`): Forms and Schedule share one generic module. Forms are stored in `module_records` (`kind='forms'`), and full payload snapshots go to the append-only `module_revisions` table. The existing protections are reused unchanged:
  - Writes are version-checked with `expected_version`.
  - Retrying an identical save returns the stored record.
  - Members see and edit only their own forms; admins see and edit every form in their organization.
  - Work-order links are checked with `permitted_row`.
  - The template is fixed once a record is created.
  - There are three hard-coded templates: incident, DVIR and JSA.
- **UI** (`static/modules.js` and the `#modules-view` markup): one view serves both Forms and Schedule. It has no search, no explicit template revision, no review status and no missing-field display, and the only export is the Work Zone Report's live view.
- **Consumers that must keep working:**
  - The Work Zone Report reads `module_records`/`kind='forms'` filtered by `$.order_id` (`app.py`) and compares snapshots (`report_history.py`). Both are Codex-owned.
  - Attachments authorize `entity_kind='form'` against `module_records` (`files.py`).
  - Existing tests, the demo builder and the account-storage tests use `/api/modules/forms`.
- **Recovered V1 sources** (`.local-recovery/core-build-baseline/src/pages/forms/`):
  - Recoverable forms: C85, JSA, DVIR, incident, whistleblower, time-off and company PDFs.
  - The V1 JSA has extensive checklists covering job information, weather, roadway type, shoulder conditions, traffic, physical, health and environmental hazards, PPE, inspections, emergency and medical clinic, and typed acknowledgement.
  - The V1 C85 is a recreated grid layout of VDOT's "Pavement Marking – Contractor's Daily Log and Quality Control Report" that V1 called a "legal form". The only output was browser print or JSON.

### Key evidence for official forms
In the cataloged but **unreviewed** VDOT source `vdot-bk704-002020-00`, the specification describes Form C-85 as a contractor's daily log. It says that "the C-85 form shall not be modified; all log entries shall be made in ink", and that the signed log goes to the Engineer. `knowledge/SOURCE_REGISTER.md` says a label like "C85" does not identify the current official template.

**Therefore WZOS will not present a recreation as the official C-85.** It provides an internal *preparation worksheet* that references the official form, with source provenance and the review state `unreviewed`. The printout says to transfer the entries to the official form. No form is marked as legally required.

### Approach
1. **A separate module.** Forms Hub gets its own backend (`services/workspace_preview/forms_hub.py`, `/api/forms/...`), its own view (`#forms-view`) and its own script and styles (`static/forms-hub.js`, `forms-hub.css`). Schedule stays on `modules.py`/`modules.js`.
2. **Same storage, no new tables.** Records stay in `module_records`/`module_revisions` with `kind='forms'`, so the report, attachments and history keep working without changes. **There is no startup DDL.**
3. **A versioned template catalog** (`forms_catalog.json`, module data):
   - Each template has an `id`, an integer `revision`, a `category` (`internal_worksheet` or `official_form_reference`), field definitions (required flags, options, length limits, repeatable rows) and conditional rules.
   - Older revisions stay in the catalog.
   - A record pins `template_id`, `template_revision` and a SHA-256 `template_checksum` of the definition. New drafts use the latest revision, and a saved record always renders and validates against its pinned revision.
4. **Templates in this increment:**
   - JSA worksheet, expanded from the V1 option sets
   - Incident report
   - Vehicle inspection (DVIR), keeping the rule that a failed item requires a defect note
   - VDOT Form C-85 preparation worksheet (official form reference)
   - Existing legacy incident, DVIR and JSA records remain readable, shown as "legacy template", and the Work Zone Report keeps reading them.
5. **Server validation:**
   - Unknown fields are rejected.
   - Values must match their declared types, options and lengths.
   - Drafts may be incomplete. The server computes `missing_required`, including conditional rules, on every read and refuses to submit a form for review while anything is missing.
6. **Review status** using the existing admin and member roles; no new permission model:
   - `draft`: the owner, or an admin, edits.
   - `ready_for_review`: the owner submits; editing is locked.
   - `reviewed` (internal review only; not approval or certification) or `returned` with a note: an admin decides.
   - `cancelled`.
   - A returned form can be edited again. Each transition is a version-checked revision that records the actor, so the audit trail is the existing revision history.
7. **Browse and search:** search by title or template, filter by category, status and work order, and page through results. The template catalog is browsable before anything is created.
8. **Print and export:**
   - A print view styled for paper. Each printout is labelled with its category, template revision and status, plus a disclaimer.
   - JSON export (`GET /api/forms/{id}/export`) with template provenance, record version and revision history.
   - No PDF engine is added; PDF generation is Codex-owned.
9. **Compatibility:** the legacy `/api/modules/forms` writer will refuse to overwrite records created by Forms Hub, so their template fields can't be dropped.

### Shared-file changes (narrow, listed for review)
- `app.py`: one registration line for `forms_hub.register(...)`.
- `static/index.html`: a `#forms-view` section, one script tag and one stylesheet link.
- `static/workspace.js`: the view switch shows `#forms-view` for `forms` instead of `#modules-view`.
- `static/modules.js` (module-owned; shared with Schedule): stop handling the `forms` view.
- `modules.py`: a guard that refuses legacy writes to template records.
- `tests/atlas_navigation.test.cjs`: the expected element for `forms` becomes `#forms-view`.
- *Proposed* module-help text for Forms in `intelligence.py` and `assistant.js`, for Codex to review.

### Acceptance checks
- Browse and search templates and records, and see the category clearly on the list, the editor and the printout.
- Create, save, reopen and edit a form linked to a work order. Persistence must survive an application restart.
- Invalid input: unknown fields, wrong options, oversized values, a mismatched template revision or checksum, a template switch, and an inaccessible work order.
- Stale-version 409 responses and idempotent retries.
- Members are limited to their own forms. Admins see their organization only, and other organizations get 404. Only admins can review, and members can't transition other people's forms.
- Template traceability: a record created at revision 1 still loads and validates against revision 1 after revision 2 exists.
- Missing-required display, and submission blocked while anything is missing.
- The print view and JSON export.
- The Work Zone Report and attachment compatibility.
- Browser checks: the full flow, mobile width, keyboard operation and reduced motion.
- The full Python and Node suites.

### Provisional behavior and questions recorded up front
- Admins may review their own forms; this is allowed and recorded.
- Signatures are not captured. The JSA keeps a typed acknowledgement, labelled "not an electronic signature".
- Whistleblower, time-off and the company PDF library are out of scope. The whistleblower form needs a confidentiality design, and the PDF library needs an admin document-library decision.

## Results (October 3, 2026)

Commits, PR and the final file list are recorded in the PR description. This document is written before the commit.

### Implemented behavior
- **Browse and search.** Four templates are searchable on the client, with category badges on the card, the saved-form list, the editor and the printout. Saved forms can be searched by title (case-insensitive, with `%` and `_` treated literally) and filtered by status, type (internal, official reference or legacy) and work order. Results are paginated at 25 per page, with a 50-item limit on the API.
- **Templates:**
  - JSA worksheet: 5 sections and 26 fields from the V1 option sets. California-specific heat thresholds were removed.
  - Incident report.
  - Vehicle inspection (DVIR): a failed check requires a defect note, and "Not checked" blocks submission.
  - VDOT Form C-85 preparation worksheet, an `official_form_reference`:
    - It includes repeatable material, work and QC rows. It doesn't claim to store the official template (`official_template_stored: false`), and applicability is `not_determined`.
    - It cites source `vdot-bk704-002020-00` Paragraph 42 with its content hash and `unreviewed` status.
    - The catalog loader refuses any official reference that claims to store the official template.
- **Create, save, reopen and edit** with an optional link to a permitted work order. Each save is version-checked: a stale save gets a 409 and a "Refresh form" control that asks before discarding unsaved entries. An identical retry returns the stored revision. Saves persist across an application restart.
- **Template revision traceability.** Each record pins the template ID, revision and SHA-256 checksum. New forms must use the latest revision; existing forms keep, load and validate against their pinned revision even after a newer one is published. A changed checksum is refused with 409, and a record can't switch templates.
- **Validation** is driven by the template: unknown fields, wrong types, options outside the list, duplicate selections, oversized text, malformed dates and times, out-of-range numbers, excess or unknown row columns, and anything beyond the 64 KiB content limit are all rejected. Fully blank rows are dropped.
- **Missing required items** are computed on the server for every read, with labelled jump-to-field links in the editor. Submitting is disabled in the UI while items are missing and refused by the server with 422.
- **Review status:**
  - `draft` → `ready_for_review` (owner or admin)
  - `ready_for_review` → `returned` (admin, with a required note) or `reviewed` (admin; internal only, never "approved")
  - `reviewed` or `cancelled` → `draft` (admin reopen)
  - `cancelled` (owner or admin, from `draft` or `returned`)
  - Editing is locked during review and after a decision. Editing a returned form returns it to draft.
  - Each transition is a version-checked revision recording the actor and note.
- **Revision history** shows the author, status, review note, changed field keys, title changes and the template revision.
- **Print** uses a dedicated print-only view on white with the app chrome hidden. It shows the category, template revision and checksum, status, revision, owner, work order and any missing items, plus the official-reference notice. The C-85 printout is headed "PREPARATION WORKSHEET ONLY … do not submit this printout as the C-85."
- **JSON export** is labelled `official_submission: false` and includes template provenance and revision history.
- **Attachments** reuse the existing `files.js`/`files.py` support for form records. They appear only when file storage is enabled; local preview has none.
- **Work Zone Report compatibility.** New forms appear in the report's linked forms with their title, revision and status. `details` carries a template summary because the report displays that field.
- **Legacy records** created before Forms Hub templates still appear in the report and in Forms Hub, read-only and labelled "Legacy draft". The legacy `/api/modules/forms` writer now refuses to overwrite template-based records (409).
- **Permissions** are unchanged. Members see and edit only their own forms. Admins see and edit forms in their organization, and only admins return, review or reopen. Other organizations' records return 404. Records are keyed per organization, so the same ID used in another tenant is a separate record.

### Bugs found and fixed during browser verification
1. After a successful save or status change, the global saving flag never cleared, which silently blocked later saves and navigation.
2. Typing an admin review note marked the form as changed, which blocked Return and Mark reviewed with "Save your changes first."
3. "Refresh form" after a conflict discarded unsaved entries without asking; it now asks first.
4. The row grid used invalid CSS (`auto-fit` combined with an intrinsic track), so it collapsed to one column.
5. The print background kept dark page edges.

### Tests and actual results
- **Python, full suite:** 235 tests, 209 passed, 26 skipped. The skips are the 16 existing PostgreSQL cases plus the 10 new `PostgreSQLFormsHubTests`, all because `WZOS_TEST_DATABASE_URL` isn't set; Codex runs them in Cloud Shell. The baseline at `3247a18` was 215 tests, 199 passed and 16 skipped.
- **New `tests/test_forms_hub.py`:** 10 SQLite tests pass, and the same 10 run as a PostgreSQL subclass. They cover:
  - catalog categories, official-reference safety and checksums
  - create, save, reopen, edit, identical retry, stale 409, history and restart persistence
  - 16 invalid-input cases
  - the complete review workflow, locking and idempotent transitions
  - member, admin and cross-organization isolation
  - template revision traceability with an injected revision-2 catalog
  - DVIR conditional rules and blank-row handling
  - search, filters and pagination (including literal `%` and `_`)
  - export, Work Zone Report compatibility and the legacy guard
  - concurrent edits (exactly one 200 and one 409)
- **Node:** 12 of 12 passed, including the updated Atlas navigation test that expects `#forms-view`. `node --check` passes on all static JS.
- **PostgreSQL: NOT RUN.** There is no local PostgreSQL or Docker. Run `WZOS_TEST_DATABASE_URL=… python -m unittest tests.test_forms_hub -v` against a disposable schema. PostgreSQL-specific code paths: `lower(json_extract(...)) LIKE ? ESCAPE '\'`, `json_extract(...) IS NULL` for legacy filtering, and `BEGIN IMMEDIATE` mapped to the advisory lock.
- **Real browser:** Microsoft Edge (headless, via Playwright) on an isolated loopback preview with a fresh scratch SQLite database and synthetic identities. The final clean run passed:
  - The template list with category badges, and template search for "C-85".
  - **Keyboard:** Tab reaches "Start JSA", Enter opens the editor, and focus moves to the editor heading.
  - A partial save, the missing-items list, Submit disabled while items are missing, and a missing-item link focusing its field.
  - A complete save.
  - A stale save from a second tab gets 409 and "Refresh form". Dismissing the discard prompt keeps the entries; accepting loads revision 3.
  - Submitting locks the inputs.
  - The C-85 official reference box, repeatable rows, the print view (app hidden, white page) and JSON export with `official_submission: false`.
  - Saved-form search and the type filter.
  - Admin: the owner name in the list, Return without a note refused, then returned with a note. The member sees the note, edits, and the form goes back to draft. History lists the revisions.
  - Another organization's admin sees 0 forms.
  - At 390 px with reduced motion: no horizontal overflow.
  - Console: the existing favicon 404 plus the intentional 409 and 422 from the stale-save and missing-note checks.
- **Screenshots** (compressed WebP, synthetic data, `docs/screenshots/forms-hub/`): JSA editor, C-85 official reference, print view, admin returned review and mobile C-85. The full-resolution captures are kept outside Git in the session scratchpad.

## API and schema changes
- **Startup DDL: none.** Forms Hub reuses `module_records` and `module_revisions`, which `modules.register` already creates. Records are written with `kind='forms'`. The new payload keys `template_id`, `template_revision`, `template_checksum`, `template_category`, `fields`, `review` and the new status values are additive and stored in the existing JSON `payload` column. No migration SQL is needed. Older consumers ignore the keys, and the report shows title, revision, status and the `details` summary.
- **New authenticated endpoints:**
  - `GET /api/forms/templates`
  - `GET /api/forms/templates/{id}/{revision}`
  - `GET /api/forms`, with optional `q`, `status`, `category`, `order_id`, `offset` and `limit`
  - `GET` and `PUT /api/forms/{id}`
  - `POST /api/forms/{id}/status`
  - `GET /api/forms/{id}/history`
  - `GET /api/forms/{id}/export`
  - Static `/forms-hub.js` and `/forms-hub.css`
- **Changed behavior:** `PUT /api/modules/forms/{id}` returns 409 for template-based records. Legacy incident, DVIR and JSA saves through that endpoint are unchanged; the demo builder and existing tests still use it.

## Changed files
- New: `services/workspace_preview/forms_hub.py`, `forms_catalog.json`, `static/forms-hub.js`, `static/forms-hub.css`, `tests/test_forms_hub.py`, `docs/FORMS_HUB_COMPLETION.md`, `docs/screenshots/forms-hub/*.webp`
- **Shared (narrow):**
  - `app.py`: import and one registration line.
  - `static/index.html`: the `#forms-view` section, a body-level `#forms-print` container, one stylesheet link and one script tag.
  - `static/workspace.js`: the view switch, and the `wzosFormsCanLeave` guard in `showWzosView`.
  - `static/modules.js`: now serves Schedule only.
  - `modules.py`: the legacy-overwrite guard.
  - `tests/atlas_navigation.test.cjs`: expects `#forms-view`.
- **Proposed module-help text (for Codex review):** the `forms` entry in `intelligence.py` (module help) and the `forms` quick-guide text in `static/assistant.js`. These are text-only. They describe template categories, missing-item checks, internal review, print/export and the vehicle "never clears" limit, and claim no applicability determination.

## Remaining gaps (not done in this increment)
- PostgreSQL execution of the new tests (Codex gate).
- **Not built:** signatures and certification, any agency submission, PDF generation (Codex-owned, through the report and PDF tooling), email delivery, required or recommended form selection (Atlas-owned), duplicate-evidence suppression, vehicle-defect follow-up workflow (repair or clearance tracking), and migrating legacy drafts to templates.
- **Templates not ported:** whistleblower (needs confidentiality and access design), time-off request (overlaps scheduling and HR), and the company PDF library (needs an admin document-library decision; V1 used public Supabase URLs, which must not be reused).
- **Template governance:** templates are edited in a code-reviewed JSON file. There is no admin template editor or per-organization custom forms.
- **Demo data:** `scripts/build_unified_demo.py` still creates legacy drafts. They appear in Forms Hub as read-only "Legacy draft" records.
- **Template maintenance:** the dead Forms-specific markup and code paths in `modules.js` and `#modules-view` (the DVIR and JSA fieldsets) are hidden but not yet removed. That cleanup belongs with the Schedule increment.
- The JSA option lists are carried over from V1 and haven't been reviewed by a safety professional.

## Open product decisions (provisional behavior in effect)
1. **Self-review:** admins can mark their own forms reviewed; this is recorded but not prevented. Should a second person be required?
2. **Admin edits:** admins can edit members' forms while they're in draft or returned (existing Forms permission); the owner is kept and the editor is recorded. Keep this?
3. **Review vocabulary:** "Reviewed (internal)" is deliberately not "Approved". Does Ray want an approval step, and who may approve?
4. **Signatures:** none are captured. The JSA keeps typed crew acknowledgement only. Which forms need signatures, and what kind (typed, drawn, identity-verified)?
5. **C-85:** WZOS provides a preparation worksheet only. If Ray wants WZOS to keep an electronic C-85, someone needs to confirm the current official template and the contract-specific rules first. The source text mentions an electronic format, but the source is unreviewed.
6. **Legacy drafts:** they're read-only in Forms Hub. Should they be migrated to templates or archived?
7. **Template updates:** existing forms stay on their pinned revision, and there is no "upgrade to latest template" action. Should one be added?
8. **Retention and deletion:** there is no delete, only cancel. Retention policy for forms, revisions and attachments is undefined.

## Integration instructions (for Codex)
1. Review the PR into `enterprise-v2`. Shared-file edits are listed above. The Atlas help text is proposed for your review of placement and accuracy.
2. Run the full Python and Node suites on the integrated candidate, then run `tests/test_forms_hub.py` (including `PostgreSQLFormsHubTests`) against a disposable Cloud Shell PostgreSQL schema.
3. No startup DDL or migration is involved. Records reuse `module_records` and `module_revisions`.
4. On staging with synthetic accounts, verify:
   - the `/api/forms` routes with admin and member accounts across two organizations
   - the Work Zone Report linked-forms view showing a Forms Hub record
   - an attachment upload on a saved form (requires private file storage)
5. `SESSION_HANDOFF.md` and `REMAINING_TASKS.md` are untouched. The product decisions above are for the "Additions to review" queue.

## Rollback
- **Code:** revert the merge. The old `modules.js` view handles Forms again, and the old `/api/modules/forms` writer returns. Records created by Forms Hub stay in `module_records`. The legacy UI would show them with partial fields (title, status, details), and the restored legacy writer could then overwrite their template data. If rolling back after real use, export or freeze those records first.
- **Data:** nothing to drop, because no tables were added.
