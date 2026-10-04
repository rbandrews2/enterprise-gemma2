# Forms Hub completion — Claude module handoff

Branch `claude/forms-hub` was cut from `origin/enterprise-v2` at `3247a18`; the PR is #2. It lives in a separate worktree. The Time Clock worktree and PR #1 are unchanged, and Codex's checkout is untouched.

## Response to Codex repair review `FORMS_HUB_REVIEW_REPAIRS_20261003.md` (of `51ed59e`)
The remaining high-priority finding was correct. **Overlapping cleanups could erase a reused file ID.** In the old sequence:
1. Cleanup 1 read the queue.
2. Cleanup 2 erased file A and forgot its metadata.
3. An upload retry recreated A under the same UUID, and so under the same object key, and the form was republished with it.
4. Cleanup 1 then erased the new object and removed its metadata.

**Repair: team-form file IDs are retired permanently once they are queued for erasure.**
- **Upload refuses retired IDs.** The upload, in the same `BEGIN IMMEDIATE` transaction that would insert the row, refuses with 409 ("This file was deleted. Upload it again as a new file.") any `form_library` file ID that is queued (`form_library_cleanup`) or erased (`form_library_retired`).
- **Erasing leaves a permanent marker.** When an object is erased, `forget_file()` replaces its queue entry with a `kind='form_library_retired'` row in the same transaction. That marker is never removed.
- **A stale cleanup is harmless.** Object keys are `sha256(organization_id)/file_id`, so a cleanup working from an old snapshot can only delete an object key, and metadata, that can no longer be recreated in that organization. Its metadata step is idempotent.
- **Why there is no lease or generation check.** Because no reuse is possible, no claim or lease is needed, and no generation-conditional deletion either. This holds as long as every writer of `form_library` files goes through `/api/files` (the only writer today).
- **Tombstones, and no DDL:**
  - One small `module_records` row per erased team-form file, kept permanently: `id` = file ID, `kind='form_library_retired'`, payload `{entity_id}`. A rollback leaves them inert.
  - The generic modules API accepts only `forms` and `schedule`, so these rows are internal.
  - No new tables or columns.
- **Client effect.** The browser always uses a fresh ID for a new file. The add flow reuses an ID only while that entry is still pending, and a discarded or rejected entry resets it. In practice the 409 is reached only by a stale retry.
- **Regression:** `test_overlapping_cleanups_cannot_erase_a_reused_file_id`, which also runs as the PostgreSQL subclass, follows Codex's sequence:
  1. Publish A, then replace it with B during a storage outage, so A is queued.
  2. Pause cleanup 1 just before it erases A.
  3. Run cleanup 2 from a second app instance to completion.
  4. Retry the upload of A with its original UUID: **409**. Republishing A: **422**.
  5. Resume cleanup 1.

  The result: the form stays at version 3, published with B and downloadable by members; only B's object remains; and a fresh ID works normally.
  - **Verified to fail without the fix:** with the retired check disabled, the same test reproduces Codex's result, with the retry and republish both returning `(200, 200)`.
  - `test_retired_ids_are_per_organization_and_survive_deletion` checks that a fully deleted form's file ID can't be reused on a new form.

## Response to Codex review `FORMS_HUB_REVIEW_20261003.md` (of `74d9466`)
Both findings were correct and are repaired in the commit after the merge `81369d2`. That merge brought in `origin/enterprise-v2` at `0dc3450` cleanly; Codex's Atlas changes are kept, and so is the proposed Forms help text.

