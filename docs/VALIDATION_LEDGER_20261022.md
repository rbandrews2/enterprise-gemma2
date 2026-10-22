# Validation ledger — reuse passing evidence

This is the index of accepted checks and repaired failures. Preserve the raw
artifacts and commit/image provenance. Do not rerun a check merely because the
conversation or Cloud Shell restarted. Verify applicability first.

## Reuse rules

1. Identify the exact source, requirements, image and runtime configuration.
2. Reuse accepted evidence for unchanged components. Documentation/test additions
   do not invalidate runtime behavior already tested. Configuration-only repairs
   use configuration diffs, readiness and a bounded public smoke check.
3. Retest only changed behavior, new failures or a concrete unresolved concern.
   An immutable new app image still needs the release gates required by the
   collaboration contract. Do not treat focused tests as a new full gate.
4. No automatic repeat of paid Speech/model pilots, real SMS, real billing,
   customer-file deletion or human acceptance. Obtain applicable authorization
   and a reason before repeating them.
5. Keep failed runs and their repair results. Never replace FAIL with PASS in
   the historical artifact or sum repeated checks as unique test coverage.

## Accepted engineering evidence

| ID | Scope / provenance | Accepted result | Evidence |
| --- | --- | --- | --- |
| LIVE-TRAINING-FOOTER | Source16d0905, image80c3819a…, deployed ui-16d0905 | 16 PostgreSQL +10 Node, zero skips; staged/public release checks PASS | TRAINING_FOOTER_RELEASE_20261022.md; cloud `/tmp/wzos-training-footer-20261022.y7ej7c0f` |
| NODE-FULL | Sweep1 source through90fdc43; JS unchanged by8d29bbf/backend-only changes | 174 PASS, zero skips, Windows/Linux | PRELAUNCH_ENGINEERING_RESULTS_20261022.md; node-final.log/node-policy.log; cloud node.log |
| COMMUNICATIONS | Enterprise boundaries / downgrade opt-out,90fdc43 | 38 focused backend PASS, zero skips | local `.local-data/prelaunch-20261022/communications.log` |
| PG-FULL | Repaired app code8d29bbf, prior dependency pins | 891 PASS, zero failures/errors/skips,399.936s | cloud postgres-final.log/postgres-final.exit0 |
| PG-DEPENDENCIES | Dependency-only change dfef889 | 119 affected PASS, zero skips,49.621s | cloud dependency-postgres.log/dependency-postgres.exit0 |
| PYTHON-ADVISORIES | Installed app environment after dfef889 | 57 packages inspected; zero known advisories, exit0 | cloud python-vulnerabilities-repaired.json/.log/.exit |
| SIGNED-RESTORE | Synthetic native PostgreSQL source/target,8d29bbf | Form/signature/payload hashes and received status preserved; auth/tenant denial; cleanup verified | cloud restore.log/restore.exit0/signed-restore.json |
| LIVE-PUBLIC-SMOKE | Live ui-16d0905 | Eight anonymous401/no-store APIs, foreign Origin403, public version/manifest/icons/footer accepted | local public-smoke.json |
| DOT-INDEX | Unchanged seven originals, rebuilt derivative schema6 | 2,627 pages; hashes/fingerprints/integrity/local retrieval accepted | local dot-readiness.json/dot-inventory.json; **not source review or inference acceptance** |
| GOOGLE-FILES | Synthetic SDK adapter contracts,e8d455e | Seven PASS, zero skips | `python -m unittest tests.test_google_files`; sweep2 tool output/report |
| CACHE-UPDATES | Five new privacy/cache +six existing update checks,b16ed82 | Eleven PASS, zero skips | `node --test tests/public-cache.test.cjs tests/app-updates.test.cjs`; sweep2 report |
| DAILY-ARTIFACT | Vendored0.93.0 | Exact upstream bytes, verified tarball integrity; direct-package advisory response empty | local `.local-data/prelaunch-sweep2-20261022/daily-sdk-audit.json`; **not complete bundle or media acceptance** |
| ACCESS-METADATA | Sweep2 live app/secret/project/bucket/private-service policies | Direct grants captured; private invocation checks confirmed; effective access limitations recorded | PRELAUNCH_SWEEP2_20261022.md; private cloud sweep2 artifacts |

Sweep1 private cloud artifacts were copied into
`$HOME/wzos-prelaunch-evidence-20261022`; sweep2 into
`$HOME/wzos-sweep2-evidence-20261022`. Local evidence paths above are relative to
the owned integration checkout. Raw runtime metadata, originals and credentials
are not Git-backed. A missing temporary folder does not mean the tests need to
be repeated: first check the durable copy and recorded source/image identifiers.

## Failures repaired — retain history

| Original result | Cause / resolution | Replacement evidence |
| --- | --- | --- |
| Node174:172pass/2fail | Fake DOM lacked real element `dataset`; fixture repaired | Node174PASS |
| PG890:889pass/1error/0skip | Synthetic demo attempted now-forbidden Core messaging; demo corrected | PG891PASS at8d29bbf |
| Python advisory audit:30 findings in3 packages | Updated certifi, Pillow, pypdf; no advisory reproducer executed | 119 affected PASS and advisory exit0 |
| Local dependency checks93:69pass/23skip/1 import error | No local PG configured; test_source_package required tests on PYTHONPATH | Corrected source-package2PASS; cloud119PASS/0skip |
| Initial pip-audit invocation error | Unsupported flag combination, invocation corrected | Actual audit artifacts and repaired scan retained |
| Policy Troubleshooter unavailable | API disabled; not enabled during read-only audit | Not a passing effective-permission check; remains a limitation |

## Human acceptance — do not repeat without a change or new concern

- [x] **HUMAN-VOICE-INCIDENT-20261022:** Ray reports creating an incident with
  Smart Field Voice, receiving the notification inside WZOS, reviewing the form,
  confirming correct numbers and wording, and seeing the notification clear
  after review. User-reported live acceptance; no report/customer details copied
  into Git. Device/OS and exact report identifier were not supplied. Baseline live
  revision was ui-16d0905 when engineering inspected it; do not invent a device or
  treat that metadata as a separately observed recording of the user's session.

This closes the incident-generation/in-app notification/review-clear scenario.
Microphone denial/revocation/offline behavior, duplicates, signature/PDF appearance,
provider media/billing/SMS and remaining source/retention/recovery acceptance are
independent checks; the successful scenario does not silently close them.

## Three operational follow-ups

Track actual completion and evidence in OPERATIONAL_FOLLOWUPS_20261022.md and the
prelaunch checklists. Use this ledger to avoid repeating unrelated feature suites
for notification routing, unchanged-image secret pinning or a scoped IAM repair.
