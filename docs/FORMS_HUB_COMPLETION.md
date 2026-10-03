# Forms Hub completion — Claude module handoff

Branch `claude/forms-hub` was cut from `origin/enterprise-v2` at `3247a18`; the PR is #2. It lives in a separate worktree. The Time Clock worktree and PR #1 are unchanged, and Codex's checkout is untouched.

## Product direction (Ray, October 3, 2026)

The first commit on this branch (`a45cdab`) built saved form records with an internal review workflow. Ray then clarified the product, and this revision replaces that design:

- Forms are for the customer's use. Customers and their employees **download or print** the forms they need and do whatever they want with them.
- **No review is required, and no forms currently need signatures.**
- Forms are downloaded, not uploaded. The one exception is that **an organization admin uploads specific forms for their team** to access.
- The **C-85 is just another form** a customer can access. Following Ray's answers, it is not bundled: an admin uploads the official copy.
- Built-in WZOS forms can optionally be **filled in on screen before printing or downloading. Nothing is saved.**
- Admin uploads are visible to **everyone in that organization**.

## Reusable components found
- The existing private file store (`files.py`): `LocalFiles` for local use and `GoogleFiles` for private GCS with uniform access and public-access prevention. It provides PDF/PNG/JPEG type and signature checks, a 10 MiB limit, SHA-256 integrity checks on download, idempotent file IDs and attachment-only downloads.
- `module_records`/`module_revisions` provide version-checked metadata with revision history.
- The existing admin and member roles and the organization-scoped actor.
- Recovered V1 forms (`.local-recovery/core-build-baseline/src/pages/forms/`): the JSA option sets, the incident fields, and the DVIR fields already adapted in V2. V1's "Company Forms" page was an upload-and-download library on public Supabase URLs. The concept is reused here; the public-URL storage is not.

## Implemented behavior
- **A separate Forms Hub module:** `#forms-view`, `forms-hub.js`, `forms-hub.css` and `forms_hub.py`. Schedule management keeps `modules.js`/`#modules-view`.
- **Team forms** (admin uploads):
  - An admin adds a form with a name, a type (*Official agency form* or *Company form*), an optional description and a PDF/PNG/JPEG file. The admin can also edit details, replace the file, or remove the form.
  - Everyone in the organization sees forms that have a file and can download them. An entry without a file yet is visible only to admins.
  - WZOS states that it does not edit or verify uploaded forms or decide whether they apply (`verified_by_wzos: false`).
  - Removing a form hides it and blocks downloads of its files. The stored objects are kept, because no delete API exists yet.
- **WZOS printable forms:** JSA worksheet, Incident report and Vehicle inspection.
  - **Print blank:** a clean paper layout with empty lines, boxes, ☐ choices and blank table rows.
  - **Download blank:** a self-contained HTML file that opens in any browser to print or save as a PDF.
  - **Fill in:** type on screen, then *Print or save as PDF* or *Download filled form*.
  - Entries never leave the browser, and leaving with unsaved entries asks for confirmation.
  - Printouts are built only from text nodes, so typed markup is escaped; this was verified in the browser.
- **One search** filters both lists by name, description, type and filename.
- **Permissions and isolation:**
  - Members cannot create, edit, upload, replace or remove team forms (403).
  - Other organizations cannot list, download, upload to or remove them (404).
  - Records are keyed per organization, so the same ID in another tenant is a separate entry that cannot attach this organization's file.
- **Concurrency:** metadata changes are version-checked (409 when stale), identical retries return the stored result, and the add flow reuses its IDs when retried, so a retry creates no duplicates.
- **Design:** gloss-black panels with amber and gold badges, visible keyboard focus, and labelled buttons ("Download VDOT Form C-85", "Fill in Incident report"). The editor heading takes focus when opened, and focus returns to the opener when closed. The layout is one column on phones, and reduced motion disables transitions.
- The C-85 preparation worksheet, saved form records, review statuses, history, the JSON export and the missing-required logic from `a45cdab` were **removed**.