1. **Partial storage deletion corrupted an available form (high).** My earlier claim that a storage failure meant "nothing was deleted" was wrong: SQL rollback cannot undo an object deletion. The new design:
   - **Commit first.** Deletion and replacement first commit a durable state change, with no storage calls:
     - **Delete:** the form gets `deleting: true`, which hides it from everyone. Every file of the form is added to a cleanup queue.
     - **Replace or switch to a link:** the new source is published, and the previous file and any unattached uploads are queued.
   - **Queued files are unreachable** for admins and members (404) from that same commit.
   - **Then cleanup.** After the commit, each queued object is erased; only after that succeeds are its file row and queue entry removed. A deleted form's record and revision history are removed once none of its files remain queued.
   - **Every step is idempotent.** A failure leaves queue entries, and the form is never published while pointing at a missing object.
   - **Recovery runs later.** It happens when the delete request is repeated, through the admin-only `POST /api/forms/library/cleanup`, or automatically when an admin opens Forms Hub (`cleanup_pending` > 0).
   - **Honest responses.** Delete returns `{"deleted": true, "cleanup_pending": bool}`, and the UI says when erasure is still finishing. Atomic rollback across SQL and object storage is no longer claimed.
   - **No new DDL.** The queue is stored in the existing `module_records` table as `kind='form_library_cleanup'` (`id` = file ID; payload `{entity_id, object_key}`). The generic `/api/modules/{kind}` API accepts only `forms` and `schedule`, so these rows aren't exposed.
2. **Unfinished uploads were reachable by members (medium).** The shared file API now asks Forms Hub's `file_access()` for every `form_library` list, download and upload:
   - **Members** may list or download only the **current file of a published team form**. Unfinished entries, unattached uploads and abandoned replacements return 404, and link-only forms expose no files.
   - **Admins** may use any file of a live form except files queued for erasure.
   - **Other organizations** get 404 as before.

## Product direction (Ray, October 3, 2026)

The first commit on this branch (`a45cdab`) built saved form records with an internal review workflow. Ray then clarified the product, and the later commits replace that design:

- Forms are for the customer's use. Customers and their employees **download or print** the forms they need and do whatever they want with them.
- **No review is required, and no forms currently need signatures.**
- Forms are downloaded, not uploaded. The one exception is that **an organization admin uploads specific forms for their team** to access.
- The **C-85 is just another form** a customer can access. It is not bundled: an admin uploads the official copy.
- Built-in WZOS forms can optionally be **filled in on screen before printing or downloading. Nothing is saved.**
- Admin uploads are visible to **everyone in that organization**.

Ray's answers to the five open questions (the third revision):

1. **Keep the built-in WZOS printable forms.**
2. **Keep the two types**, "Official agency form" and "Company form", and **use the plural "forms" where appropriate.** The library is grouped under the headings *Official agency forms (n)* and *Company forms (n)*. A single card's badge stays singular.
3. **Improve the interrupted or failed upload process** (described below).
4. **Admins can permanently delete team forms.** I read this as covering every team form an admin added, official agency forms included, since all of them are the organization's uploads.
5. **Add Word, Excel and Google Docs options.**

## Reusable components found
- The existing private file store (`files.py`): `LocalFiles` for local use and `GoogleFiles` for private GCS with uniform access and public-access prevention. It provides type and signature checks, a 10 MiB limit, SHA-256 integrity checks on download, idempotent file IDs and attachment-only downloads.
- `module_records`/`module_revisions` provide version-checked metadata.
- The existing admin and member roles and the organization-scoped actor.
- Recovered V1 forms (`.local-recovery/core-build-baseline/src/pages/forms/`): the JSA option sets, the incident fields, and the DVIR fields already adapted in V2. V1's "Company Forms" page was an upload-and-download library on public Supabase URLs. The concept is reused here; the public-URL storage is not.

## Implemented behavior
- **A separate Forms Hub module:** `#forms-view`, `forms-hub.js`, `forms-hub.css` and `forms_hub.py`. Schedule management keeps `modules.js`/`#modules-view`.
- **Team forms:** each one is either an uploaded file or a Google link.
  - **Files:** PDF, PNG, JPEG, **Word (.docx)** or **Excel (.xlsx)**, up to 10 MB. Members download them.
  - **Google links:** Google Docs, Sheets, Forms or Drive. Members get *Open in Google Docs/Sheets/Forms/Drive*, plus Google export downloads where Google offers them:
    - Docs: PDF and Word.
    - Sheets: PDF and Excel.
    - Drive: the file.
    - Forms: open only.
  - All Google links open in a new tab with `noopener noreferrer`. Google's own sharing settings decide who can actually open the file; WZOS says so on the card.
  - The library is grouped under plural headings. Admins see unfinished entries in a separate *"n forms didn't finish uploading"* group; members never see them.
  - WZOS states that it does not edit or verify team forms or decide whether they apply (`verified_by_wzos: false`).
