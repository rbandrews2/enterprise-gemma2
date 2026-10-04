# Claude Forms Hub review — changes required

Reviewed PR #2, `claude/forms-hub` at `74d9466a8a364e76cb009fb87f0e8f63a1e59872`.
Base: `3247a18`. Integration target at review: `enterprise-v2` / `15fc587`.
Decision: **do not merge or deploy this revision**. Claude's checkout was not
modified. Tests used a separate ignored archive of the committed branch under
`.local-data/review-forms-74d9466` with synthetic data and local file storage.
This review concerns Forms Hub; Time Clock PR #1 remains a separate gate.

## 1. High priority: partial storage deletion corrupts the available form

Locations on the reviewed branch: `services/workspace_preview/files.py:112-115`
and `services/workspace_preview/forms_hub.py:132-139`.

`delete_entity_files` erases objects before the database transaction commits.
A database rollback cannot undo an object deletion. If the second deletion
fails, the first object is already gone but its file row and published form
remain. Replacement has the same failure path. A database commit failure after
successful object deletion is another instance of the same problem.

Reproduced with the branch's `FormsHubTests` fixture:

1. Publish one PDF using `published()`; upload an unattached second PDF.
2. Patch `LocalFiles.delete`: actually delete the first key, then raise `OSError`
   on the second call.
3. Request deletion of the form at version 2.

Actual results: deletion **503**, message **"nothing was deleted"**, one object
remaining, library item still **complete=true**, published-file download **503**.
The existing failure test throws on the first object and misses partial success.

Required repair: use a durable deletion/replacement state and idempotent cleanup
that survives partial object failures and database failures. Do not report atomic
rollback across SQL and object storage. Persist the intended transition before
irreversible cleanup; distinguish pending/failed cleanup from available content.
Any new startup DDL must follow the collaboration contract's migration review.
Add second-object-failure, post-delete database failure, replacement failure and
retry/restart tests on SQLite and PostgreSQL.

## 2. Medium priority: unfinished uploads are accessible to members

Locations: `services/workspace_preview/files.py:130-136`, `:175-188`.

The Forms Hub listing hides incomplete entries, but the shared file API checks
only that the parent record exists. A member can list and download files that
were uploaded but not attached/published. This also exposes abandoned replacement
uploads belonging to an otherwise published entry. This is within one tenant;
the reproduced issue is not cross-organization access.

Reproduction: create a version-1 library entry, upload a PDF, and do not attach
it. Member `/api/forms/library` returns no items, while member
`GET /api/files?entity_kind=form_library&entity_id=<id>` returns **200** with the
file ID, and `GET /api/files/<id>` returns **200** with its contents.

Required repair: enforce publication at the file API. For members, list/download
only the current `file_id` referenced by the organization's published library
record. Keep incomplete and unattached files admin-only. Add tests for incomplete
entries, abandoned replacements, current published downloads and tenant denial.

## Validation and outstanding gates

- Focused Forms Hub suite: **24 cases, 12 passed, 12 PostgreSQL skipped**.
- Two additional fault/access reproductions above independently confirmed.
- Full branch Python suite: **239 cases, 211 passed, 28 PostgreSQL skipped** (49.212 seconds). Node: **12 passed, 0 failed**. These are branch-level results, not an integrated-candidate acceptance. Logs are in the ignored review archive as `review-python-results.txt` and `review-node-results.txt`.
- No PostgreSQL, private GCS deletion or new browser acceptance was performed.
  Confirmed correctness defects already prevent merge; those gates remain required
  after repair. Claude's reported screenshots are evidence from Claude, not a new
  independently executed browser run.
- No changes to runtime code, Claude's worktrees, staging, V1, DNS or production.

## Claude follow-up

Repair these two findings on `claude/forms-hub`, add regression tests, and update
`docs/FORMS_HUB_COMPLETION.md` to describe actual failure/recovery behavior.
Reconcile with current `enterprise-v2` per the collaboration contract, preserving
Codex's Atlas work. Codex then reviews the revised commit, runs integrated Python
and Node suites and the disposable PostgreSQL gate, and checks private GCS and UI
behavior before merge/deployment acceptance. No message was sent to Claude by
this review; Ray can relay this committed handoff.
