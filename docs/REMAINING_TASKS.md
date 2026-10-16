## Current next gates - October16

- PAUSED at user request for computer refresh. Checkout is connected in source,
  default disabled, not deployed. Resume from docs/CHECKOUT_RUNTIME_INTEGRATION_20261016.md:
  complete exact PostgreSQL/integrated/provider/browser checks, bind existing key
  plus webhook/encryption secrets, build/review image, then reviewed activation.
  Source Python34 passed/34 PG skipped; final targeted3 passed; Node26 passed.

- Stripe tax: Ray approved SaaS business-use txcd_10103001 for only the two V2
  products, plus immediate collection using the existing Virginia registration
  without filing services. Both live changes remain PENDING after browser loss.
  Actual Tax dashboard showed zero collecting locations. Complete changes/readback
  and controlled tax calculation before enabling automatic tax. Local purchase19
  and official SDK/preflight6 passed; recurring lifecycle/upgrade gates remain open.

- Complete candidate UI browser checks for both roles/editions and phone/desktop;
  Node119 passed. Keep Guided Workspace B scoped to landing. Review tools appear
  only on Enterprise desktop. Core upgrade nudges are admin-only.
- V2 live Stripe catalog CREATED: two products, six prices, USD20 once upgrade
  coupon restricted to Enterprise. Three price-contract checks PASS. Details:
  docs/V2_PRICING_ACTIVATION_20261016.md. Production checkout is NOT enabled.
- Connect secure Stripe runtime/webhook credentials, verify subscription lifecycle,
  server-owned organization mapping, once-only Core credit eligibility, paid
  activation and seat synchronization before enabling customer payment buttons.
  Review tax obligations/registrations; do not infer tax setup from price previews.
- Re-run exact final candidate PostgreSQL/build gates; retain cloud persistence29
  and696-test old-source evidence as scoped evidence, not new-candidate acceptance.
- Stage a security-capable fallback and candidate without traffic, verify identity,
  secrets/ingress/config preservation and backup/schema compatibility; only then
  cut over and validate deployed browser flows. No deployment made in pricing pass.
- Restore and evaluate actual private31B Atlas inference with bounded runtime and
  existing dedicated resources; app currently disabled and legacy model not Ready.

## Corrected live security workflow29 PASS - October16

Ray approved corrected-image single live retest. Image4d90f2dde45188afddc4cec5256fcb3a8c16bbcd53c5466073127b616c18927d
ran once as wzos-security-workflow-4hmlc; succeeded tasks1/failed0, job.exit0.
SECURITY_WORKFLOW_PASS explicitly reports mode=live, identity=Google metadata,
passed29. Actual private scanner detected the intact fixture; blocked admin download
and publication, denied infected release, and enforced member/cross-org boundaries.
Clean upload/quarantine/injected outage/recovery/notification/audit checks passed.
No mocks substitute for clean/detection scans; outage remains explicitly injected.
Cleanup WORKFLOW_JOB_REMOVED; independent jobs-after-live-retest.json confirms
WORKFLOW_JOBS_REMAINING0. Approval consumed; no job or new IAM grant remains.
Evidence pointer $HOME/wzos-fixture-workflow-latest.txt: live-retest/ configuration,
execution.json, logs.json, job.exit/removal log; live-retest-launch.log and independent
jobs-after-live-retest.json. See docs/SECURITY_FIXTURE_REPAIR_20261016.md.
No public app/schema/traffic/customer sends. This accepts Google metadata/private
scanner plus in-process app control flow with temporary SQLite/local files, not
full deployed Firebase/browser/CloudSQL/GoogleStorage workflow acceptance. Next
complete those persisted-deployment/rollback gates and remaining five HIGH OS
findings assessment before public security activation. Test image is never a web
service release. Existing695 PostgreSQL/108 Node evidence remains unchanged.
## Corrected immutable workflow image ready - October16

Build453c0c18-30b8-476d-915d-3f1763bb7647 SUCCESS. Corrected test-only image
4d90f2dde45188afddc4cec5256fcb3a8c16bbcd53c5466073127b616c18927d;
29 checks PASS against real local ClamAV plus29 mocked checks inside image.
Source9ffb411; no product/dependency/production/IAM changes. Evidence pointer
$HOME/wzos-fixture-workflow-latest.txt includes build-final.json,image.txt and
corrected run_security_workflow_job.sh (requires29 live checks).
Next request one new scoped app-identity live retest, same300s/task1/retries0/
1CPU/512MiB limits and immediate cleanup. No new job launched; approval pending.
See docs/SECURITY_FIXTURE_REPAIR_20261016.md for exact scope and acceptance limits.
## Corrected workflow29 real-engine checks PASS - October16

Source9ffb411 replaces invalid PDF-wrapped EICAR with intact standard fixture in
supported Forms Hub DOCX upload.29 mocked checks PASS;29 real local-engine app
checks PASS with ClamAV1.5.4/28155, injected app identities, temporary SQLite/files.
Detection, admin download423, publication409, release409, member/unrelated-org404
and other-org incident isolation now complete. Existing work-order member423,
quarantine/recovery/audit checks remain. Engine stopped; gate exit0; peak999216KiB.
No production source/schema/IAM/traffic/customer sends changed. No full deployed
Google authentication/storage acceptance claim. See docs/SECURITY_FIXTURE_REPAIR_20261016.md.
Cloud evidence pointer $HOME/wzos-fixture-workflow-latest.txt. Test-only image
build453c0c18-30b8-476d-915d-3f1763bb7647 submitted; verify final status/digest
before approval for new live29-check job. Prior live execution approval consumed.
Do not silently rerun old image or attach app identity without new scoped approval.
## Fixture classification diagnosed - October 16

Isolated native engine comparison d7b6ab4 PASS, exit0: ClamAV1.5.4/28155 classified
raw68-byte EICAR infected, workflow's PDF-wrapped bytes clean, intact EICAR inside
OOXML archive infected. Benign clean, expanded-limit/missing-engine error; daemon
stopped. Evidence pointer $HOME/wzos-fixture-diagnosis-latest.txt. The PDF-prefix
violates EICAR's standard test format; mocked substring matching masked this
invalid expectation. See docs/SCANNER_FIXTURE_DIAGNOSIS_20261016.md.
No new Cloud Run job, IAM/production change or customer sends. This comparison is
not an exact earlier live-instance/signature replay. Next correct the synthetic
workflow fixture using a supported document-container upload, log bounded status
on failures, and validate locally before a separately approved live retest. Do not
weaken scanner/hold policy or mark full workflow accepted. Existing application
695 PostgreSQL/108 Node passes remain applicable; no product source changed.
## Repaired live retest executed; detection gate remains blocked - October 16

CLI sign-in confirmed admin@workzoneos.org / enterprise-gemma2. The previously
approved exact fb0ef792 test-only image ran once with helper646e5fc; no new grant,
secret binding, public application/schema/traffic change or customer sends.
Configuration limits verified. Result: job.exit1, SECURITY_WORKFLOW_FAILED
real_eicar_upload_detected. By sequential fail-fast harness order, the preceding
22 checks passed, including real clean upload, metadata authentication, quarantine,
injected outage hold, persisted admin notification, clean rescan, explicit release
and recovery audit. The final infected-download/release and other-org incident
checks were not reached; do not claim26 PASS or full workflow acceptance.
The earlier cold-start failure is overcome: scanner HTTP200 at33.109808744s,
then two200 responses at0.040019855s/0.044259224s. HTTP status is not an engine
verdict. The harness does not log the failed fixture's actual classification;
clean versus held/error cannot be inferred. Its fixture wraps the standard test
string in PDF-looking bytes, unlike the engine gate's raw standard fixture.
Next compare these fixtures against the same engine/signatures and collect only
non-sensitive classification diagnostics. Do not weaken malware assertions or
claim malware detection failure cause until established. No automatic rerun:
the single repaired live execution approval is consumed.
Cleanup helper reported WORKFLOW_JOB_REMOVED; independent jobs list confirmed
WORKFLOW_JOBS_REMAINING0. Private evidence under the existing home release pointer:
live-workflow-cold-retest/, live-workflow-cold-retest-launch.log,
jobs-after-cold-retest.json, scanner-cold-retest-logs.json and
live-workflow-cold-retest-all-logs.json. Existing695 PostgreSQL/108 Node results
remain applicable; no product source change or redundant suite/build.
Remaining five HIGH OS findings and full deployed Firebase/CloudSQL/Storage/browser
acceptance remain separate gates. Public release remains unchanged.
## Approved repaired retest waiting on CLI sign-in - October16

Ray explicitly approved one repaired-image live retest (fb0ef792) with the same
300s/task1/1CPU/512MiB/retries0 limits and immediate cleanup. Approval is UNUSED:
no job launched. Fresh Cloud Shell reconnected/provisioned configcloudshell-298;
projectenterprise-gemma2, but account unset/auth list empty. Read-only projects
describe rejected no active account. Started standard gcloud auth login refresh;
complete Google sign-in before any mutation. Do not ask for another job permission
unless scope changes. Never request passwords/tokens in chat.
Preserved home pointer, repaired helper, exact build metadata and695-test exit0
were verified present. No live-workflow-cold-retest-launch.log exists; don't infer
an execution from submitting the guarded command. Next finish CLI authentication,
verify admin@workzoneos.org/project, then use the already-approved exact fb0ef792
retest once and verify cleanup. No public app/schema/IAM changes made.

## Live workflow failure repaired; retest ready - October15

Approved actual live workflow failed real_clean_upload; job removed and independent
jobs list[]. Earlier first creation stopped before execution on JSON timeout string;
helper646e5fc repaired it without changing300s. Scanner request logged HTTP200 at
31.7595s, exceeding old30s caller read wait; response body unavailable, no clean verdict
claim. Full workflow remains unaccepted. No public app/schema/IAM changes.
Sourcee9ad09a extends bounded read65s/acceptance70s for existing60s scanner limit,
retains5s connect/metadata, no retries/fallback and all integrity/identity/hold gates.
695 PostgreSQL PASS in262.617s, zero failures/errors/skips. Buildace779fe SUCCESS;
26 mocked checks PASS in repaired test-only imagefb0ef7929cda0530ffad9c03b367c50565731a310e56db7541fb61837d1327ad.
See docs/SECURITY_COLD_START_REPAIR_20261015.md for exact digest/evidence/new proposed
single300s job with existing app identity. Fresh action-time approval required for
new image/workload execution. Do not use failed old image or silently treat mock aslive.

## Findings assessment and workflow harness prepared - October15

Remaining five HIGH findings assessed and retained with bounded applicability
statements; unresolved zlib vendor classification is NOT suppressed. See
 docs/SECURITY_WORKFLOW_ACCEPTANCE_20261015.md for exact evidence and limitations.
