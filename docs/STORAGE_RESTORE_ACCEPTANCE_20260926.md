# Restricted staging file and recovery acceptance

## Scope

Only `enterprise-gemma2`, `wzos-v2-accounts`, `wzos-v2-staging-db` and the
private `enterprise-gemma2-wzos-v2-files-staging` bucket. Synthetic fixtures only.
No V1 deployment, DNS changes, customer data or outbound messages.

## Private files

`scripts/validate_managed_files.py` uses real provider tokens and deployed app
routes. It verifies a synthetic PNG upload, identical retry, conflicting retry,
invalid MIME signature, exact download bytes and SHA-256, attachment disposition,
no-store/nosniff headers, admin/member access, other-organization denial and
anonymous Cloud Run/GCS denial. Operator evidence also records object generation.

Upload acceptance passed on `wzos-v2-accounts-00004-fc6`. A configuration-only
rollout created `wzos-v2-accounts-00005-2ns`, serving 100% of traffic, with the same
application image. Post-rollout reads passed: exact bytes and hash, admin/member
access, cross-organization denial, and anonymous service/object denial. The script
asserted that the serving revision differs from the upload revision.

## Repeatable recovery drill

1. Prepare isolated synthetic users with `validate_managed_accounts.py prepare`;
   keep its mode-0600 state outside Git. Never print tokens or send test emails.
2. Upload a synthetic attachment and preserve non-secret file evidence separately.
3. Run `validate_restore_snapshot.py --port 5544 --output <new-source-json>`.
   This fingerprints all public application table rows in one repeatable-read,
   read-only transaction. Evidence contains only counts and hashes, not rows.
4. Create an on-demand native Cloud SQL backup of `wzos-v2-staging-db`; wait for
   SUCCESSFUL. Record its ID. Freeze acceptance writes during the snapshot/drill.
5. Create a uniquely named temporary restore instance in us-central1 with the same
   PostgreSQL major version, db-g1-small tier and 10 GiB disk. Require the SQL
   connector and encrypted connections; do not grant authorized networks or new
   users. Do not point the app at the temporary instance.
6. Restore the recorded backup with `--backup-instance=wzos-v2-staging-db` and
   `--restore-instance=<verified-temporary-name>`. Never target the source.
7. Connect a separate loopback SQL proxy on 5545. Run
   `validate_restore_snapshot.py --port 5545 --output <new-restored-json>
   --compare <source-json> --file-evidence <file-evidence-json>`. All table counts
   and row fingerprints must match.
8. Confirm the restored attachment record still references the preserved object.
   SQL backups do not contain Cloud Storage bytes; object protection is separate.
9. Remove only the verified temporary restore instance, stop its proxy, disable
   synthetic users/revoke refresh tokens, disable synthetic organizations, and
   preserve the non-secret evidence. Verify temporary resource removal.

The comparison checks data content, not a full schema/permission migration or
application disaster-recovery failover. Record actual elapsed recovery time rather
than claiming a contractual RTO. Bucket version recovery, scanning, operational
alerts, real email delivery and production release remain separate gates.

## Execution record

- Initial source snapshot: 16 application tables, 34 rows.
- On-demand backup ID: `1790400494832`, status SUCCESSFUL.
- Temporary destination: `wzos-v2-restore-check-20260926`.
- Native restore operation: `52e61350-f107-4605-8a52-b77200000032`, DONE without
  error, 2026-09-26 05:30:58.395–05:34:38.974 UTC (about 3 minutes 41 seconds).
  This excludes instance creation, verification and cleanup; it is not an RTO.
- Restored comparison: PASS, all 16 tables and 34 rows matched. Restored private
  file metadata and original object generation verified against SHA-256 and size.
- Negative control: deliberately altered source fingerprint rejected with nonzero
  exit and no success-evidence file.
- Cleanup: four synthetic provider users disabled, refresh tokens revoked, both
  test organizations disabled, operator state stripped of tokens, restore proxy
  stopped. Cloud Run IAM rechecked: no public principal. Temporary instance
  deletion completed at 05:38:40.157 UTC, operation
  `0f16bbe9-8d30-46b8-9362-36ca00000032`, DONE without error. Instance inventory
  afterward contains only `wzos-v2-staging-db`, RUNNABLE. No temporary database
  remains billing; the on-demand source backup is retained as recovery evidence.

Non-secret attachment evidence: file `6e78d137-08e9-495d-b2ba-c837974dc58f`,
order `07011c0a-e6a8-409f-a69d-347c101e1135`, organization
`9d06fc2c-40ad-4ce2-a969-730a597ccd2c`, object generation `1790400396823588`,
70 bytes, SHA-256
`abc58d5127d7cdf313beb9ec8ee839860a9c6bfbc48c8b8eb6a3f7d8bb63de6f`.
Anonymous object and service requests returned 403; other-organization access
returned 404. The test object remains private in the disabled synthetic organization.

Detailed Cloud Shell evidence is temporary and not Git-backed:
`/tmp/wzos-file-evidence.json`, `/tmp/wzos-file-after-revision.json`,
`/tmp/wzos-restore-source.json`, `/tmp/wzos-restored-evidence.json`,
`/tmp/wzos-restore-verification.log`. This document preserves the measured result
and IDs; operator state files with credentials must never be committed.
