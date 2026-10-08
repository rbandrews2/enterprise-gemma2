# PR #2 retired-ID repair review

Reviewed `01d4b426e30b8ed87f5cfcb5eb66dd8e4f98d404` (base includes current
`enterprise-v2` through `5ae81ad`). Decision: **changes still required; not merged**.

The permanent retired marker closes the previously reproduced Forms Hub to
Forms Hub reuse path. It is checked inside the upload transaction, and retirement
survives removal of the form. Existing tables are reused without new startup DDL.

## High priority: retirement must cover the shared object-key namespace

In `services/workspace_preview/files.py:158`, the retirement check runs only
when the new upload's `entity_kind == 'form_library'`. However, every file type
uses the same storage key: organization hash plus file UUID (`:150`). Work-order
and legacy-form attachments can recreate a retired key. The stale cleanup then
erases that object and deletes its new metadata without checking its entity kind.

Confirmed locally using synthetic data and the real API/storage code:

1. Create a work order and publish team-form file A.
2. Replace A with B while injecting a storage failure, leaving A queued.
3. Pause cleaner 1 after its queue read, immediately before object deletion.
4. Let cleaner 2 finish erasing/forgetting A and write its retired marker.
5. Upload a work-order attachment using A's UUID with `entity_kind=order`.
   Upload returns **200**, and downloading the new attachment returns **200**.
6. Resume cleaner 1. It returns pending=0, but the new attachment's download
   now returns **404**: its object and metadata were erased.

This is the same overlapping-cleaner fault model used in the prior review, now
crossing module boundaries within one organization. It is not cross-tenant access
and does not require UUID guessing: upload clients choose and retry their IDs.
The same missing retirement check also exists for `entity_kind=form`.

## Required correction and tests

Apply the queued/retired-ID check to **all uploads sharing that organization's
object-key namespace**, not only new Forms Hub uploads. Preserve the transaction
lock and organization scope. Retaining a retired marker must prevent the same
key from being recreated through any module. Do not remove retirement records
while stale cleanup could still run.

Extend the overlap regression with retries through both `order` and `form`:
expect 409, confirm the current Forms Hub replacement survives, and confirm fresh
UUIDs still upload normally. Also test retired IDs after a completed deletion
and across restart. Keep the corresponding PostgreSQL cases.

## Validation

Full Python suite: 264 cases, 229 passed and 35 PostgreSQL skipped (66.288s). Node: 13 passed. The suite does not cover the cross-module overlap reproduction above. Review used an isolated
ignored archive at `.local-data/review-forms-01d4b42`, with logs in
`review-python-results.txt` and `review-node-results.txt`. The reproduction above
was independently executed. Claude's worktree was not modified.

No merge, cloud changes, deployment or customer communication. PostgreSQL and
private-GCS integration gates remain open until the correctness repair passes.