## Tests and actual results
- **Python, full suite:** 231 tests, 207 passed, 24 skipped. The skips are the 16 existing PostgreSQL cases plus 8 new `PostgreSQLFormsHubTests`, all because `WZOS_TEST_DATABASE_URL` isn't set. The base `3247a18` had 215 tests, 199 passed and 16 skipped.
- **New `tests/test_forms_hub.py`** (8 SQLite tests, also run as the PostgreSQL subclass) covers:
  - the printable catalog, with nothing stored and no write endpoint
  - an admin publishing a form and a member downloading it byte-for-byte, surviving a restart
  - member write attempts refused (403), and file-less entries hidden from members
  - cross-organization isolation for listing, download, file listing, upload, removal and file attachment
  - validation, stale versions, identical retries, attaching another entry's file refused, file type and signature checks, path-like filenames, and idempotent uploads
  - replace, rename and remove: removal hides the form and blocks downloads, and retrying a removal is idempotent
  - behavior when file storage isn't configured
  - concurrent edits (exactly one 200 and one 409)
- **Node:** 12 of 12 passed (including `atlas_navigation.test.cjs`, which expects `#forms-view`). `node --check` passes on all static JS.
- **PostgreSQL: NOT RUN.** There is no local PostgreSQL or Docker. Codex should run `python -m unittest tests.test_forms_hub -v` with `WZOS_TEST_DATABASE_URL` against a disposable schema.
- **Real browser:** Microsoft Edge (headless, via Playwright) on an isolated loopback preview with a fresh database, `LocalFiles` storage, synthetic identities and a synthetic placeholder PDF (not a VDOT file). Results:
  - An admin adds "VDOT Form C-85 (synthetic test copy)" as an official agency form and sees the card and badge. The admin renames it and replaces the file.
  - The member sees Download only, with no add panel. The download matches the replacement bytes exactly.
  - Searching "vehicle" and "c-85" filters both lists.
  - JSA print blank: the app is hidden, ☐ choices appear, and print is invoked. DVIR download blank produces a standalone HTML file.
  - **Keyboard:** Enter on "Fill in Incident report" opens the editor and focuses its heading.
  - A filled Incident form, including a work order and a selected option (☑), downloads and prints with the entries. `<script>` text is escaped. Nothing was sent to the server while the form was filled, printed or downloaded; the one write the listener logged was the later admin removal.
  - The leave guard keeps the editor when dismissed and closes it when accepted. Focus returns to the "Fill in" button.
  - Another organization's admin sees no team forms.
  - After the admin removes the form, the member sees none.
  - At 390 px with reduced motion: no horizontal overflow.
  - Console: only the existing favicon 404.
- **Screenshots** (compressed WebP, synthetic data, `docs/screenshots/forms-hub/`, about 280 KB in total): admin team forms, member view, blank JSA print, Incident fill-in and mobile admin. The full-resolution captures stay outside Git in the session scratchpad.

## API and schema changes
- **Startup DDL: none.** Team-form metadata uses the existing `module_records`/`module_revisions` with `kind='form_library'`. Files use the existing `workspace_files` table and object store with `entity_kind='form_library'`. No migration SQL is needed.
- **New authenticated endpoints:**
  - `GET /api/forms/templates` and `GET /api/forms/templates/{id}/{revision}`
  - `GET /api/forms/library`
  - `PUT /api/forms/library/{id}` (admin)
  - `POST /api/forms/library/{id}/remove` (admin)
  - Static `/forms-hub.js` and `/forms-hub.css`
- **Shared file contract (`files.py`, narrow):** `entity_kind` adds `form_library`. `parent()` gains a `write` flag that only the upload path sets. For `form_library`, read access is any member of the organization while the entry isn't removed, and writes are admin-only. Behavior for `order` and `form` is unchanged; the flag is ignored for them.