- **Word and Excel safety:**
  - These types are accepted **only for team forms**; work-order and form attachments stay PDF/PNG/JPEG.
  - The server opens the ZIP directory, without decompressing the contents. It requires the matching main part (`word/document.xml` or `xl/workbook.xml`) and `[Content_Types].xml`, and caps the package at 5,000 entries.
  - It **rejects macros**: any `vbaProject.bin`, or a macro-enabled content type.
  - Legacy `.doc`/`.xls` and macro-enabled `.docm`/`.xlsm` files are refused. The browser explains how to save them as `.docx`/`.xlsx` first.
- **Upload failures and interruptions:**
  - **Checked before sending:** the file type, empty files and the 10 MB limit are checked in the browser before any request. A bad file never creates an entry.
  - **Progress and Cancel:** the upload shows a progress bar and a *Cancel upload* button (XMLHttpRequest, 3-minute timeout).
  - **Automatic retry:** a dropped connection, timeout or temporary server error (0/408/429/502/503/504) is retried once automatically with the same file ID, so the server never stores the file twice.
  - **Retry or Discard:** if the upload still doesn't finish, the panel keeps the details and the chosen file and says what happened. *Retry upload* reuses the same entry and file IDs, so nothing is duplicated. *Discard* deletes the unfinished entry.
  - **Server refusals:** if the server refuses the file itself (wrong type, failed signature or macros), the empty entry is **deleted automatically** and the admin is told to choose a different file.
  - **Lost responses:** if a create succeeded but its response was lost, a retry recovers through the 409 and continues; an identical retry of the attach returns the stored result.
  - **Leaving mid-upload:** leaving the page, switching modules or changing identity during an upload asks first (or cancels cleanly).
  - **Unfinished entries** (for example, the tab was closed mid-upload) appear only to admins, with *Upload file* and *Delete*.
- **Permanent deletion:**
  - *Delete* asks for confirmation ("Permanently delete …? Its file will be erased from WZOS … This can't be undone."). It then erases the stored objects, the `workspace_files` rows, the metadata record and its revision history.
  - **Two phases (see the review response above).**
    - Phase 1 commits the hidden "deleting" state and the cleanup queue. If that transaction fails, nothing changes and the form stays published.
    - Phase 2 erases the objects and then the metadata. If it is interrupted, the form stays deleted and unreachable, the response says `cleanup_pending: true`, and the UI reports that its stored file couldn't be erased yet. Repeating the delete, the admin cleanup endpoint, or the next admin visit finishes it.
    - A retry after completion returns 404, which the client treats as already deleted.
  - **Replacing a file, or switching a form from a file to a link, erases** the previous file and any unattached uploads for that form, through the same queue. The new file is published in the same commit that makes the old one unreachable. If erasing fails, the replacement still succeeds and the old object is erased on a later cleanup. Earlier versions are not kept.
- **WZOS printable forms** (unchanged in this revision): JSA worksheet, Incident report and Vehicle inspection.
  - *Print blank*, *Download blank* (standalone HTML), or *Fill in* and then print or download.
  - Entries never leave the browser, and printouts are built from text nodes only.
- **Permissions and isolation:**
  - Members cannot create, edit, upload, replace or delete team forms (403).
  - Other organizations cannot list, download, upload to or delete them (404).
  - Records are keyed per organization, and deleting another tenant's entry with the same ID doesn't touch this one.
- **Design:** gloss-black panels and amber/gold accents.
  - The *Upload incomplete* badge and the unfinished group use a muted rust tone, and Delete has a rust outline.
  - Visible keyboard focus. The source choice is a radio group that works with the arrow keys.
  - Labelled buttons, such as "Delete VDOT Form C-85 permanently" and "Open … in Google Docs (new tab)".
  - The progress and status text is announced politely to screen readers.
  - One column on phones, and reduced motion is supported.

