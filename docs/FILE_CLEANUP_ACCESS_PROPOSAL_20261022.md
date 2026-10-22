# Retired-file cleanup access — review proposal, not applied

## Finding

The WZOS runtime's observed bucket grants are objectCreator, objectViewer and
legacyBucketReader. None provides `storage.objects.delete`. Observed direct project
grants are Cloud SQL client and three single-permission account/Speech roles.
No direct organization grant was found. Group-derived permissions remain outside
this inspection; Google's Policy Troubleshooter API is disabled, so a complete
effective-access verdict was not obtained. No API was enabled to finish the audit.

Forms Hub removal commits a hidden/deleting state before attempting object
cleanup. Storage failures stay queued and files remain unavailable through WZOS;
the application must not describe that state as completed physical erasure.
This is a launch follow-up, not evidence of a data leak or compromise.

## Smallest proposed repair, if effective denial is confirmed

- Create `projects/enterprise-gemma2/roles/wzosFileCleanup` using
  `file-cleanup-role.proposed.yaml`.
- Grant it only on bucket `enterprise-gemma2-wzos-v2-files-staging`, only to
  `wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com`.
- This adds one permission: `storage.objects.delete`; no objectAdmin, project
  storage role, bucket update, secret, database or IAM management permission.
- The permission covers **all objects in this shared bucket**, not just forms.
  Application authorization, retired-ID guards and Atlas holds remain essential.
  A separate cleanup identity/service can reduce the app identity's privileges,
  but requires additional architecture and separately approved workload/access.

New delete access requires explicit approval before applying it. Granting it may
allow previously queued cleanup to complete on a later admin operation. Inspect
queue counts and the agreed retention/hold policy first; do not run a backlog
cleanup as an unassisted acceptance test or delete customer objects to test access.

## Acceptance and rollback

After applicable approval, check effective permission first, then use only a
separately authorized synthetic file to verify the intended remove/retry/recovery
flow and current versioning/soft-delete behavior. A real managed-object restore
remains distinct from mocked adapter checks or a local database restore.

Rollback removes only the new runtime/bucket binding, retaining previous grants.
That stops subsequent cleanup attempts; it does not restore an already deleted
object. Recovery must use the bucket's verified version/soft-delete procedures.
No destructive command, resource mutation or real-file cleanup is part of this
proposal.