## Changed files (relative to `3247a18`)
- New: `services/workspace_preview/forms_hub.py`, `forms_catalog.json`, `static/forms-hub.js`, `static/forms-hub.css`, `tests/test_forms_hub.py`, `docs/FORMS_HUB_COMPLETION.md`, `docs/screenshots/forms-hub/*.webp`
- **Shared (narrow):**
  - `app.py`: import and one registration line.
  - `files.py`: the `form_library` kind, the write flag and the `json` import.
  - `static/index.html`: the `#forms-view` section, the body-level `#forms-print` container, one stylesheet link and one script tag.
  - `static/workspace.js`: the view switch, and the `wzosFormsCanLeave` guard in `showWzosView`.
  - `static/modules.js`: Schedule only.
  - `tests/atlas_navigation.test.cjs`: expects `#forms-view`.
  - `modules.py` is unchanged from the base.
- **Proposed module-help text (for Codex review, text only):** the `forms` entry in `intelligence.py` and the `forms` quick guide in `static/assistant.js`. These describe the download/print library, admin team forms, on-screen fill-in without saving, and the vehicle "never clears" limit.

## Remaining gaps
- PostgreSQL execution of the new tests (Codex gate).
- **No object deletion:** removing a team form hides it, but the stored file is retained. A file-store delete or retention policy is shared storage work.
- **No malware scanning** of uploads; this is an existing launch gate for all files.
- **Legacy form drafts:** drafts made by the old Forms UI (`/api/modules/forms`, used by the demo builder and existing tests) still exist and still appear in the Work Zone Report's "Linked form drafts", but Forms Hub no longer shows them. The report's linked-forms section is Codex-owned and may need rethinking now that forms aren't saved.
- Hidden Forms markup and code in `#modules-view`/`modules.js` (the DVIR and JSA fieldsets) is unreachable but not yet removed. That cleanup belongs with the Schedule increment.
- Downloaded blanks are HTML (printable or savable as PDF from any browser), not PDF files. Server-side PDF generation is Codex-owned.
- The JSA option lists come from V1 and haven't been reviewed by a safety professional.
- Not ported: whistleblower reporting (needs a confidentiality design) and time-off requests (an HR and scheduling workflow, not a download).

## Open product decisions (provisional behavior in effect)
1. **Should the built-in WZOS printables stay?** They are shown by default. Ray may prefer team forms only, or a per-organization option to hide them.
2. **Team form types:** "Official agency form" and "Company form". Are more categories needed, such as Safety or Vehicle?
3. **Admin-only entries without a file** (for example after an interrupted upload) are visible only to admins, who can upload a file or remove the entry. Is that acceptable?
4. **Removal is a soft hide.** Should admins be able to delete files permanently, and should older versions of replaced files be kept?
5. **Upload types:** PDF, PNG and JPEG up to 10 MB, from the shared file policy. Are other formats needed, such as Word or Excel?

## Integration instructions (for Codex)
1. Review PR #2. `files.py` is the only shared backend contract touched, and the change is narrow and listed above. The Atlas help text is proposed for your review.
2. `enterprise-v2` has moved past `3247a18` (`85cf1ca` through `85edf21`). A merge check reported no conflicts; rerun the full Python and Node suites on the integrated candidate.
3. Run `tests/test_forms_hub.py`, including `PostgreSQLFormsHubTests`, against a disposable Cloud Shell PostgreSQL schema.
4. On staging with synthetic accounts and private GCS:
   - an admin uploads a synthetic PDF and a member downloads it
   - another organization is refused
   - removing the form blocks the download
5. No startup DDL or migration is involved. I haven't touched `SESSION_HANDOFF.md` or `REMAINING_TASKS.md`; the open decisions above are for the "Additions to review" queue.

## Rollback
- **Code:** revert the merge. Forms then returns to the old `modules.js` draft UI. Team-form metadata (`module_records` rows with `kind='form_library'`) and the `workspace_files` rows and objects remain but are no longer reachable. With `form_library` gone from the `files.py` kinds, those files can't be downloaded through the API.
- **Data:** nothing to drop; no tables were added. If rolling back after real uploads, decide whether to keep or purge the stored objects.