Synthetic account workflow26 checks PASS in Cloud Shell and immutable test image
53b5189b78f9d766c42b83bdc6025a72159a727fa0f9295292e2165231bab0ec;
build09622ebb-2e0e-4b48-9a85-204b14e8c177 SUCCESS. Mock scanner and injected
identities mean this is NOT live scanner/metadata-token or deployed-app acceptance.
No product application edits. Next approve/create one disposable wzos-security-workflow
Cloud Run job (300s,1CPU/512MiB,retries0) using existing app service account;
no secrets, SQL/bucket configuration or public endpoint. Remove job immediately.
Attaching existing app identity to a new workload requires action-time approval.
Full jobs list empty at preparation; no job, new grant or deployment made.
Public site/schema remain unchanged. Current working branch codex/preproduction-modules.

## Repaired application scan completed - October15

Exact imageef31216bc772a0233b7c59a9e219dcd9b17f6c6f2c8ed058270a9a009676ab9d:
review7c7076f5-e5a9-4443-a502-40e633b3ad7d SUCCESS/review.exit0. Findings67:
critical0/high5/medium1/low36/minimal25; fixAvailable0, pip findings[]. All six
bundled-installer findings removed. Not a blanket security clearance.
Approved original-expiry grant removed immediately; independent IAM binding query[].
No grant extension. Offline exact-image inventory4b7b05b3 SUCCESS: uid10001,
ensurepip absent, activepip26.2.1, Perl Archive::Tar absent, ACL/attr commands absent,
ACL/attr libraries remain, linked zlib1.3.1. High applicability review remains open.
Detailed evidence and next gates: docs/APPLICATION_IMAGE_REVIEW_20261015.md.
No live app/schema/traffic/DNS change or customer sends. Next finish OS-finding
assessment, then actual app metadata-token/upload-hold-recovery acceptance before
cutover. Existing694 PostgreSQL/108 Node results preserved, not redundantly rerun.

## Bundled-installer repair image built - October15

Builded80918c-ca2d-48d1-921f-8dafab07ab29 SUCCESS, sourceab30279.
Repaired immutable image:
`us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:ef31216bc772a0233b7c59a9e219dcd9b17f6c6f2c8ed058270a9a009676ab9d`
Build required3.6KB context; parent73e47d4d preserved. Build assertions passed:
active pip26.2.1/dependency consistency, ensurepip absent, source-library verification,
uid10001 and existing synthetic HTTP/admin/member/origin checks. Application source
still4380849;694 PostgreSQL and108 Node regression evidence unchanged/applicable.
This does NOT establish vulnerability removal until the repaired image is scanned.

Prior review grant independently removed. Proposed re-review: SAME four-permission
role/Cloud Build identity and original condition ending2026-10-16T00:26:17Z,
not a fresh one-hour extension. Scan only repaired digestef31216b, same estimated
0.35USD review before allowances/storage; remove exact binding immediately afterward.
Changing the reviewed target requires action-time confirmation before reapplying
access. Use existing condition.txt as helper second argument; never silently extend
expiry if fewer than20minutes remain. High-five OS applicability dispositions,
actual runtime-token/full upload/hold/release acceptance and deployment stay open.
No public app/schema/traffic/DNS change. All evidence under existing app-release pointer.

## Application review completed; bundled-installer repair - October15

Ray approved the new one-hour application review window. Build7547db29-2ba3-40eb-
a792-c067752aff5e SUCCESS/review.exit0 on image73e47d4d. Findings73: HIGH5,
CRITICAL0, MEDIUM6, LOW37, MINIMAL25. Six fixAvailable findings all identify
bundled pip25.0.1: CVE-2026-1703/8643/6357/3219/13346 and CVE-2025-8869.
Temporary conditional grant expired no later than2026-10-16T00:26:17Z; harness
removed it immediately. Independent project IAM query returned
REMAINING_SCAN_BINDINGS[]. No grant remains for another review.

High findings: CVE-2026-54369/54370 acl2.3.2-2; CVE-2026-54371
attr1:2.5.2-3; CVE-2026-9538 perl5.40.1-6+deb13u1; CVE-2026-85091
zlib1:1.3.dfsg+really1.3.1-1. None has fixAvailable in Google's report.
Debian tracker pages for all five were read October15. ACL/attr relate to local
pathname/symlink operations, Perl to Archive::Tar allocation, zlib to gz* stalled
writes. These are NOT blanket false-positive dispositions: actual installed
commands/modules, linked versions and app call paths still require evidence.
References: https://security-tracker.debian.org/tracker/CVE-2026-54369
https://security-tracker.debian.org/tracker/CVE-2026-54370
https://security-tracker.debian.org/tracker/CVE-2026-54371
https://security-tracker.debian.org/tracker/CVE-2026-9538
https://security-tracker.debian.org/tracker/CVE-2026-85091

Reuse the prior hub repair approach: remove only ensurepip's obsolete bundled
installer while preserving active audited pip26.2.1. Source Dockerfile.accounts
now does so for fresh builds. Dockerfile.accounts-runtime-repair pins exact
image73e47d4d, preserves app/dependencies/source snapshot, and runs pip consistency,
ensurepip absence, full source verification and synthetic HTTP/role/origin checks
via existing check_hub_image.py as unprivileged uid10001. Tiny build context avoids
re-uploading sources. Repaired image/build outcome and re-scan remain pending;
old image is blocked by six fixAvailable findings. No production deployment.
Live configuration privately saved in release evidence/live-app-before-review.json:
hub-5a3ac86 still100%; internal-and-cloud-load-balancing ingress retained.

## Application image ready for review - October15, 2026

Application source4380849471d813c3d093efdb0ad7949b2e62058c passed694 PostgreSQL
 tests in256.275s: failures0/errors0/skipped0; postgres.exit0. Existing108 Node
passes remain applicable: subsequent changes are packaging/docs only.
Fresh Cloud SQL backup1792105746846 on wzos-v2-staging-db is SUCCESSFUL,
ended2026-10-15T23:10:17.968Z. No schema writes or public deployment performed.

Build3737a11b-ccb0-4415-b506-1851fa8c6e7b SUCCESS, us-central1:
`us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:73e47d4d7318aac95b3d0f6eb65687e512bbadbee63777719b322b2ae435622d`
Reused completed GCS archive1792105532.316336-0c4a493bf6c8412a839b0176cbd494ae.tgz;
no duplicate149MiB upload. First buildf658e24c failed because snapshot verifier
was root-owned mode600. Config543ddc8 repairs only COPY ownership for that helper;
final image source-library verification succeeded. Optional source-image reuse
path is committed but not cloud-tested or used by this build.
Cloud evidence: $HOME/wzos-security-app-release-latest.txt points to
/home/admin_/wzos-security-app-release.P6EZHXKM (postgres.log/exit,
repaired-build.json, backup-operation.json). Cloud Shell identity/project verified
admin@workzoneos.org / enterprise-gemma2. Billing October1-15 net23.51USD;
October forecast49.07USD is an estimate, not a cap.

### Proposed application-image review permission window

Approval pending: bind existing four-permission wzosImageReview role to existing
Cloud Build identity910004733138-compute@developer.gserviceaccount.com for at most
one hour, using scripts/review_scanner_with_temporary_access.sh with
WZOS_IMAGE_REVIEW_IMAGE set to the exact application digest above. Previous
scanner-review grants were removed; those approvals do not authorize this window.
Permissions: ondemandscanning.scans.analyzePackages, listVulnerabilities,
ondemandscanning.operations.get and wait. No database/storage/secret/app-user
permissions. Project-level scope also applies to other workloads using that
identity during the window. Expected scan0.26USD plus at most0.09USD build compute
before allowances/storage. Remove exact conditional binding immediately after
review (including failure); expiry is a backstop. Independently verify removal.
No public cutover is included in this permission request.

Next: obtain action-time approval, scan exact application image and review findings;
then validate app-runtime metadata-token authentication and complete synthetic
upload/hold/admin-alert/rescan/release with tenant/member boundaries. Startup DDL
is additive but deployment applies it. Preserve security holds/audits on rollback;
old public hub is unsafe as rollback after held files exist. Atlas31B inference,
Daily two-device media acceptance and production purchase flow remain unfinished.

## Billing verified; release preparation resumed - October15

Google Billing Projects - this month report directly read for enterprise-gemma2:
October1-15 usage$25.06, other savings-$1.55, net$23.51. Google forecast for
October1-31 is$49.07, an estimate not an invoice or spending cap. Initial live-cost
view excluded savings; do not confuse its approx$25.1 subtotal with net cost.
Report grouped by Project explicitly showed enterprise-gemma2/910004733138.
No current billing/auth blocker remains. No billing settings or payments changed.

Cloud Shell showed lost connection; Reconnect is provisioning its machine.
Verify active account/project/config before any commands in the resumed terminal.
Preserved home evidence must be checked, not assumed to imply a process survived.
Next verify source snapshot, build immutable security-capable app candidate,
review migration/rollback and app-runtime upload/hold/rescan/release acceptance.
Private scanner principal tests/schema/backup gates below remain historical
accepted evidence; refresh release-relevant state before applying changes.

## Latest release blocker - October15 evening

Authenticated private scanner pilot and read-only schema gate are accepted below.
Google Billing sign-in completed, but Reports showed Failed to load; one Retry
started loading, then browser control timed out and reset. No current cost figure
was obtained. Do not ask for another password or treat historical spend as current.
Next recover the existing billing report/Cloud Shell browser session and read
project-filtered current spending, then continue the security-capable app candidate
and full upload/hold/recovery integration checks. Temporary identity grant already
removed/verified; no SQL proxy remains. Private scanner min0/max1 remains ready;
public application/DNS/schema unchanged. No new approval needed to repeat these
read-only checks; any new identity-token grant window needs its own approval.

## Authenticated scanner pilot PASS; live schema compatible - October15

Ray explicitly approved the temporary ID-token test. Narrow SA-scoped
roles/iam.serviceAccountOpenIdTokenCreator grant to admin@workzoneos.org was
conditional until2026-10-15T22:33:15Z. Single synthetic run PASS, test.exit0:
anonymous403; app-principal clean200/clean; EICAR200/infected; altered hash400.
UUID/hash/byte-count response traceability validated. Identity token remained
in process memory only. Grant removed immediately; independent SA IAM read[].
This validates an operator-minted app-principal token, NOT the production app's
metadata-token path or complete browser upload/hold/rescan/release workflow.

Read-only live schema check: compatible_existing_columns=True, conflicts[].
Missing:security_incidents/security_actions/security_file_states/security_alert_reads
(additive reviewed startup migration). Also purchase_requests/purchase_events,
which belong to explicitly instantiated sandbox commerce; not automatic checkout
activation. Owned temporary localhost5544 SQL proxy stopped; process check empty.
Latest backup1792044000000 SUCCESSFUL,2026-10-15T08:48:21.194Z. No schema writes.

Next gate: current billing report. Opened Google Billing; Google requires account
verification for admin@workzoneos.org. User sign-in request pending; no password
requested in chat. Do not claim current spend verified from historic estimates.
Then finish lower-severity disposition, prepare security-capable app candidate,
verify retained source library/config, and test authenticated upload/hold/recovery
through existing ingress before production cutover. Public app still unchanged.
Atlas security UI wording is committed and Node108/108 passed, not live yet.

