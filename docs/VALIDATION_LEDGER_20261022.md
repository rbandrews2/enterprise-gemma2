# Validation ledger — reuse passing evidence

## Managed onboarding — October23

- [x] Admin-created username/password accounts; optional invitations; first-login
  password change; admin/member and seat/isolation enforcement. Deployed7a674b3.
- [x]937PostgreSQL/181Node checks, zero skips; schema/config/public/auth boundary
  acceptance. Reuse evidence in MANAGED_ONBOARDING_20261023.md.
- [x] Approved Google create/update runtime permissions, independent IAM readback.
- [x] Ray Enterprise25 email-bound organization creation grant, seven-day expiry;
  CSV email replacement and backup complete.
- [ ] Human acceptance: Ray creates/verifies identity and organization, then one
  employee account is created and the employee changes the initial password.
  No real employee accounts or passwords were created during automated checks.


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

October23 release supersedes earlier runtime provenance: app content b693d8b,
release tooling a1d24d1/checker72aef6b, runtime/tests unchanged between these.
Full PostgreSQL919/430.662s PASS; Node179 Windows2.082s/Linux5.487s PASS; no skips.
390px synthetic import receipt PASS; schema/backup/staged/public/traffic checks
PASS; live authenticated dashboard import dialog and roster read PASS without
production writes. Revision ui-a1d24d1 at100%, image e29aeee4..., marker
e83ce03ec082a537e4795648. Durable evidence $HOME/wzos-release-evidence-20261023;
see AVAILABLE_UPDATES_RELEASE_20261023.md. Do not add overlapping counts to older
suite totals or repeat unchanged real Voice/SMS/billing acceptance.

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
| PIN-CHECK-GUARD | Tooling-only50557db | Five focused PASS: revision marker/nonce may change; auth, asset, security directives and denial changes still fail comparison | `python -m unittest tests.test_secret_pin_guard`; actual config result in operational repair note |
| LIVE-SECRET-PINS | Same image80c3819a…, live pins-1022181839 | Numeric refs1, same runtime/image, Ready, HTML/API marker, unchanged assets/auth/security and anonymous401 PASS; prior revision retained | OPERATIONAL_FOLLOWUPS_20261022.md; private pins-result.json, pins-resume2.exit0 and independent readback |
| ALERT-ROUTING | Four existing policies, approved info@workzoneos.org | Enabled email channel; exact recipient; all policy fields except channels/provider mutation metadata unchanged on independent readback PASS | durable follow-ups channel/alerts readback and operational-final-result.json; no inbox delivery test |
| CLEANUP-GRANT | Approved app identity on single file bucket | Role exactly storage.objects.delete; exactly one additive binding; previous bindings/policy version preserved PASS | durable follow-ups role/bucket readback and operational-final-result.json; no customer-object deletion or restore test |

Sweep1 private cloud artifacts were copied into
`$HOME/wzos-prelaunch-evidence-20261022`; sweep2 into
`$HOME/wzos-sweep2-evidence-20261022`. Local evidence paths above are relative to
the owned integration checkout. Raw runtime metadata, originals and credentials
are not Git-backed. A missing temporary folder does not mean the tests need to
be repeated: first check the durable copy and recorded source/image identifiers.
The durable sweep1 folder now also contains `validation-index.json`: raw log
SHA256, named Python cases, outcomes and reported suite totals. Full-gate891 and
affected119 cases reconcile with their summaries. Node174 and restore markers
are indexed as their own artifact types, not invented Python test cases.

## Failures repaired — retain history

| Original result | Cause / resolution | Replacement evidence |
| --- | --- | --- |
| Node174:172pass/2fail | Fake DOM lacked real element `dataset`; fixture repaired | Node174PASS |
| PG890:889pass/1error/0skip | Synthetic demo attempted now-forbidden Core messaging; demo corrected | PG891PASS at8d29bbf |
| Python advisory audit:30 findings in3 packages | Updated certifi, Pillow, pypdf; no advisory reproducer executed | 119 affected PASS and advisory exit0 |
| Local dependency checks93:69pass/23skip/1 import error | No local PG configured; test_source_package required tests on PYTHONPATH | Corrected source-package2PASS; cloud119PASS/0skip |
| Initial pip-audit invocation error | Unsupported flag combination, invocation corrected | Actual audit artifacts and repaired scan retained |
| Policy Troubleshooter unavailable | API disabled; not enabled during read-only audit | Not a passing effective-permission check; remains a limitation |
| Initial secret-pin cutover rolled back | Tooling incorrectly expected version marker unchanged; app intentionally includes K_REVISION. Corrected comparison preserves asset/auth/security checks | Three focused guard tests PASS; resume reuses the same staged candidate, no rebuild or broad rerun. Keep original pins.exit1 and rollback receipts. |
| First pin resume rolled back | CSP hash included a per-response Maps nonce. Recorded diff showed only marker/nonce hash changes; auth/assets unchanged. Normalize only nonce bytes, preserving directives, and validate stable baseline before routing | Five focused guard tests PASS. Archived resume-attempt1-evidence preserves receipts; later resume uses the same candidate. |

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

### Subsequent employee-import development (not deployed)

- EMPLOYEE-IMPORT-LOCAL:8new import backend checks +8existing employee cases =
  16unique PASS, zero skips. Initial7new cases repeated once in the15case combined
  run; count coverage once. Core/pagination extension passed separately.
- ACCOUNT-UI-IMPORT-COMPAT:26existing Node checks PASS; no account provisioning,
  SMS, Speech, model or payment calls. Changed scripts syntax accepted.
- IMPORT-BROWSER: synthetic three-row review ->2ready/1duplicate -> checkbox
  enables confirmation ->2imported/1skipped visible receipt. Private screenshot
  .local-data/employee-import-browser.png. Final mobile and PostgreSQL release
  acceptance remain open; see EMPLOYEE_IMPORT_20261022.md for provenance/limits.

Track actual completion and evidence in OPERATIONAL_FOLLOWUPS_20261022.md and the
prelaunch checklists. Use this ledger to avoid repeating unrelated feature suites
for notification routing, unchanged-image secret pinning or a scoped IAM repair.