## Tests and actual results
- **Python, full suite** (after merging `enterprise-v2` through `5ae81ad` and applying both rounds of repairs): 264 tests, **OK, 35 skipped**. The skips are the 16 existing PostgreSQL cases plus 19 `PostgreSQLFormsHubTests`, because `WZOS_TEST_DATABASE_URL` isn't set.
  - An earlier run of the previous revision reported one uncaptured error that didn't recur.
- **`tests/test_forms_hub.py`** has 19 SQLite tests, also run as the PostgreSQL subclass. They include the two overlap regressions above. The first-review regressions:
  - **Second-object failure:** the first object is really erased and the second fails. The response is 200 with `cleanup_pending: true`, and the form is hidden from admins and members. Both files return 404 (not a broken 503), and upload or edit returns 404. After a **restart**, `cleanup` finishes: no objects or rows remain, and the delete retry returns 404.
  - **Database failure after an object was erased** (`forget_file` fails): the object is gone and its row stays queued, the form stays hidden, and repeating the delete finishes it.
  - **Failure before commit** (`queue_files` fails) on delete and on replace: 500, nothing hidden, queued or erased, and the published file still downloads.
  - **Replacement when the old object can't be erased:** the new file is published and downloadable, and the old file is 404 for everyone and missing from the admin file list. Cleanup later erases it.
  - **Members only reach the published file:** for an unfinished entry, members get 404 on both list and download while admins can list and download it. For an abandoned replacement upload, members see only the current file in the list and get 404 on the abandoned one, while admins can reach both. Other organizations get 404 everywhere.
  - **Link-only forms** expose no files to members.

  The earlier scenarios are still covered:
  - **Printables:** the catalog, with nothing stored.
  - **Publish and download:** an admin publishes and a member downloads byte-for-byte, including after a restart.
  - **Admin-only management:** unfinished entries are visible only to admins (`complete: false`).
  - **Isolation:** across organizations, including another tenant deleting its own same-ID entry.
  - **Validation, versions and retries:** includes an interrupted add whose attach is retried after it already succeeded.
  - **Replace and delete:** replacing erases the previous file and unattached uploads. Delete is permanent: objects, file rows, the record and revisions are all gone; a retry returns 404; and the ID can start over.
  - **Word and Excel:** accepted and downloaded with the right content type. Refused: macros (`vbaProject.bin` or a macro-enabled content type), a workbook labelled as Word, a truncated ZIP, legacy `.doc`, and a macro-enabled MIME type.
  - **Office types stay limited to team forms.**
  - **Google links:** Docs, Sheets, Forms and Drive, with the expected export downloads and the fragment stripped. Refused: http, a look-alike host, a host embedded in the path, credentials, a port, `javascript:`, Slides, a too-short ID, and a backslash trick. A form can't have both a file and a link, switching from a file to a link erases the file, and members can't add links.
  - **Without file storage:** links still work, and delete works.
  - **Concurrent edits:** exactly one 200 and one 409.