Cloud evidence:~/wzos-scanner-patched-latest.txt/identity-test/{acceptance.json,
launch.log,condition.txt,removal.log,test.exit}; live-schema.json/schema.log,
schema-proxy.log. Private scanner remains Ready min0/max1, app-only invocation.
Atlas model service remains absent; retained31B weights integrity already verified.

## Private scanner ready; Atlas security wording saved - October15

Approved private synthetic pilot is deployed as wzos-v2-scanner-00002-sj2,
Ready=True, origin https://wzos-v2-scanner-udtvm4rgca-uc.a.run.app.
Dedicated scanner identity has no project roles; only WZOS app principal has
service-scoped run.invoker. No public callers. min0/max1,1CPU/4GiB,concurrency1.
Anonymous real /scan403 confirmed. Public app configuration remains unchanged.

Authenticated pilot blocked before file transmission: Google IAMCredentials
confirmed IAM_PERMISSION_DENIED for iam.serviceAccounts.getOpenIdToken on the
app identity, not expired sign-in. Direct ID-token validator avoids broader
access-token impersonation permission. Requested action-time approval for only
roles/iam.serviceAccountOpenIdTokenCreator to user:admin@workzoneos.org on the
single WZOS app service account, expiry15min and immediate removal after test.
No grant yet. Do not claim app-principal detection/traceability accepted.

User requests all user-facing security/scanning credit Atlas. Implemented in
attachment and admin security messages, preserving truthful pending/unavailable/
clean status. Sourcefc85382, not publicly deployed. Full Node108/108 PASS,
focused Python5/5 PASS; no new app Python/schema changes. Full prior689 DB suite
not rerun for text/helpers. Scanner engine/lifecycle/vulnerability gates and
Atlas weight checks remain accepted as recorded below.

Next: approved short-lived ID-token test if granted, clean/detection/integrity
requests, remove/verify grant. Then remaining lower-severity applicability review,
current cost/schema/backup, security-capable app candidate and held-file workflow.
Atlas private inference remains absent; verified weights ready for its next trial.
Cloud pointer~/wzos-scanner-patched-latest.txt; details in
SCANNER_PATCH_ACCEPTANCE_20261015.md. Progress pushed to integration branch.

## Scanner repaired and cloud-tested; Atlas weights verified - October15

Patched isolated scanner built from official pinned Ubuntu26.04, supported
security updates, ClamAV>=1.5.4, mandatory vendor certificates and removed pip.
Build40db26b2-9f1b-4f98-8742-348accc66b22 SUCCESS; immutable digest
6190d698438aff6ab92ea9e8de8acce9f9149cd1e94c7e374ab5e0a95903da16.
Container gate33a26700-bbaa-4460-adea-8db133da5e23 SUCCESS. ClamAV1.5.4/28154,
Python3.14.4, nonroot10001, no pip, clean/EICAR/ZIP limit/identity/expiry/
recycle/shutdown/network/certificate tests PASS. Both starts24s, steady1.116GiB.

Vulnerability reviewfd9f372c-a40b-43ea-86ac-7330efba06e9 SUCCESS, exit0:
HIGH0/CRITICAL0/MEDIUM92/LOW3/MINIMAL1; available fixes0. Old18HIGH and six
pip fixes resolved. Remaining medium/low applicability review still OPEN;
zero HIGH does not mean malware-proof or production accepted. The newly approved
scan-only IAM window was removed and independently verified absent ([]).

Atlas read-only inventory: all10 retained objects/62,578,670,545 bytes match
Google source CRC32C and size. Generations preserved in cloud evidence. No
weight redownload/GPU wakeup. Existing dedicated identity/subnet present,PGAtrue.
Live model service still absent. HF_TOKEN valid for31B; no runtime access granted.
Five focused local verifier/HF tests PASS using bundled Python. No app source
changes; accepted application regression689/108 unchanged, not rerun for packaging.

Detailed evidence:docs/SCANNER_PATCH_ACCEPTANCE_20261015.md;
Cloud Shell pointer:~/wzos-scanner-patched-latest.txt (gate/review logs,findings,
atlas-artifacts.json). Next: lower-severity disposition and narrowly scoped private
scanner pilot approval (dedicated identity with no project data roles, app-only
service invoker, min0/max1,synthetic files). Then app identity/upload holds,
schema/backup/current-cost gates and security-capable app cutover. Atlas next:
reuse verified weights for bounded private live inference under cleanup guard.
LandingB integration remains separate. Production unchanged throughout repair.

## HF_TOKEN verified; scanner vulnerability gate blocked - October 15, 2026

Canonical secret HF_TOKEN version1 enabled. Live operator check: identity200,
selected google/gemma-4-31B-it repository access200, fineGrained token. No secret
value displayed or persisted. See HUGGINGFACE_GEMMA_ACCESS_20261015.md.
Failed gemma-inference-00007-njh loaded old google/gemma-2-2b-it and failed
GatedRepoError401 before listening8080; that model returned403 with this token.
Do not broaden token or restart wrong model. Existing Atlas helper uses Google
Storage weights, not HF. Live inference still unaccepted; bind HF_TOKEN only to
an actual HF consumer after narrowly scoped access review.

Completed analysis build27c1de4f-7011-45ff-b6b9-48c0fb3b90f4, scan
projects/enterprise-gemma2/locations/us/scans/eb138154-f833-40b8-bb35-893d3f4b217a.
Build FAILURE was formatting-only (python3 alias absent); findings retrieved
using existing operator access without another scan. Counts:162 total, HIGH18,
MEDIUM8, LOW84, MINIMAL52, CRITICAL0. Six fixAvailable, all pip25.0.1 with highest
reported patched version26.2. High packages:clamav12, acl2, cyrus-sasl2/attr/zlib/
perl one each. Debian trixie ClamAV1.4.3 has relevant parser vulnerabilities.
Image99019f1 is NOT cleared for activation despite functional acceptance.

Approved four-permission scan-only binding was removed automatically and absence
independently verified (IAM result[]). Original expiry2026-10-15T22:24:39Z was
not extended. Custom role remains unbound. No runtime grants/service/deploy made.
Cloud evidence pointer:~/wzos-approved-image-review-retry-latest.txt includes
findings.json,hf-check-result.json,access-removal/launch logs. Earlier pointer
~/wzos-approved-image-review-latest.txt includes redacted Gemma startup diagnosis.

Next: patched supported scanner engine/base and resolve/remove vulnerable build
tooling; immutable rebuild,lifecycle tests,new vulnerability disposition. Do not
mix unstable packages into stable or waive parser risks. New scan IAM window
requires new approval. Then dedicated runtime/invoker approval, live identity/
upload/hold tests,schema/current costs,security-capable rollback and cutover.
Atlas next: selected immutable weights/serving path and real inference acceptance.
CLI formatter now selects SDK bundled interpreter; new config not cloud-rerun.
Existing app gate689/108 unchanged; earlier two focused HF helper tests passed.
Local rerun unavailable:python command currently resolves Windows Store alias.
LandingB remains prototype-only. Production traffic unchanged.

## Vulnerability extraction repaired; temporary scan permission approval needed - October15

Requested local retry timed out180s/exit124. Cloud job missing-component and
package-repository issues repaired with Google's COMPONENTS installer/default
entrypoint and pinned official CLI digest. Buildca2222cf-59ba-4cf2-8084-71544fa84f93
COMPLETED package extraction, then failed only on IAM
ondemandscanning.scans.analyzePackages for existing build identity
910004733138-compute@developer.gserviceaccount.com. No findings/scan acceptance.

Prepared scanner-image-review-role.yaml (four scan-only permissions) and exact
one-hour conditional grant/rollback in docs/SECURITY_CUTOVER_20261015.md.
User approval required before applying; no grant made. Cloud scanner runtime still
not activated. Local review clients stopped; uploaded contexts cleaned by verified
/tmp/wzos-scanner-review.* prefix. Gate689/108 and real scanner container gatePASS
are unchanged. Next: approve/apply temporary custom scan role, rerun exact-image
review and remove matching binding; then resolve findings before scanner/live
identity/schema/cost/cutover gates. No production traffic or data changes.

## Cloud scanner acceptance PASS; cutover plan prepared - October 15, 2026

Cloud Build gatea3aac155-9a1f-433e-8c62-775f2aea21b6 SUCCESS, explicitly read
SCANNER_IMAGE_GATE_PASS and image.exit0. Harness629f10b tested immutable scanner
image99019f10204758114bc54cf987c4db1a7d881b693cd7d67083f4d346679adb8e, source2cd5485.
Clean/EICAR/expanded-limit ZIP/missing-identity/expiry/recycle/shutdown passed;
network/certificate failures prevented readiness. Boot24s/23s; steady1.108GiB,
limit4GiB; non-root10001; no OOM. Actual Debian engine1.4.3/28154, not prior native1.5.4.
Only3 harness files6.9KiB uploaded; no customer/private files or credentials.
Cloud Shell Docker pull was blocked; cloud-native test resolved that blocker.

Live app verified100% wzos-v2-accounts-hub-5a3ac86; immutable imagefc87869680a0c6948d4116225ddf7ae22de6a659d0264e31351a251367465f06.
SQL RUNNABLE, backup1792044000000 SUCCESSFUL (2026-10-15T08:48:21.194Z).
No runtime, traffic, DNS or IAM changes made. App source/tests identical to accepted
503dfc3 (689 Python/PostgreSQL +108 Node, zero failures/errors/skips).

Prepared docs/SECURITY_CUTOVER_20261015.md: exact artifacts, evidence, identity and
resource proposal, startup DDL review, bounded rollout and rollback stop conditions.
Reviewable startup SQL scripts/security_schema_review.sql; no destructive migration.
Do NOT rollback to old hub after security holds exist: it predates enforcement.
Preserve mandatory scan gate/holds/audit in any post-activation rollback.

Vulnerability CLI stalled on local package extraction; verified owned PID27402
and stopped it with TERM, terminal returned Failed/prompt; no findings obtained.
Use a bounded cloud-native review job, not another slow local image extraction.

Next: image vulnerability disposition/current billing; exact approval for new
private scanner service/dedicated identity and service-scoped invoker grant;
live Google identity/cold-start and synthetic upload-to-hold acceptance. Then
review actual live schema, build security-capable application image and validate
no-traffic candidate through existing ingress before conditional public cutover.
Selected landingB still needs actual functional integration, landing-scoped only;
prototype is saved, OptionA archived, other module pages must remain unchanged.

## Scanner image built; Cloud Shell download gate blocked - October 15, 2026

Repaired first Cloud Build failure05e320ee: non-root UID10001 could not read
root-owned mode600 Python files from the restrictive source archive. Commit
2cd54853fc1abd320f3f52145493865c9e2a2304 adds read/traverse permission to the
explicitly allowlisted public scanner code only; runtime remains non-root and
cannot modify root-owned code. No secret/IAM permissions changed.

