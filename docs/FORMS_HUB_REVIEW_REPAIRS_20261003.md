# PR #2 repair review

Reviewed `51ed59e9dc5844900bd500de1b29ac5ee6f0e887`, including its merge of
`enterprise-v2` through `0dc3450`. Review only; no merge or deployment.

## Original findings

Both original reproductions are now covered and pass locally:

- Partial object deletion hides the deleted form, persists pending cleanup and
  recovers on retry/restart. Replacement publishes the new file before erasing
  the old one. Responses no longer promise SQL rollback can restore objects.
- Member listing/download checks permit only the current published file;
  unfinished and unattached uploads are denied. Tenant checks remain intact.

The repair reuses existing tables; no new startup DDL. Claude also retained the
current Atlas changes when updating the branch.

## Remaining high-priority finding: stale cleanup can erase a reused file ID

Location: `services/workspace_preview/forms_hub.py:200-211` on the reviewed branch.

Cleanup snapshots its queue without a claim or lock spanning deletion. Two
requests can hold the same entry. Once the faster request erases the object and
removes its metadata, upload accepts that UUID again and recreates the same object
key. The slower cleanup still deletes that key and unconditionally removes its
new metadata. Missing-object idempotency does not protect against key reuse.
File upload retries deliberately reuse IDs, so this is an API-supported sequence,
although it requires overlapping cleanup and a retry/republication.

Deterministic local reproduction using the committed test fixtures:

1. Publish file A; replace it with B while injecting a storage outage. A remains
   queued, B is published.
2. Start cleanup request 1 and pause immediately before its `LocalFiles.delete`.
3. Run cleanup request 2 to completion: A is erased and forgotten (pending=0).
4. Retry uploading A using its original UUID, then publish it at version 3.
   Both requests return **200**, and the form advances to version 4.
5. Resume request 1's stale deletion and metadata removal.

Actual result: request 1 returns pending=0; the admin's version-4 form now has
`file=null`, `complete=false`; members see no form; its download returns **404**.
The successfully republished object and metadata were erased. The interleaving
was injected at the storage method; API, database and local-object operations
ran normally against synthetic data. This is not a live-GCS reproduction.

Required repair: prevent deleted IDs/object keys from being reused while any
stale cleanup can act on them, or implement claimed/versioned cleanup with
generation-safe object deletion and matching conditional metadata deletion.
A database check alone before deleting the object leaves a race. Add a regression
with two overlapping cleaners and upload retry/republication, including the
PostgreSQL variant. Document any tombstones, leases or DDL needed for the fix.

## Validation

- Full Python suite: **260 total, 227 passed, 33 PostgreSQL skipped**, 50.348s.
- Full Node suite: **13 passed**.
- New deterministic overlap reproduction: confirmed data loss as above.
- Tested an isolated archive in `.local-data/review-forms-51ed59e`; full logs are
  `review-python-results.txt` and `review-node-results.txt` there.
- PostgreSQL, private GCS and updated browser acceptance remain open. No cloud
  resource, IAM, production or Claude-worktree changes were made.

Decision: the two earlier defects are repaired for tested sequential cases, but
**do not merge yet** due to the confirmed overlapping-cleanup defect. After repair,
rerun this regression and required PostgreSQL/GCS/UI integration checks. This
review was saved for Ray to relay; no message was sent to Claude.