- **Node:** 13 of 13 passed (including Codex's newer test). `node --check` passes on all static JS.
- **PostgreSQL: NOT RUN.** There is no local PostgreSQL or Docker. Codex should run `python -m unittest tests.test_forms_hub -v` with `WZOS_TEST_DATABASE_URL` against a disposable schema.
- **Real browser:** Microsoft Edge (headless, via Node Playwright 1.62) on an isolated loopback preview with a fresh database, `LocalFiles`, synthetic identities and synthetic files (placeholder PDFs and minimal `.docx`/`.xlsx` packages, not agency files). I reran the run below after the review repairs, with the same results. The storage and database failure paths are covered by the Python tests, not the browser run. Every check passed:
  - **Uploads:** PDF (official agency form), Word and Excel (company forms) uploaded. The headings read *Official agency forms (1)* and *Company forms (2)*, and three stored objects existed.
  - **Google Docs link:** shows *Open in Google Docs*, *Download PDF* and *Download Word*, all with `https`, `target=_blank` and `rel=noopener noreferrer`.
  - **Refused in the browser:** `.doc` and an 11 MB PDF, with **zero requests sent**.
  - **Refused by the server:** a fake `.docx` got "broken.docx wasn't added: Not a valid Word (.docx) or Excel (.xlsx) file without macros. Nothing was saved …", and **no entry was left behind**.
  - **Interrupted upload** (connection aborted on both automatic attempts):
    - The message read "The upload of night.pdf didn't finish. The connection dropped during the upload. Your details and file are kept here. Select Retry upload, or Discard."
    - The unfinished group appeared.
    - *Retry upload* then succeeded with exactly one "Night work checklist" entry.
  - **Interrupted, then Discard:** the entry was removed.
  - **Cancel upload** during a request that never completed: the details were kept, and Retry and Discard were offered.
  - **An entry left without a file** was shown under "1 form didn't finish uploading" and finished from its card with an `.xlsx`.
  - **Member view:** grouped under *Official agency forms (1)* and *Company forms (5)*, with Download buttons and the Google links only. There was no add panel and no management buttons, and the `.docx` download was byte-identical.
  - **Permanent delete:** the confirmation text was correct, and stored objects went from 5 to 4.
  - **Keyboard:** Enter opens the add panel, and the arrow keys switch the source.
  - **Phone (390 px, reduced motion):** no horizontal overflow.
  - **Console:** only expected entries: the existing favicon 404, the deliberate 415, and the deliberately aborted requests.
  - **A bug the browser run found and I fixed:** after one successful add, the form reset cleared both source radios, so the next add was treated as a link. The default source now survives the reset.
- **Screenshots** (compressed WebP, synthetic data, `docs/screenshots/forms-hub/`, about 440 KB in total):
  - `01-admin-team-forms`: grouped library with a Google link.
  - `02-member-forms-hub`
  - `03-jsa-blank-print`
  - `04-incident-fill-in`
  - `05-admin-interrupted-upload`
  - `06-mobile-admin`

## API and schema changes
- **Startup DDL: none, and no migration.**
  - Team-form metadata uses the existing `module_records`/`module_revisions` with `kind='form_library'`. A deleted form keeps `deleting: true` in its payload until cleanup finishes.
  - The cleanup queue uses existing `module_records` rows with `kind='form_library_cleanup'`. Erased file IDs keep a permanent `kind='form_library_retired'` row so they can't be reused.
  - Files use the existing `workspace_files` table and object store with `entity_kind='form_library'`.
- **Authenticated endpoints:**
  - `GET /api/forms/templates` and `GET /api/forms/templates/{id}/{revision}`
  - `GET /api/forms/library`: items carry `file`, `link` (with `url`, `service` and `downloads`) and `complete`. Admins also get `cleanup_pending`, a count.
  - `PUT /api/forms/library/{id}` (admin): body `{expected_version, title, category, description, file_id | link}`. The response adds `cleanup_pending` (bool) for that form.
  - `POST /api/forms/library/{id}/delete` (admin, permanent): body `{expected_version}`, response `{deleted, cleanup_pending}`. Repeating it while cleanup is pending finishes the cleanup, without a version check. It **replaces** the earlier soft `/remove`, which was never deployed.
  - `POST /api/forms/library/cleanup` (admin, idempotent): response `{cleanup_pending}`.
  - Static `/forms-hub.js` and `/forms-hub.css`
- **Shared file contract (`files.py`), additive:**
  - `OFFICE` and `KIND_TYPES`: Office types are allowed only for `form_library`; `order`/`form` are unchanged.
  - `office_document_ok()` validates `.docx`/`.xlsx` packages.
  - `LocalFiles.delete()` and `GoogleFiles.delete()`, both idempotent (a missing object is fine).
  - `parent(..., write=False, file_id=None)`: for `form_library`, delegates to `forms_hub.file_access()`. Download passes the file ID, and listing filters rows through the same rule. The `order`/`form` rules are unchanged.
  - **Removed:** the `delete_entity_files()` helper from `74d9466` (the unsafe in-transaction deletion).
- **`app.py`:** passes `file_store` to `forms_hub.register` instead of a boolean.
- **GCS permission to confirm (Codex):** erasing needs `storage.objects.delete` on the private bucket for the runtime service account. Without it, deleted forms are still hidden and replaced files are unreachable, but the objects stay in the bucket and `cleanup_pending` stays above zero until the permission is granted.

## Changed files (relative to `3247a18`)
- **New:**
  - `services/workspace_preview/forms_hub.py`
  - `services/workspace_preview/forms_catalog.json`
  - `static/forms-hub.js`
  - `static/forms-hub.css`
  - `tests/test_forms_hub.py`
  - `docs/FORMS_HUB_COMPLETION.md`
  - `docs/screenshots/forms-hub/*.webp`
- **Shared (narrow):**
  - `app.py`: import and one registration line.
  - `files.py`: as described above.
  - `static/index.html`: the view, the print container, one stylesheet link and one script tag.
  - `static/workspace.js`: the view switch and the leave guard.
  - `static/modules.js`: now serves Schedule only.
  - `tests/atlas_navigation.test.cjs`
  - `modules.py`: unchanged from the base.
- **Proposed module-help text (for Codex review, text only):** the `forms` entries in `intelligence.py` and `static/assistant.js`. They now mention grouped official agency forms and company forms, Word, Excel and Google links, and permanent delete.

## Remaining gaps
- PostgreSQL execution of the new tests (Codex gate).
- **No malware scanning** of uploads; this is an existing launch gate. Macro-free Office files are a reduced risk, not a scanned one.
- **WZOS can't check Google links.** It doesn't know whether a Google file is shared with the team, or whether it is later moved or deleted in Google. Google's sharing settings control access.
- **Google export downloads use Google's export endpoints.** They work for users Google lets open the file.
- **Legacy form drafts:** drafts made by the old Forms UI (`/api/modules/forms`) still appear in the Work Zone Report's "Linked form drafts" (Codex-owned), but not in Forms Hub.
- Hidden Forms markup and code in `#modules-view`/`modules.js` is unreachable but not yet removed. That cleanup belongs with the Schedule increment.
- Downloaded WZOS printables are HTML, which can be printed or saved as PDF; server-side PDF generation is Codex-owned.
- The JSA option lists come from V1 and haven't been reviewed by a safety professional.

## Open product decisions
None are outstanding from Ray's latest answers. To confirm, if needed:
- **Who can delete:** I applied permanent delete to **all** team forms, not just company forms.
- **Google Slides:** links aren't accepted. Ray asked for Google Docs, and Sheets, Forms and Drive files were added as the closest form-related options.

## Integration instructions (for Codex)
1. Review PR #2. The shared backend changes are the additive `files.py` contract above and the one `app.py` line. The Atlas help text is proposed for your review.
2. The branch now contains `origin/enterprise-v2` at `0dc3450` (merge `81369d2`). Rerun the full Python and Node suites on the integrated candidate.
3. Run `tests/test_forms_hub.py`, including `PostgreSQLFormsHubTests`, against a disposable Cloud Shell PostgreSQL schema.
4. Confirm the staging runtime service account can delete objects in the private bucket (`storage.objects.delete`).
5. On staging with synthetic accounts and private GCS:
   - an admin uploads a synthetic PDF and a synthetic `.docx`, and a member downloads both
   - another organization is refused
   - an admin replaces a file, and the old object is gone from the bucket
   - an admin deletes a form, and its object is gone from the bucket
   - a member can't list or download an unattached upload
   - optionally, with delete permission temporarily withheld, a delete reports `cleanup_pending` and finishes after the permission returns
6. No startup DDL or migration is involved. I haven't touched `SESSION_HANDOFF.md` or `REMAINING_TASKS.md`.

## Rollback
- **Code:** revert the merge. Forms then returns to the old `modules.js` draft UI. `form_library` metadata and files remain in storage but are no longer reachable through the API. Any `form_library_cleanup` queue rows and `form_library_retired` markers remain as inert `module_records` rows. After a rollback, list their `object_key` values to erase those objects manually, or keep them.
- **Data:** nothing to drop; no tables were added. Deletions and replacements made while this was live are permanent by design and **can't be undone by a rollback**.