Second Cloud Build32e7be44-f0f1-4ddf-9fab-187c15de5aad (us-central1) SUCCESS,
verified directly. Immutable image:
us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-scanner@sha256:99019f10204758114bc54cf987c4db1a7d881b693cd7d67083f4d346679adb8e
Source2cd5485. Base remains pinned official Python3.12-slim-trixie. Build success
is packaging evidence only, not service/engine acceptance or live deployment.

Cloud Shell source checkout /home/admin_/wzos-security-20261015.5LohuDMf/repo.
Image acceptance evidence /home/admin_/wzos-scanner-image-acceptance.LqMlyPDJ;
pointer $HOME/wzos-scanner-image-acceptance-latest.txt. First background attempt
exited before evidence setup; foreground traced retry passed preflight with
~5.6GB available RAM and reached immutable Artifact Registry image pull. Gate
exited124 at the five-minute Artifact Registry download timeout, before any
container started. Directly observed image.exit124, empty docker ps and cleanup
of owned /tmp/wzos-scanner-image.BMYxusG6. This is blocked download evidence,
NOT an engine/runtime test failure or acceptance. Do not repeat the same slow
Cloud Shell image pull. Next fallback: run bounded image acceptance within
Google Cloud Build, using the existing immutable image and synthetic fixtures
only; prepare its minimal source context and explicit timeout/resources first. Browser tab12 was reconnected after session
transfer; user tail command had an unmatched quote, safely completed/restored.

Full application regression remains PASS at503dfc3:689 Python/PostgreSQL and108
Node, zero failures/errors/skips. Later change is Docker packaging, helpers,
prototype and documentation only. Avoid repeating full suite without a new cause.
Landing Option B remains a saved prototype; actual functional dashboard integration
is pending and must affect LANDING ONLY. Other module pages/styles unchanged.

Next: finish actual container clean/EICAR/archive and lifecycle/failure checks;
review live identity, resources/cost and exact scanner service/IAM activation.
New scanner service/IAM still requires concrete approval. Then integrate selected
landing with real entitled navigation, validate, and prepare conditional public
site release/rollback. No live-site, DNS, IAM or customer communications changed.

## Landing B selected; supervisor regression passed; image diagnosis pending - October 15, 2026

Ray chose Option B (Guided Workspace) and explicitly limited the design change to
LANDING ONLY. Removed comparison/study header and A/B selector, preserved original
workspace size, two-tone surfaces, icons, background/blur/motion and module cards.
Other module pages/shared live styles were NOT changed. Local preview8185/index.html
shows only B; Option A and original comparison preserved in primary ignored
.local-data/landing-concepts/option-a.html and comparison-before-selection.html.
Tracked designs/landing/index.html, option-a.html, background.css, README.txt reuse
existing static assets. Actual app dashboard integration remains to do: prototype
buttons are visual only, not functional navigation. Do not imply live UI update.

Ray authorized updating app.workzoneos.org AFTER remaining applicable tests pass.
Keep rollback and migration review; no unaccepted scanner activation/new IAM grant
is authorized by that conditional release request. Preserve all module UI/behavior.

Application source503dfc32aadeaaa501b88e396b0e6d77884df0d3 full gate PASS:
Python/PostgreSQL689 (304.061s), Node108 (2.565s), failures0/errors0/skipped0,
gate.exit0 directly inspected. Evidence /home/admin_/wzos-security-20261015.rFzHkKcJ.
No /tmp/wzos-pg-gate.* or owned scanner-build temp dirs/containers remain.
Latest sourceec8f9daf68d3a4386dab49a1d280b84119756c0f only adds build helpers,
scoped landing prototype and docs; git diff confirms services/tests/Dockerfile/
requirements-scanner unchanged from accepted503dfc3.16 focused tests PASS.

First local Docker build was stopped after a stalled official Docker Hub layer
(2MiB/29.84MiB after300s). Verified owned timeoutPID13503 before TERM; no container
had started. Switched to one bounded Cloud Build in existing project/registry,
within approved development budget; no new runtime service, IAM or public exposure.
Cloud Build05e320ee-b7c1-4eaa-b9f6-ce173f0211a0 (us-central1), sourceec8f9da,
status FAILURE, USER_BUILD_STEP step0 exited1. Image NOT ACCEPTED. Do not retry
until precise log failure is read. Source archive only11 allowlisted files/56.3KiB,
no private data/credentials. Default pool e2-medium timeout900s: maximum build
compute illustration0.045USD before allowances, excluding artifact/source/log cost.
Official pricing inspected October15: https://cloud.google.com/build/pricing.

Cloud Shell has $HOME/wzos-scanner-cloud-latest-path.txt pointing to build evidence
(build.id/source.txt/base.txt/image-tag.txt). Requested gcloud builds log into that
folder/build.log, then tail24; browser control timed out and reset. Reconnect/read
first, do not assume log command ran. Read-only question to Ray is pending.
Active gcloud principal was admin@workzoneos.org/project enterprise-gemma2,
config cloudshell-1052, verified this session. No production/DNS/customer send.

Next: read build.log or gcloud builds log05e320ee..., repair actual packaging error,
finish hardened image lifecycle/engine acceptance, then live-identity/cold-start/
resource/cost review. Separately integrate selected B into actual dashboard with
scoped CSS and real existing navigation/entitlement controls; test home-to-module
roundtrips without styling changes elsewhere. Prepare exact release and rollback
before the user-authorized conditional live rollout. Do not provision scanner
service/invoker IAM until its concrete activation review/confirmation is complete.

## Scanner image/supervisor implementation, acceptance running - October 15, 2026

Browser cleanup requested by Ray: closed old in-app landing concept preview;
kept Cloud Shell tab9, left personal Chrome service tabs unchanged. Re-read Git,
contract/checkpoint/tasks; owned codex/preproduction-modules clean at48f81c1.
Fresh check: project enterprise-gemma2/config cloudshell-1052; Docker available,
~5.4GiB available memory. No credentials, IAM, cloud service or production change.

Runtime/image sourceb846dbf3d85a02fabd9eef5baded5a909c24e6c8 pushed; latest helper
503dfc32aadeaaa501b88e396b0e6d77884df0d3 only adds image-test diagnostics/timings;
application/tests/Dockerfile/dependency pins unchanged between those commits.
Prepared non-root read-only image, minimal pinned dependencies without DB/storage
SDKs, verified signature seed + bounded boot refresh, private engine socket,
readiness scan before HTTP, crash/shutdown supervision and request-driven aging
recycle. No idle background CPU assumption.16 local focused tests PASS.
Signature reserve one hour; max instance scan lifetime20h. Recycling may cause a
transient scan failure/hold; live Cloud Run cold-start/identity remain open.

Cloud Shell local Docker image build/acceptance RUNNING (not cloud provisioning).
Base official python3.12-slim-trixie manifest index sha256:
a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1,
amd64 manifest2b4f19dae3a777dfc3b76730bda1e82e1f66ab2a2686fa93ca78edbfb4f04ffe.
Read $HOME/wzos-scanner-image-latest-path.txt, build.log/launch.log/image.exit.
Do not start duplicate while active. Helper timeout1200, build timeout900;
only harmless synthetic engine checks, no customer files or cloud credentials.
Full exact503dfc3 Python/PostgreSQL689 PASS (304.061s), zero failures/errors/skips,
gate.exit0 directly inspected. Node count/result still to read from node.log.
Evidence /home/admin_/wzos-security-20261015.rFzHkKcJ;
$HOME/wzos-supervisor-regression.log; $HOME/wzos-security-latest-path.txt.
Latest helpers f359a90/ec8f9da do not change runtime/tests/dependency pins.

Next: finish image and full gates; repair concrete failures, verify owned Docker
containers/temp/database cleanup, save exact image ID/package versions/latency.
Then image vulnerability/identity/cold-start/resources/billing review before any
new private service and service-scoped invoker grant. No production activation.

## Private scanner connection regression accepted - October 15, 2026

Owned codex/preproduction-modules source2b47a750cbe4e01fd01ef9fbe19ae6776b638fa0
pushed; NOT DEPLOYED. Separate private scanner HTTP service/client prepared, with
Google audience/caller verification, pinned HTTPS run.app destination, raw bytes,
request UUID/hash/size-bound replies, bounded input/output, single-flight admission,
no redirects/retries, no token/error detail leakage, and existing quarantine/release
contracts. Disabled unless WZOS_SCANNER_URL is explicitly set. No DDL or UI changes.
No database/bucket credentials are supplied to the scanner wrapper. Actual separate
service account/IAM isolation is a deployment gate, not established by source code.

Focused local transport10 PASS; transport + SQLite quarantine11 PASS. Initial
fixture incorrectly expected explicit-quarantine behavior for an implicit pending
scan; corrected test to apply reviewed quarantine first, preserving existing policy.
Windows temporary-storage sandbox restriction required the synthetic SQLite test
outside the sandbox. No protections disabled or production settings changed.
Fresh Cloud Shell config cloudshell-1052/project enterprise-gemma2 verified;
pg_config and Node available, ~5GiB memory available. No cloud resource mutations.
Full exact2b47a75 gate PASS: Node108 (3.647s), Python/PostgreSQL683
(307.212s), failures0/errors0/skipped0, gate.exit0 directly inspected.
No /tmp/wzos-pg-gate.* directories remain after helper cleanup.
Evidence /home/admin_/wzos-security-20261015.5LohuDMf, source.txt/node.log/
postgres.log/gate.exit; launcher $HOME/wzos-private-scanner-regression.log.
Run finished; latest-path pointer references this gate. No reason to rerun
until source changes or a concrete new concern requires it.

Next: implement/accept the isolated image and signature/process supervisor described in
PRIVATE_SCANNER_TRANSPORT_20261015.md. Live Google identity, bounded boot/refresh,
stale signature behavior, engine crash/shutdown, memory/cost and rollback acceptance
remain open. New service/invoker IAM requires explicit activation approval after
concrete image/resource review. No public service, production deploy, paid resource,
secret grant, customer file transfer or messaging occurred in this increment.

## Scanner engine and full regression accepted - October 15, 2026

Owned codex/preproduction-modules runtime source7521b265253ca4252cdac7a71374661522378348,
pushed; NOT DEPLOYED. Fresh Cloud Shell project enterprise-gemma2 verified,
config cloudshell-26890. No production, IAM, credentials, customer messages or
paid resources changed. Reused official distro binaries without package installs.

Repaired CVD certificate paths for Freshclam, its database-test subprocess and
clamd while preserving vendor code-signature verification. Real-engine acceptance
then exposed clean on an over-limit ZIP member. Both CLI and daemon now enforce
an independent bounded ZIP completeness gate; incomplete/unsupported/encrypted/
nested archives stay error-held rather than being diagnosed as infected.
See CLAMD_ADAPTER_INTEGRATION_20261015.md for precise limits and remaining formats.

