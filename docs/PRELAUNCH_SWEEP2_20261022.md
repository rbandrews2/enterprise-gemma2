# Prelaunch sweep 2 — access, cache privacy and recovery readiness

October 22, 2026. Engineering checks completed independently. Production traffic
remains 100% on `wzos-v2-accounts-ui-16d0905`; no production configuration, IAM,
secret payload, customer object, paid workload or provider delivery was changed.
Cloud Shell was reconnected and the account/project were verified again.

## Findings that need follow-through

| Priority | Finding | Repair / next step |
| --- | --- | --- |
| Before launch | Four enabled operational alert policies have **zero notification channels**. They cover app 5xx errors and SQL CPU, memory and disk thresholds. | Keep the policies; attach an approved, monitored recipient/channel and verify delivery with authorization. A question requesting the monitored email is pending. An enabled condition alone does not deliver an email. |
| Before claiming completed file erasure | Observed runtime storage roles do not include `storage.objects.delete`, which retired-form cleanup uses. | Confirm effective access, including any group-derived bindings, then review the narrow [cleanup-access proposal](FILE_CLEANUP_ACCESS_PROPOSAL_20261022.md). No permission was granted. The app hides the deleted item and keeps failed cleanup queued; that is not completed physical erasure. |
| Next release | Database URL and browser-auth key use mutable `latest` references. | Both currently have exactly one listed version, numeric **1**, enabled. Pin those validated versions during the next approved release, with fresh drift checks. Do not read/print secret payloads or rotate credentials just to pin them. Current instances were not reconfigured. |

The two mutable references are `wzos-v2-staging-database-url` and
`wzos-v2-staging-auth-web-key`. This is a reproducibility/rollback improvement,
not evidence that either credential is wrong or compromised.

## Access inspection

Runtime: `wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com`.

- Direct project grants: `roles/cloudsql.client` and three custom roles.
  Role definitions contain only `firebaseauth.users.get`,
  `firebaseauth.users.createSession` and `speech.recognizers.recognize`, respectively.
- All ten bound secrets have resource-scoped `roles/secretmanager.secretAccessor`
  for the runtime; no project-level Secret Accessor was observed.
- Bucket direct grants: objectCreator, objectViewer and legacyBucketReader.
  Google's role definitions confirm none contains a delete permission.
- No direct runtime organization grant was found. No allUsers/allAuthenticatedUsers
  grant appeared in the captured project, bucket, ancestor or private-service policies.
- Private scanner and Atlas inference retain invocation checks. Their inspected
  service-level invoker bindings contain only the WZOS runtime, without public
  principals. This was metadata inspection, not a model/scanner invocation.

Limits: this is a direct-principal policy review, not a complete effective-access
attestation. Group membership, every unbound resource policy, deny policies and
conditional evaluation are not fully covered. Policy Troubleshooter returned
`SERVICE_DISABLED`; it was not enabled and no access grant was added to complete
the check. Secret payloads were never accessed.

## Focused automated acceptance

**18 checks passed, zero skips**; no unrelated full suite rerun this sweep.

- Seven new GoogleFiles adapter checks: reject non-private buckets; create-only
  writes with digest metadata; identical/conflicting retries; generation-pinned
  reads; pre-download size bound; failure on changed generation; missing-delete
  idempotency and propagation of other storage errors. Synthetic SDK objects only.
- Five new public service-worker cache checks: exclude APIs/files/audio/exports,
  external and POST requests; refuse persistence without public markers; require
  release-addressed static assets; preserve unrelated/offline device caches during
  activation; avoid intercepting query-bearing navigation and the worker itself.
- Six existing update-flow checks pass alongside them: user-controlled install,
  unsaved-work guard, offline/meeting/upload protection, release-specific dismissal,
  rollback and failed version reads. Actual installed-device acceptance is separate.

Commands:

```text
python -m unittest tests.test_google_files
node --test tests/public-cache.test.cjs tests/app-updates.test.cjs
```

Only tests, read-only audit tooling and documentation were added. No runtime code
or migration changed in this sweep. The previous full gate and dependency repair
provenance remain in [sweep 1](PRELAUNCH_ENGINEERING_RESULTS_20261022.md).

## SDK provenance and operational metadata

Vendored Daily SDK matches the public npm package `@daily-co/daily-js` **0.93.0**
byte-for-byte. Registry tarball SHA-512 integrity verified. Local/upstream JS SHA256:
`c6a5cae720b07b1f8c371977808b14379eca5a374329902d160b57484ef750d9`.
The public registry's package/version advisory query returned no matching entries.
This does not clear every bundled/transitive library: declared dependencies use
ranges, and a newly resolved tree would not prove what is inside the old bundle.
Full bundle/SBOM and container/OS review remain open. No SDK code was executed
during artifact comparison and no media call was started.

A successful bounded log query (last 24 hours, maximum 50 records) returned zero
matching app ERROR or HTTP 5xx records. Request bodies, headers and log messages
were excluded. This does not prove every user journey works or replace alerting.

Bucket metadata confirms versioning, a lifecycle rule deleting noncurrent versions
after 30 days and seven-day soft-delete retention. Lifecycle timing is asynchronous;
do not promise an exact 37-day erasure deadline. Business retention choices and
real object/managed-database restore acceptance still remain open.

## Evidence / handoff

Source checks: `e8d455e` (audit + storage tests) and `b16ed82` (cache tests).
Local ignored evidence: `.local-data/prelaunch-sweep2-20261022/daily-sdk-audit.json`
and its bounded artifact-check script. Cloud private evidence:
`/tmp/wzos-sweep2-20261022.M8CLjJ0U`, home pointer
`wzos-sweep2-latest-path.txt`; durable copy
`$HOME/wzos-sweep2-evidence-20261022`. Keep raw runtime/policy snapshots outside Git.

Next actions: obtain the alert recipient; finalize numeric secret references at
release; complete effective delete-access diagnosis and any separately approved
cleanup permission repair. Keep actual customer-file deletion, real notifications,
provider acceptance, paid image review and managed restores outside this sweep.