Cloud engine acceptance at exact7521b26 PASS, engine.exit0:
ClamAV1.5.4/28154, benign clean, harmless detection fixture infected,
expanded-file-limit error-held, missing engine error-held, daemon_stopped true.
Child peak RSS995716KiB (~973MiB); not a production sizing guarantee.
Evidence /home/admin_/wzos-security-20261015.Jzsfaok3/clamav-engine-archivefix/;
engine-archivefix-source.txt records candidate. Prior failed runs retained there.
Local focused14 PASS. Previous source3b7507e full665/108 PASS remains historical.
Final exact7521b26 Python/PostgreSQL671 PASS (288.582s), Node108 PASS
(2.350s), failures0/errors0/skipped0; gate.exit0 directly inspected.
Evidence /home/admin_/wzos-security-20261015.wh8UI1RX; launcher
/home/admin_/wzos-scanner-final-regression.log. source.txt confirms candidate.
No /tmp/wzos-pg-gate.* or /tmp/wzos-clam* directories remain; no clamd/freshclam
process remains. Latest-path pointer references final regression, not engine evidence.

Next: production scanner activation review, not another regression rerun.
Before activation: review isolated deployment, signature updater/health/restart
supervision, memory/cost, existing-file inventory/backfill and rollback holds.
Other container formats and real encrypted/macro fixture acceptance remain open.
No endpoint-device protection, infrastructure feed or SOC2 certification claim.

## Streamed scanner integration - October 15, 2026

Claude's INSTREAM approach now integrates with Google-backed Atlas Security at
runtime3b7507e, not deployed. Private Unix socket only; no Supabase/Render runtime,
new API/schema or credential. Focused13 PASS; cloud Node108 and PostgreSQL665 PASS,
zero failures/skips; database cleanup verified. Real-engine command status unknown
after two browser-control timeouts: reconnect requested; read saved engine-launch
and clamav-engine evidence before any retry. Helpers at3e4342d; runtime remains3b7507e.
Next verify actual ClamAV/fresh-signature/limit/memory/cleanup, then deployment review.
See CLAMD_ADAPTER_INTEGRATION_20261015.md and current SESSION_HANDOFF.md.

## Downloaded security kit review - October 15, 2026

Reviewed security-kit.zip from Downloads, SHA256 da19cb8a022bdc4807922c22df52658876aef3481d3177680ebae1e24b8b0bd5.
Not integrated/deployed: old Supabase/Render/Netlify architecture, tenant isolation
and admin alert delivery absent, file-type defects reproduced with harmless buffers.
Exact Supabase project metadata lacks the proposed schema/buckets; no dedicated
scanner found in the open Render workspace inventories. Netlify V1 last published
May8. No service/credential/schema/production changes. Full findings and reuse path:
CLAUDE_SECURITY_KIT_REVIEW_20261015.md. Next: real-engine acceptance through existing
Google-backed security contracts, not a second auth/storage runtime.

## Atlas Security checkpoint - October 15, 2026

Sourcec4a8b5f pushed; implemented in local working model, NOT DEPLOYED. Admin
alerts/review, file holds, trusted-count Atlas guidance, known-user denied-request
signals, audited containment/recovery and integration-key revocation now exist.
Actual scanner is not installed/activated; legacy unscanned behavior remains until
the explicit scan gate is enabled. No device/network protection claim.

Next in order:
1. Exact-source release validation COMPLETE: PostgreSQL/Python651 and Node108
   PASS, zero failures/errors/skips, exit0; disposable PostgreSQL directory absent.
   Prior prompt-size failure repaired at1572 characters; full rerun passed.
   Ray confirmed training editor collapse/expand. Real media remains open.
2. Size and validate real ClamAV scanning with fresh signatures, quarantined-file
   retention and legacy inventory backfill. Review four-table/three-index DDL and
   safe rollback before controlled deployment. Never release malware to close a case.
3. Connect approved perimeter/auth/service security signals and out-of-app admin
   alert delivery; app observations are not endpoint/device compromise detection.
4. Resume prior controlled SMS, Daily/media, Maps/navigation, Atlas inference,
   checkout/activation and connector acceptance/integration tasks below. Guided
   Workspace is the selected standalone design, not a deployed dashboard redesign.

Local tests: initial59 regressions, expanded22+final2 focused security/scanner, UI6
PASS; actual browser admin incident/reopen/resolve, member redaction and390px fit
verified. Loopback HTTP containment/tenant checks PASS. Full cloud651/108 PASS.
SESSION_HANDOFF.md has exact evidence. Scanner activation review is saved in
SECURITY_ENGINE_ACTIVATION_REVIEW_20261015.md.

## Training/SMS candidate - October 14, 2026

Source bf33fd6 pushed, not deployed. Collapsible admin video links and compact
click-to-load players implemented; queued SMS access revocation repaired in
parallel. Node102 cloud PASS directly inspected. Ray reported PostgreSQL606 PASS,
no failures/skips. Direct cloud exit/cleanup inspection and browser
visual/admin/member/mobile/playback checks remain pending controller recovery.
Read $HOME/wzos-training-20261014 saved logs before rerunning tests. Next: finish
those gates, then prepare code-only release inheriting the current OS-patched
image. No new schema/dependency/secret; preserve SMS test mode. See latest
SESSION_HANDOFF.md and TRAINING_PLAYER_UPDATE_20261014.md.

## Public hub release completed - October 14, 2026

app.workzoneos.org serves hub-5a3ac86 at100%, OS-repaired digestfc878696.
Exact source5a3ac86: PostgreSQL596/Node96 PASS; live public/auth gates PASS.
Six tables/audit index verified; fresh successful backup. Budget report USD21.79
October1-14, delayed usage may post later. Five reviewed high Debian advisories
remain without stable fixes; full disposition HUB_CONTAINER_REVIEW_20261014.md.
Deployment item below is complete; earlier not-deployed statements are historical.

Next in order:
1. Real admin/member/Core/Enterprise/mobile dashboard and shared notes/preferences
   acceptance; verify status expiry. Connect actual billing/monitoring/security
   evidence before green status claims. Remove preview-only labels behind public
   sign-in modal in focused UI polish.
2. Finish controlled one-way organization SMS and truthful verification/delivery UI.
3. File malware quarantine/scanning; audit/restore/incident/access-review evidence;
   monitor residual container advisories for stable fixes. No SOC2 certification claim.
4. Provider-specific connectors using approved OAuth/tenant/field mappings; existing
   integration API exports only scoped work-order/schedule projections.
5. Deferred Daily device media, Maps/navigation, Atlas inference, checkout/activation
   and operational acceptance. Preserve current provider restrictions until tested.

## Built release candidate — October 14, 2026

Final runtime5a3ac868085685a5e71169ceac21fa618cc405e9; Node96/PostgreSQL596 PASS,
actual image verification and package audit57/0 findings/no skips PASS. Build
1685f954-4c4f-4f0a-9729-28c36871c0c1 SUCCESS. Digest4cc2f391151e1aaf00d9ad29bc68c57779b808f75ed9034f23e3bcbb3af71bdd.
NOT DEPLOYED. Live Daily service/config/traffic verified unchanged.

Next: OS-image scan coverage, fresh SQL schema/backup/budget review and applicable
public API activation approval, then zero-traffic candidate and controlled rollout.
See HUB_ROLLOUT_REVIEW_20261014.md for exact access scope, DDL and rollback.
Do not rebuild with old650aa5a helper or deploy a source-only dependency overlay.
All subsequent acceptance/feature tasks below still apply. The new invalid-key
shared-lock hardening is covered by SQLite/PostgreSQL tests; no real keys issued.

## Latest implementation queue — October 14, 2026

Source650aa5a adds admin dashboard + security controls + scoped read-only API;
Node96/native PostgreSQL594/HTTP7 PASS; patched audit57 packages/0 findings/no skips.
No public deployment. Full evidence: ADMIN_HUB_SECURITY_API_20261014.md.

Next in order:
1. Deploy patched dependencies and new source after image-level audit, frozen-source
   preservation, backup/schema/budget review and applicable public API activation
   approval. Current public runtime still has old framework dependencies. Reusing an
   old image with source-only COPY does NOT apply security dependency patches.
2. Validate dashboard on actual admin/member devices, Core/Enterprise, account
   controls, shared preferences/notes and status evidence expiry. Connect real billing,
   monitoring and security observations before green operational-status claims.
3. Complete pending one-way WZOS SMS notifications to consenting verified organization
   members/admins; truthful verification/delivery UI and controlled carrier acceptance.
4. Add file malware quarantine/scanning and clean-result release, dependency/image
   inventory, audit retention, restore/incident/access-review evidence. Code controls
   are not SOC2 certification; privacy/vendor/process work remains.
5. Implement provider-specific integration connectors after customer/provider OAuth
   setup, tenant authorization and approved field mappings. Current API exports only
   work-order/schedule projections; it does not yet sync QuickBooks/Workday/payroll.
6. Resume existing deferred Daily media, Maps, Atlas inference, checkout/activation
   and production operations acceptance. Prior milestones below remain historical.

## Daily release checkpoint - October 14, 2026

Daily meeting integration deployed at app.workzoneos.org, revision
wzos-v2-accounts-daily-748f382,100%. Native576/Node96 PASS; real room/token/expiry
and cleanup PASS; public asset/access checks and authentication-origin checksPASS.
Ray deferred integration/device testing until a later session. Still to do:
Android/laptop audio/video, denied permissions, Leave cleanup, cancellation of an
already connected call and membership-revocation behavior. The provider API checks
are complete; those device checks remain open. Do not infer media acceptance.
See latest SESSION_HANDOFF.md and DAILY_MEETINGS_INTEGRATION_20261014.md.
Prior pending-deployment checkpoints below are historical. Other acceptance tasks
(Maps, Twilio delivery, Atlas, checkout/activation and operations) remain unchanged.

## Daily embedded meetings - local implementation, October 14, 2026

Ray selected Daily and supplied wzos.daily.co; reports key saved in Secret Manager.
Secret metadata independently verified: version1 enabled, no value read.
Candidate af83922ca06c18eb9f752b4d6da33bdadc014b0f pushed to
origin/codex/preproduction-modules. Exact disposable native database gate
started in Cloud Shell; log $HOME/wzos-daily-20261014/postgres.log.
Local implementation reuses schedule/admin/member boundaries, private server rooms
and existing TV. Full Node96 passed; focused Python20 passed/eight PG skips.
Full local Python574 passed with169 PostgreSQL skips; exact PostgreSQL gate running. No Daily runtime grant,
media acceptance or deployment yet; public00044-xim unchanged. See
DAILY_MEETINGS_INTEGRATION_20261014.md for DDL, security activation and rollback.
Next: exact database gate, scoped Daily secret/runtime activation approval, build,
then two-device call acceptance. Existing Google Meet links remain external.

## Embedded meeting engine decision — October 14, 2026

Ray authorized investigating interactive calls inside the faux TV. Compared Daily
Prebuilt, self-hosted Jitsi and LiveKit; recommend Daily for first implementation,
or self-hosted Jitsi for Google Cloud media ownership. Exact proposed security,
data flow, cost examples and tests in EMBEDDED_MEETINGS_OPTIONS_20261014.md.
Provider selection/account setup/implementation remain pending. Existing admin-only
Google Meet scheduling and external join behavior remain unchanged. No provisioning.

## Navigation and credential release checkpoint — October 14, 2026

Direct normal start/destination inputs and preserved job routing deployed00044-xim;
Map heading/under-map text cleanup/+1pt paragraphs complete. Node92 and full
PostgreSQL555 PASS/no skips; exact live assets and auth-origin/security checks pass.
Twilio credentials remain Secret Manager-only runtime references, now pinned to
audited enabled versions; test mode and voice webhook unchanged. No sends.
Next acceptance: user refresh and actual authenticated Google manual/job route
behavior, then remaining provider delivery, Atlas inference and checkout work.

## Authentication repair checkpoint — October 14, 2026

Ray confirms successful real admin sign-in, organization selection and workspace
entrance. This acceptance is complete; proceed to authenticated module/Maps checks.

Fixed missing production authentication-key referrer after Ray's explicit approval.
Live bounded provider-origin gate six checksPASS; five gate unit testsPASS.
Real admin password login/organization selection is still the next user acceptance.
Negative probes did not create accounts, reset passwords or send email. Require
scripts/check_auth_origin.py acceptance for future origin/key release changes.
See AUTH_ORIGIN_REPAIR_20261014.md. Other remaining tasks below are unchanged.

## Public V2 is live; next acceptance tasks — October 13, 2026

Completed: exact Node90/native PostgreSQL546; frozen-source build; schema compatibility;
fresh SQL backup; shared test admin retirement; public00041-pem deployment and
app.workzoneos.org routing; production origin/RP; Twilio restricted test bindings;
public root/assets200, protected401, cross-origin403 and direct run.app404 checks.

Remaining in sequence:
1. Real admin public-domain sign-in, organization selection and mobile/desktop module
   acceptance; Maps rendering and Routes response under that authenticated origin.
2. Controlled Twilio SMS delivery/status/webhook acceptance to approved recipient only;
   decide customer messaging rollout after acceptance. AIRA voice hook unchanged.
3. Restore cost-bounded self-hosted Atlas engine and run actual module/reference inference
   scenarios. Live flag remains disabled until accepted; historical trial is not live AI.
4. Finish payment activation/seat packages, real prices and recurring billing lifecycle;
   default runtime does not expose sandbox checkout. Confirm email delivery provider.
5. Resolve resulting functional/UI defects, tenant and role acceptance, monitoring,
   restore exercise and production operations documentation.

See PUBLIC_RELEASE_20261012.md, PUBLIC_ROLLBACK.md and latest SESSION_HANDOFF.md.

## Exact PostgreSQL gate accepted; Navigation map increment — October 12, 2026

Ray reports exact db60b7ef9a4c57497ba60818dc34c4e42630ab6d native PostgreSQL:
546 tests153.812s, PASS,0 failures/errors/skips. This resolves the Docker-download
block and supersedes the local timeout as the current reported database gate.
Raw Cloud log and cleanup still need independent readback before build.
Navigation now adds a visible interactive Virginia overview (explicitly not device
location), route endpoint symbols and Show full route after pan/zoom. Existing
Google loader/Routes adapter and permitted-job lookup reused; no backend/DDL change.
Client asks location only on click, and map errors/offline remain explicit.
Live origin/credentials rendering and public release remain unverified, not deployed.
## Release gate follow-up — October 12, 2026

Exact application candidate db60b7ef9a4c57497ba60818dc34c4e42630ab6d pushed and
verified on origin/codex/preproduction-modules. Node87 passed. Local Python546 ran
760.149s: one Atlas cancellation timeout,159 PostgreSQL skips; NOT a full pass.
Focused cancellation rerun5 passed19.053s; do not erase full-run failure or infer
resource causation. Exact Linux/native PostgreSQL gate remains required.
Ray reports Docker image retrieval exceeded300 seconds before gate execution.
Existing scripts/test_postgres_native.sh avoids Docker, uses private Unix socket,
mode700 disposable cluster and cleanup trap. Exact-candidate command sent to Ray.
Chrome absent initially, restored to inventory after reconnection but attaching to
Cloud Shell still timed out. No native gate/build/deployment/traffic changes verified.
Next use native runner, inspect actual outcome/cleanup, then live release checks.
## Release candidate saved — October 12, 2026

Ray requests GitHub synchronization and public V2 release. Current candidate includes
paid-seat grants, sandbox-only commerce foundation, install assets/guidance and the
approved original module layout with translucent glass/icons and account menu.
Full Node87 passed. Full local Python discovery running; initial -t discovery rejected
non-package tests, corrected to -s tests. Exact native PostgreSQL gate remains open.
Chrome Cloud Shell inventory/attachment timed out twice; no live schema, spending,
backup, credential or traffic checks verified during this attempt. No new cloud deploy.
Reviewable additive DDL: scripts/purchase_seats_schema_review.sql. Default runtime
applies only seat tables; sandbox purchase ledger is not mounted in workspace.
Resume: finish current test result, run exact native PostgreSQL candidate, check live
backup/schema/budget, retire shared synthetic admin, set app.workzoneos.org auth
origins/passkey RP and review existing IAP/backend routing, then deploy/verify/rollback.
Public request is recorded, but fixture authentication must never be published.
Live payment products/lifecycle, Atlas inference and Twilio acceptance remain open.
## Latest accepted real admin organization — October 12, 2026

Molecular Project Development LLC creation completed through approved normal endpoint;
selected admin/Enterprise entry and workspace loaded as admin@workzoneos.org.
Independent DB: exactly1 active admin membership, active Enterprise organization,
activation consumed, exactly1 organization_created audit. Private acceptance JSON in
Cloud Shell release folder; temporary SQL proxy cleaned, clipboard cleared.
Protected00039 repair remains, preview45min. Browser evidence saved ignored and tab
kept open. See ORGANIZATION_SETUP_REPAIR_20261012.md. No V1/public/IAM/customer change.
Next retire shared synthetic admin before public release; finish production origin/RP/
routing and Atlas/provider acceptance. Historical synthetic/test copy cleanup remains.
## Latest private repair release — October 12, 2026

Exactbf77c91 Node83 and PostgreSQL498 passed/no skips; PGcleanup verified.
Build2deb3159 SUCCESS; private00039-wum/repair-bf77c91 Ready, runtime config unchanged,
main00031 still100%. Preview HTML/API200, bothJS byte matches, anonymousaccount401/
publictag403. Live activation guidance accepted; company name filled. User asked to
copy existing private activation directly to app and submit. Organization/admin/
Enterprise audit acceptance pending. Do not read raw terminal if code visible.
See ORGANIZATION_SETUP_REPAIR_20261012.md. Preview45min, no V1/public/IAM/schemachange.
Next user outcome and independent membership/audit checks, then remaining release
milestones. Atlas still disabled and Twilio runtime acceptance pending.
## Latest exact repair gate checkpoint — October 12, 2026

Ray reports exactbf77c91 PostgreSQL498 PASS,195.552s,zero failures/errors/skips.
Node83passed locally. Build-only helper scripts/build_auth_repair.sh prepared and
Bashsyntax checked; reuses00038 immutable image, overlays only two tested JS files,
checks frozen sources. Requires raw PASS log, exact checkout and no remaining PG
processes. Chrome lists but cannot attach; user-run terminal fallback needed.
Build/deploy not submitted yet. Organization still NOTcreated per independent DB;
existing activationunused. Next build result/cleanup, private deployment, same
approved activation setup and audited admin/Enterprise verification. V1 unchanged.
## Latest independently verified recovery checkpoint — October 12, 2026

Preview port8080 was closed; restored private auth-2b42560 proxy, API200/verified_accounts.
Live DB: real admin memberships0, activationunused, creationaudit0. Organization
creation NOT completed; prior success inference superseded. Do not issue another
activation. Use existing approved24-hour activation via normal verified-user setup.
Node83passed. Exactbf77c91 nativePG gate submitted, result unknown; inspect
HOME/wzos-release-20261012/postgres-bf77c91.log and cleanup before build/deploy.
Cloud editor stalled; Chrome disconnected. Reconnect in Terminal mode, finish setup,
verify admin/Enterprise and deploy repairs. Clipboard cleared. No new deployment,
main/V1/public routing unchanged. See ORGANIZATION_SETUP_REPAIR_20261012.md.
## Latest HTML-response repair checkpoint — October 12, 2026

Ray reports HTML instead of API JSON after organization setup/selection. Local
workspace startup JSON guard repaired; full Node82 passed, additional organization
HTML regression included in focused26 passing checks. Live00038 lacks these local
repairs. Chrome absent; reconnect requested. Preview expiry/reauth/routing unverified.
Next restore exact protected preview, inspect existing membership/audit and select
company; do not duplicate activation/organization. Prior company-list observation
is not full workspace acceptance. V1/public routing unchanged.
## User-confirmed organization creation — October 12, 2026

Ray reports Molecular Project Development LLC now appears for selection after the
approved activation flow. Prior unknown creation outcome is superseded; no repeat
activation or organization creation. Select its admin/Enterprise entry next.
Workspace entry and independent role/audit readback remain open. Chrome currently
absent from connected inventory; activation clipboard cleanup still required.
## Latest approved admin setup checkpoint — October 12, 2026

Ray approved Enterprise organization/admin setup. Provider identity verified/active;
DB membership and same-name organization counts both0. Single-use24-hour activation
saved0600 privately, copied through editor to WZOS form without token output. Name
filled. Browser failed during submit; creation UNKNOWN. User asked to select company
if present or click filled Create organization once, then reconnect. Do not issue
another code/create duplicate: inspect memberships, activation and audit first.
Clear activation clipboard when reconnected. See ORGANIZATION_SETUP_REPAIR_20261012.md.
Repair d44af92 full Node78 passed, not deployed. V1/public routing unchanged.
## Latest organization setup checkpoint — October 12, 2026

Firebase recovery repair applied under Ray's explicit approval; fresh SDK config
HTTP200/project/key matched. Ray confirms successful password reset. Organization
chooser reached, no listed membership. Organization/join requests422 in live logs;
UI concealed validation arrays. Local client now explains activation/invitation and
validates fields before sending; full Node78 passed/no skips. No backend/schema
change or new deployment yet. See ORGANIZATION_SETUP_REPAIR_20261012.md.
Next confirm single-use Enterprise activation/admin setup for Molecular Project
Development LLC and admin@workzoneos.org, inspect existing membership to avoid
duplication, then normal audited creation and candidate deployment. Public release,
Atlas and Twilio acceptance remain pending. V1/public routing unchanged.
## Latest password-recovery checkpoint — October 12, 2026

Ray confirms admin@workzoneos.org account already exists; reset email arrived but
newest-link Firebase page reports invalid mode. Ray confirmed apiKey query blank.
Provider template/client key metadata matches current runtime; no registered WebApp,
default Hosting site not linked, init.json404. Auth key only allows local/CloudShell,
not Firebase email-action origin. Narrow repair prepared in
EMAIL_ACTION_REPAIR_20261012.md and approval requested: add only Firebase origin,
register WZOS with existing key UID, link existing Hosting site. Not applied yet.
No password/reset code in repository, no verification/IAM/public cutover change.
Auto-review blocked private mailbox read and stored-key lookup egress; metadata-only
alternative completed. Resume approved repair, then fresh user-operated password
reset and sign-in; do not bypass identity checks. Candidate00038 remains private;
Atlas/provider/public-release work still pending.
## Latest authentication UI checkpoint — October 12, 2026

Ray's admin account creation returned a generic provider error; root cause not yet
established. Client error handling repaired and requested open/closed password eye
added. Full Node75 and native PostgreSQL498 passed, no failures/errors/skips.
Exact2b42560 built/delivered as private00038-yoz, auth-2b42560, no main traffic,
IAM/schema/public changes. Ray must retry real account signup/sign-in himself.
Readonly admin identity lookup403 did not establish account absence. Real password
creation remains user-operated; no verification bypass. See
RELEASE_ASSEMBLY_20261012.md for evidence and actual IAP/TLS/public URL-map findings.
Next user retry, real admin/org setup and retire weak synthetic admin; activate
private Atlas/bind providers and prepare confirmed public cutover. V1 unchanged.
## Latest release checkpoint — October 12, 2026

Ray requests public V2 tonight. Exact1afe3d6 passed498native PostgreSQL tests
with zero skips; buildf1a1b800 SUCCESS; private candidate00037-xot Ready,
tracker-1afe3d6, no main traffic/IAM/DNS change. Current SQL compatible/additive
location table only; today's backup successful. Live Google test admin, workspace,
Time Tracker and location-history read passed. Twilio account/sender capability
metadata verified; no sends or AIRA changes. Live Atlas still disabled and origins/
passkey RP still Cloud Shell-specific. Ray selected admin@workzoneos.org for real
admin; retire shared synthetic admin before public exposure. See
RELEASE_ASSEMBLY_20261012.md for exact evidence, billing and remaining blockers.
Next real admin sign-in/setup handoff, public routing/TLS/identity preparation,
activate/test private Atlas and bind/accept Twilio, then concrete cutover/security
confirmation. Current online request supersedes old staging-only product intent;
never represent incomplete functionality or provider acceptance as finished.
## October 12 Time Tracker integration

Time Tracker UI/offline/location changes combined with the current release candidate.
Original source branch preserved. Full Node64 passed, local location HTTP/access and
asset hash checks passed; isolated location Python6 passed/3 PostgreSQL skips.
Windows full Python process crashed before completion; not a passing result.
Next exact Linux/PostgreSQL gate with persistent HOME evidence, cleanup, UI and
budget/schema/backup review, then private no-main-traffic staging deployment.
Cloud gate result unknown following reconnect/missing log; V1/DNS unchanged.

# WZOS V2 remaining tasks — proposed execution order

## Latest execution — October 11, 2026

### Still to do — added at Ray's stopping point

1. Change the Time Clock UI.
2. Clarify offline functions and their limits, including local drafts, reconnect/
   reconciliation requirements, and features that need internet connectivity.

Development paused at Ray's request so the laptop can cool; do not auto-resume.

Address flow clarified and locally implemented: Open in Navigation beside job/
assignment/schedule addresses enters the selected internal destination. Get directions
inside Navigation; duplicate external link removed. Larger phone text and compact
Atlas greeting behavior. Full Node58 passed; admin/member browser handoff passed.
Release gates/restricted updated deployment remain. Ray's Android fit/correct initial
map centering confirmed; newer flow has not yet been deployed to his phone.

Navigation exact6c78ae8 PostgreSQL492 passed/no skips; cleanup/build source checks
passed. Credential replacement/deletion verified, version2 pinned; quotas20/day,6/min.
Private00036-ray zero-main-traffic candidate deployed; synthetic admin route,
directions and visible Google map overlay accepted using one route/map. Anonymous
401/public403 verified. See NAVIGATION_RELEASE_20261011.md. Next Android device,
live member/assigned destination and denied private-job, cancellation/lifecycle,
and billing reconciliation before promotion. Main traffic/V1 unchanged; Twilio hold.

Earlier implementation checkpoint (superseded by release evidence above):

In-app Navigation is locally implemented; see NAVIGATION_IMPLEMENTATION_20261011.md.
Full Node56 passed, focused backend10 passed/six PG skips, local HTTP and responsive
browser disabled state verified. Full Python492 passed with132 PG-dependent skips;
exact PostgreSQL gate remains. Dedicated Routes setup approved/submitted; Ray
reports ROUTES_SETUP_COMPLETE, but independent cloud completion is unverified
after browser timeout. Reconcile metadata without revealing secrets, apply quota/
billing controls, private-tag deployment, bounded live routes and Android acceptance.
No production change, no live routing request; Twilio remains on hold.

Ray clarified that Navigation must be WZOS's own in-app function powered by
Google Maps APIs, for both admin and member. Existing external Maps directions
links are interim/fallback behavior, not completion of this requirement. Plan
the web route/map experience using Maps JavaScript and server-side Routes API:
route display, directions, distance/ETA and supported traffic information. Keep
server credentials private, apply role/tenant-scoped job access and bound requests.
Verify API enablement, credentials, pricing and Android behavior before accepting
integration. Google's Navigation SDK targets Android/iOS native applications;
do not imply it is a browser SDK or promise equivalent background/voice/offline
navigation for the web app. Full native guidance is a separate architecture decision.

Twilio delivery is explicitly on hold pending registration; Ray reports the
corrected sender is saved. See MAPS_ACCEPTANCE_20261011.md: private configuration
and live hybrid imagery passed; embedded Street View is black despite successful
metadata and remains unaccepted. Local candidate adds external fallback and
accurate shared/cloud saving labels. No traffic promotion or production change.

Twilio preparation: see TWILIO_STAGING_CONNECTION_20261011.md. Three enabled
secrets exist, but the sender format needs a corrected version from Ray.
Callback relay is implemented and locally validated (Python476/126 PG skips,
Node47, gateway11); provider authentication, candidate PostgreSQL and live
callback/delivery acceptance remain open. No new IAM grants or deployment yet.

See STAGING_DEPLOYMENT_20261011.md. Exact cf35780 and verified sources are built
and deployed to restricted staging (00031-h5t, 100%). Live schema, backup and
real-provider role/tenant checks passed. Maps revision 00032-9rw is tagged with
zero main traffic; acceptance and promotion remain open. Ray is entering Twilio
credentials himself. Next finish Maps/private-file/module acceptance, connect
provider callbacks/delivery, complete bounded Atlas acceptance and production
routing/passkey/security gates. V1 remains online. Requested cutover authority
does not mark incomplete features below as finished. Older snapshots are historical.

## Current development/testing budget

October10 latest-additions staging preparation: cf35780 release bundle/source
snapshot verified; full local Python465 passed with126 PG-dependent skips,
full Node47 passed. Exact PostgreSQL, live configuration/backup/rollback capture,
build and restricted mobile acceptance remain open. See
LOCAL_ADDITIONS_RELEASE_20261010.md. No deployment/enterprise-v2 merge yet.
Update: exact-candidate native PostgreSQL465 passed with zero failures/errors/skips
(135.288s), reported by Ray and independently observed in Cloud Shell.
Independent temporary-cluster cleanup remains open along with live config/backup,
build, staging and mobile acceptance. No additional regression is needed for
documentation-only acceptance updates.

October10 priority from Ray: increase Atlas intelligence. Bounded operational
context and corrected app capability guidance are implemented in the owned
candidate; see ATLAS_CONTEXT_INTELLIGENCE.md. Next: eight bounded live private
Gemma evaluation cases, then return to durable forms/assignment notifications.
Mock transport and synthetic browser success do not close live AI acceptance.

Current assembly priority (October10): complete internal module connections first,
then connect Twilio, Maps and other providers. See TEST_MODEL_ASSEMBLY.md for the
current capability matrix and sequential assembly passes. Assigned-job Time Clock
linkage preserves private work-order permissions; see ASSIGNED_TIME_CONTRACT.md.
Assigned-job own-form links and read-only dispatch schedule cards are implemented
in the local candidate; see ASSIGNED_FORMS_SCHEDULE.md. Next internal work is
durable completed printable forms and submitted attachments/signatures, followed
by assignment update notifications. Provider connections remain a later phase.

Ray approved **an additional $150 for October 8–17, 2026**, separate from production hosting. Refresh actual usage before paid tests; include build/storage costs and billing lag. Do not exceed this cap without further authorization. Production cutover remains unscheduled.

Updated October 2, 2026 for Ray Andrews, Molecular Project Development LLC.
Product: WZOS powered by Atlas AI Assistant.

This is the current sequential remaining-work list. Ray can add items or revise priorities in Plan mode. Work resumes on explicit user requests; this document does not authorize production cutover. Use SESSION_HANDOFF.md for verified state and the dated evidence documents for completed tests. Older roadmap/checklist status paragraphs are historical, not instructions to repeat completed work.

## October 8 review-workflow increment

October9 parallel module foundation: Codex's isolated integration-release candidate
adds employee profile/qualification APIs and account editor. Contract:
EMPLOYEE_DIRECTORY_CONTRACT.md. PostgreSQL/browser/full Python acceptance precede
merge. Availability, qualification evidence uploads and account lifecycle delivery
remain open. Claude owns Messaging, Enterprise dispatch, Training and expanded
offline module work; Codex owns shared employee contracts, Atlas, report and Meet.

Internal saved-form submissions and self-reported training acknowledgements now have immutable snapshots and organization-scoped admin review in the local integration candidate. They do not include external sending, attachments or qualification issuance. New startup DDL requires PostgreSQL acceptance before deployment. See INTERNAL_FORM_SUBMISSIONS.md, TRAINING_ACKNOWLEDGEMENTS.md and the concise ordered list in REMAINING_RELEASE_WORK.md.

## Starting point

Restricted Google account/database/private-file and SQL restore acceptance already passed. Full-size private Atlas replies and authenticated module guidance passed bounded earlier tests. The preserved source library is now in the staging image. Last verified staging revision 00029-d6k is Ready with Atlas disabled; trial GPU removed and synthetic accounts disabled. The September 29 saved-job/candidate-citation reply passed in 5.288 seconds; see ATLAS_CITED_ACCEPTANCE_20260929.md. Source freshness and job applicability are not approved. Existing code and useful V1 assets will be reused before replacements are built; Supabase is not the replacement runtime.

## Meeting decision

Ray selected Google Meet; admins create/manage, members view/join only. Manual-link scheduling is implemented in the integration candidate; organizer OAuth for automatic space creation and browser acceptance remain open.

## Expanded operational acceptance requested October8

See [operational integration matrix](OPERATIONAL_INTEGRATION_20261008.md). The combined candidate restores saved member forms; delivery, meetings, training completion, account lifecycle, dispatch and live report/Atlas acceptance remain incomplete. Keep these distinct from menu availability. Admin authority stays inside the organization and edition. Combined PostgreSQL/private-files gates precede merging or deployment.

## Mobile access requirement

Phone-first members, desktop-first admins, both fully responsive. Persistence opt-in is implemented in the integration candidate. October8 combined PostgreSQL309tests/zero skips and real Google cookie issuance/revocation passed. Desktop synthetic-provider browser transport/reload/new-tab/logout and opt-out checks passed. Real Google integrated HTTPS, browser restart and real-phone lifecycle remain pending. Passkeys are implemented in the candidate and disabled by default pending new PostgreSQL/schema, token-signing IAM and real-device gates; see PASSKEYS.md. See MOBILE_AUTH_ACCEPTANCE.md.

## Sequential checklist

1. [x] **Finish the pending live Atlas citation test.** Accepted September 29 for one bounded case; see ATLAS_CITED_ACCEPTANCE_20260929.md. Refresh operator authentication, verify Git/cloud state and remaining approved trial spend. Test one saved job through private inference with revision/page citations, missing-evidence warnings, stale-version protection and tenant boundaries. Record the actual answer. Do not repeat previously accepted eight-module tests without a relevant change.
2. [ ] **Finish Atlas reliability and cost testing.** October3 concurrent pair failed upstream IAM403; cleanup verified. Private invocation preflight added and nine focused tests passed; live probe/impersonation permission remain open. See ATLAS_INVOCATION_PREFLIGHT_20261003.md. Pass the guarded invocation check before another concurrent pair.  October 2 explicit cancellation repair passed live: cancellation 0.646s, immediate real-model recovery 200/2.292s, owner/tenant denials and unchanged orders. Real PostgreSQL shared-state tests also passed. See ATLAS_CANCELLATION_20261002.md. October3 cold probe failed503/286.397s; startup preceded the measured request and completed before timeout, so request-triggered cold start and the full failure cause remain unproven. Cleanup verified; see ATLAS_COLD_START_20261003.md. A later October3 cold request passed200/200.741s with startup correlation and cleanup verified; see ATLAS_COLD_ACCEPTANCE_20261003.md. Single-case scale-from-zero is accepted; sustained capacity, GPU stop after cancellation, and representative cost per workflow remain open. The earlier timeout root cause remains unresolved. Verify scale-from-zero, bounded simultaneous requests, cancellation, timeout/provider failures and readable status messages. Measure latency and cost per successful request; keep inference private and scale-to-zero. Resolve failures before treating the engine as production-ready.
3. [ ] **Complete the Virginia reference foundation.** Local coverage audit completed September 29: see SOURCE_COVERAGE_AUDIT_20260929.md; Publication revalidation and local index recovery completed as a partial increment; see SOURCE_REVALIDATION_20260929.md. OSHA direct download and coverage/review completion remain open. October1 combined pass added14 pinned VDOT marking Word documents and prepared a verified139-file source snapshot locally; October 2 snapshot deployed; marking preparation works, but model citation selection repair is now deployed with the cancellation image; targeted real-model marking acceptance remains pending. Text-only contract-scope inspection now records 14 member-specific conditions and revision-bound notes; visual review, project applicability and cloud/model acceptance remain open. Verify current official editions and extraction quality, fill OSHA/VOSH and locality gaps, identify road authority and official forms, and define controlled source updates. Preserve hashes, citations and review states; unavailable or superseded material must remain visible. Extend to other jurisdictions through controlled official-source discovery as coverage grows.
4. [ ] **Finish organization setup and account lifecycle.** Complete signup/invitations, verification and recovery delivery, organization setup, employee profiles/qualifications, and Core/Enterprise entitlements. Enforce exactly admin and member roles on the server. Reuse accepted Google identity/storage and test customer access beyond the internal email domain.
5. [ ] **Finish work orders and measured site inputs.** Validate reusable work-order and approach editors, address/coordinates, road ownership, lanes, speeds, dated traffic evidence, work limits, access and pedestrian constraints. Persist changes with version checks and clear missing-data prompts.
6. [ ] **Complete Maps and placement recommendations.** Verify staging/production key restrictions and representative sites; connect measured geometry to reviewed sign/flagger rules and cited Atlas suggestions. Produce annotated actual site imagery and diagrams with attribution, uncertainty and qualified review. Confirm permitted imagery use/export before packaging.
7. [ ] **Complete Forms hub.** Latest: Codex repair80bafed pushed to PR2; all reviewed defects repaired in local tests (230 Python, 36 PostgreSQL skips; 13 Node). PostgreSQL gate passed October8 on f638931:270tests,zero failures/errors/skips; cleanup verified. Private-GCS and complete UI gates remain before merge. Earlier review notes below are historical.  PR2 at74d9466 reviewed October3; merge withheld for reproduced partial-delete corruption and member access to unpublished uploads. See FORMS_HUB_REVIEW_20261003.md. Branch suites pass (211 Python, 28 PostgreSQL skipped; 12 Node), but repair and integration gates remain open.  Reuse useful V1 templates; distinguish official forms from internal worksheets. Finish required/recommended form selection, revisions, attachments, appropriate signatures, review states, vehicle defect follow-up and print/export. Avoid duplicate recommendations when equivalent evidence exists.
8. [ ] **Complete Work Zone Report and delivery.** Assemble the work order, imagery, diagrams, recommendations, source references and linked forms into a versioned reviewable report. Finish PDF generation, private downloads, authorized review, email preview/send, retry protection and delivery history.
9. [ ] **Finish Time clock and tracking.** October11 local Time Tracker increment adds near-black/orange/gold styling from Ray's live clock.superiorllc.org reference, lightning branding, persistent device shift/task/break timelines and location capture at punches/task changes/reconnect/five-minute intervals. Full Python343:273passed/70PGskipped; Node27passed; desktop/320/390px UI verified. Actual phone GPS/loss-recovery, new PostgreSQL location-table gate, storage eviction and multiple-device acceptance remain open. See TIME_TRACKER_COMPLETION.md and OFFLINE_CAPABILITIES.md. Attendance still requires audited offline reconciliation; no full offline app shell or closed-browser GPS guarantee. Define attendance/payroll boundaries and GPS retention/export/deletion behavior. Keep it a separate module.
10. [ ] **Finish Messaging and Twilio integration.** Implement scoped conversations, notification preferences, delivery/reconnect states and audited SMS/MMS sending with safe retries. Verify sender/provider requirements and use controlled test recipients before customer delivery.
11. [ ] **Finish Schedule management and Enterprise dispatch.** Complete calendar/assignments/conflicts and cancellations. Atlas proposes eligible crews using qualifications, availability and work-order needs; admin reviews before assignment messages are sent. Record acknowledgement and exceptions. Enforce Enterprise dispatch while retaining Core messaging.
12. [ ] **Finish Training, Navigation and agreed integrations.** Reuse authorized V1 courses/media, quizzes, completion and qualification records; verify navigation handoff and unavailable-data behavior. Inventory remaining V1 integrations and optional functions. Each must be implemented and tested or explicitly deferred by Ray; a menu link is not completion.
13. [ ] **Finish Atlas across every module and polish the app.** Give Atlas accurate scoped module data and verified help; separately authorize and audit any write actions. Validate proactive missing-item advice across the workflow. Finish the unobtrusive Atlas assistant, gloss-black/liquid amber-gold presentation, mobile layouts, keyboard access and reduced-motion behavior. Apply usability improvements throughout earlier steps, not only here.
14. [ ] **Consolidate the release and complete operational gates.** Reconcile reusable V1/new assets and repeatable sample data, keep historical backups outside the release, and remove obsolete runtime dependencies. Finish upload scanning, retention/deletion, dependency review, secrets/IAM, CI, alert recipients/delivery tests, cost limits, durable source backups, object recovery and rollback. Reuse existing SQL restore evidence; test remaining recovery gaps.
15. [ ] **Run the complete restricted pilot.** Exercise admin/member and Core/Enterprise journeys across tenants and devices: setup, job, Atlas planning, forms/report, schedule/dispatch, shift, training, navigation, messaging and delivery. Run regression, security, accessibility, load and failure/reconnect tests. Fix blockers and document real capabilities, exclusions and support procedures.
16. [ ] **Approve and launch production.** Review the release candidate with Ray, reconcile every launch gate, confirm ongoing operating cost and support ownership, and approve cutover. Configure app.workzoneos.org routing/TLS, verify monitoring and rollback, and conduct a controlled rollout. Marketing remains at workzoneos.org; preserve V1 until acceptance.

## Milestones and additions

October 1 decision: Ray deferred the earlier September 30 test-model and October 5 production-readiness dates. Replacement dates are unset. Increase daily progress through bounded implementation and validation passes. Previous dates are historical. These are targets, not a claim that the entire remaining scope fits. In Plan mode, estimate this list and agree the test/pilot scope before promising dates; do not silently drop modules or acceptance gates.

New items from Ray can be added below and then inserted into the sequence according to dependencies. No new paid provisioning or customer communications are authorized by this planning document. Preserve the existing approved staging scope and budget.

### Additions to review

- Time Clock product decisions from Claude's `docs/TIME_CLOCK_COMPLETION.md` on `claude/time-clock` (not yet integrated or approved):
  1. Admin self-correction: currently allowed with an audit trail; decide whether any second-person review is required.
  2. Offline draft persistence: October11 implementation follows Ray's offline Time Tracker request; device records survive reload once the app loads, and explicit sign-out/organization switching clears them. Storage eviction and multi-tab/device acceptance remain open; attendance needs audited reconciliation.
  3. Validation windows: currently 14-day submission age, 48-hour shift cap, and a +/-15-minute duplicate hint; confirm or revise.
  4. Active-shift corrections: currently close the shift; decide whether adjusting a still-running shift is supported.
  5. Retention and access: define audit/submission/export retention and member audit exports.
  6. Payroll scope: current exports say payroll is not calculated; confirm the intended integration scope without treating payroll exclusion as decided.

## October 10 repaired module candidate

Assignment inbox increment: My jobs and explicit confirmation with all requested
client/crew/timing/notes fields, frozen at dispatch, are now in the candidate.
Navigation links support both roles. See ASSIGNMENT_INBOX_20261010.md for evidence,
remaining cloud/phone gates and the closed-app push requirement before launch.

Messaging, Enterprise dispatch, versioned training/reassignment and offline drafts are assembled on codex/preproduction-modules. Combined local Python444 and Node37 passed; PostgreSQL/browser acceptance precede release. See CLAUDE_REPAIR_ACCEPTANCE_20261010.md.

Combined PostgreSQL acceptance subsequently passed444 tests/118.086s, zero skips/failures/errors at9c331c4. Browser gates and explicit cleanup confirmation remain before release.

Navigation frontend full Node90 PASS/no skips after overview/endpoint/recenter edits.
No Python/backend/DDL changes since exact db60b7e PostgreSQL546 reported PASS.
Live Google Maps rendering is not accepted by these mocked tests. Cloud browser
inventory timed out again; raw gate log, cleanup and deployment remain unverified.
Endpoint symbols follow Google Maps JavaScript documented Polyline icon sequences:
https://developers.google.com/maps/documentation/javascript/symbols
