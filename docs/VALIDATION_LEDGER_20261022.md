# Validation ledger — reuse passing evidence

## Time history update deployed - October 30, 2026

Commit 2d77bc6 live at 100% on wzos-v2-accounts-history-2d77bc6.
PWA version 970b793986986cc9adc34a77. Build
 d1a33f69-1c6c-4cb9-b8fc-2fd2e8f63d89 SUCCESS; image digest
100f17c262e3eab4abc3c5b88e9fc9d1bc0a685b8059f4642ed021254656c558.
204 Node checks PASS, no failures/skips. Reused unchanged backend's 977-pass
gate. Prior local browser expand/collapse acceptance retained. Live HTML has
closed history disclosure; JS/CSS match archive bytes; no-store version endpoint
and service worker agree. Runtime settings preserved. No attendance mutations,
IAM, migrations or customer sends. Live browser remains signed out; this release's
install click was not repeated (previous release's update click passed).
Evidence: .local-data/release-2d77bc6 and ~/wzos-release-2d77bc6.
Rollback revision: wzos-v2-accounts-clock-bf522a0.

## Time Tracker recovery deployed - October 30, 2026

Supersedes the local-only clock checkpoints below. Repairs 89274e7 and bf522a0
are live at 100% traffic on wzos-v2-accounts-clock-bf522a0.
PWA version: 41c42a8821e8156528ed3b99.
Image digest: e568dd2965bc11c2aedbd20096049a6d5cec8ad17adbfe801e6cfe5c873b0c35.
Cloud Build 7b7aecc5-e09e-46b1-a7dd-48af776763d7 succeeded.

Full Node gate: 204 PASS, zero skips/failures. Reused the unchanged backend's
977 PostgreSQL passes; no backend/migration changes. Phone-width synthetic
browser check confirmed the seven-second device record and reachable Saved
device records controls (send for review, download, confirmed discard).
Live JS/CSS bytes match tested files. Version endpoint and worker agree.
Actual live Install updates click loaded the new release; DOM release verified
and update prompt cleared. Installed Android acceptance remains user-side.
No real attendance records were submitted or discarded. Runtime configuration,
identity, secrets, resources and ingress preserved; no new IAM or inference.

Rollback: route traffic to wzos-v2-accounts-atlas-2992d86.
Cloud evidence: ~/wzos-release-bf522a0.
Local evidence: .local-data/timeclock-release-node.log and
.local-data/release-bf522a0/{mobile-recovery.png,update-offered.png,live-version.txt}.

## Atlas repair and PWA update release deployed - October 30, 2026

Live: wzos-v2-accounts-atlas-2992d86, 100% traffic, app version
106c379b7fa757dfe873e77b. Code commits: 46c0a13 (Atlas), 2992d86 (PWA).
Image digest: e9872ccadc1f9b4f53b5c4401537d30cd32c5868c163fabd58fe0f667548138d.
Cloud Build f6679e61-98b2-4a60-ad93-b262190f9439 SUCCESS.

Validation: 977 PostgreSQL/backend tests passed in 441.307s, zero skips/errors/
failures; temporary database cleanup verified. Full Node suite 200 PASS. A live
browser check found explicit updates could load a stale shell via the 1.5-second
startup fallback. Repaired only app-updates.js to navigate to a versioned query
URL, which the worker does not intercept. Reran all 200 Node tests successfully;
reused the unchanged backend gate. Browser synthetic stale-cache check: one click
loaded the new release and removed the update prompt. Live original session
showed the update banner; final live update URL loaded the exact latest version
with no repeated prompt. Installed Android-specific acceptance was not run here.

Live API/HTML/worker release IDs match; version endpoint and shell are no-store.
Atlas JS matches the committed archive; updater JS matches the tested patched
file byte-for-byte. Initial raw working-file mismatch was CRLF normalization,
not deployed content drift. Existing identity, resources, secrets, environment,
private model settings, source package and ingress preserved during staging.
No migrations, IAM grants, customer sends or paid inference calls. Ask Atlas's
actual answer quality on Ray's questions remains for in-app acceptance.

Rollback: route traffic to wzos-v2-accounts-atlas-061900a (pre-repair), or
wzos-v2-accounts-atlas-46c0a13 (Atlas repair without PWA fix).
Cloud evidence: ~/wzos-release-46c0a13 and ~/wzos-release-2992d86.
Local evidence: .local-data/release-46c0a13 (Node logs, candidate ZIP, live-version,
update-prompt.png and pwa-one-click-pass.png). Source ZIP SHA256:
31f26287e70a953dfbc01d9e932cd58b6e1fa6ae9fe15e14701393ed745a138a.
Browser returned to sign-in on reload because Stay signed in was unchecked;
this was the existing shared-device policy, not a failed installation.


## Ask Atlas reported-question repair - October 30, 2026 (local only)

Ray reported three unanswered questions after the traffic-control deployment and
provided two examples: proper taper length on a 45-mph road, and a residential
work zone in Roanoke, Virginia. Reproduced both against the exact production
source snapshot; conversational filler routed retrieval into oversized chapters.

Local repair selects explicitly named section topics despite filler/site inputs,
keeps complete sections and mandatory corrections, and deduplicates warnings.
Reviewed pages with documented conflict-only holds can accompany eligible pages
for partial reasoning; those held pages remain ineligible for claims/calculations.
Unreviewed/image-held/incomplete contexts still cannot enter inference. The prompt
and response schema enforce this distinction and preserve discrepancy notices.
Budget failures now ask which operation is planned and retain the exchange in
bounded conversation history instead of displaying repeated technical errors.

Validation: 46 focused Python PASS (26.825s), 8 Ask Atlas Node PASS; diff check PASS.
An initial new test had an invalid empty-claim draft and was corrected; its focused
rerun passed before the final Python run. Real snapshot replay: taper section
10 pages/44,318 bytes with 21 eligible passage choices; Roanoke returns an operation
clarifier without a model call. No paid inference or source-review changes.

NOT DEPLOYED. Production remains wzos-v2-accounts-atlas-061900a. Remaining:
required integrated release gates, browser check, deployment, and bounded actual
answer acceptance. The prior candidate's 972/199 passes are historical evidence,
not validation of these code changes. No schema/IAM/resource/secret changes.


## Traffic-control Atlas release deployed — October 30, 2026

User-authorized latest tested candidate061900a is live at app.workzoneos.org.
Revision `wzos-v2-accounts-atlas-061900a` serves100% of traffic.
Cloud Build `a58d7602-6f5b-47bd-8702-f3d402800e40`: SUCCESS.
Image digest: `8a1e6284beb37422537d257d66be14c28e04d66c951c1b6a403c5392be70604a`.
Public app version: `cc7e94b7283ce912970bcefb`.

Reused972 PostgreSQL/backend and199 Node passes. New release checks passed:
source/package hashes, runtime catalog/index compatibility, live schema (no
missing tables/conflicts/migration), recent successful backup, image compile/pip
check, staged readiness, unchanged identity/resources/secrets/existing settings,
public assets/security headers/protected endpoint401 responses,100% traffic.
No new IAM, GPU settings, customer sends or paid inference tests.

Ask Atlas enabled only for Molecular Enterprise organization
`51704959-cccd-4e2f-964a-cdc4ce8f27cb` using existing private model invocation.
Production references: VWAPM2026, its known-errors document and field guide.
Eight VWAPM issue holds and review restrictions retained; field guide is not
promoted to reviewed authority. Striping/paving originals preserved locally for later.
Bulk managed-account UI/backend updates are included in this tested candidate.

Authenticated browser question acceptance remains for Ray, as requested. The
previous browser session returned to sign-in after reload; no live answer was
claimed or generated. Sign in, select Molecular, then test Ask Atlas.

Rollback: route100% to `wzos-v2-accounts-ui-8cb99c2`.
Cloud evidence: `/home/admin_/wzos-atlas-release-061900a/` (private config/logs).
Local screenshot: `.local-data/release-gates-061900a-20261030/live-release.png`.
CLI startup duplicate sections were repaired after backup to
`/tmp/wzos-sdk-properties-1793409218.bak`; user completed SDK login.

## Integrated release gates passed — October 30, 2026

Step 1 complete for application candidate061900a0c1d176f23a1fcdcc9cd0071ab7b63fe2.
Full backend/PostgreSQL:972PASS; full Node:199PASS; zero failures/errors/skips.
All11 PostgreSQL Time Tracker correction cases included. Cloud source integrity and
private temporary database cleanup independently verified. Initial CRLF shell failure
occurred before testing; shell input normalized, no candidate files changed.
Evidence: docs/ATLAS_INTEGRATED_GATES_20261030.md. Reuse these passing results;
do not repeat for this documentation-only checkpoint. No live deployment or model calls.
Next: authenticated in-app Ask Atlas acceptance, then release/deployment verification.


## Ask Atlas speed repair - October 25, 2026

Implemented stable public-reference prefixes, narrower boundary-page reference hops,
lossless source-passage selection, and elapsed waiting feedback with cancellation.
The repaired hand-signal answer passed in58.91s versus baseline80.86s (single trials);
22510input/1395output tokens. Contextual follow-up PASS29.15s,22738input/665output.
No cache-hit metric or guaranteed latency claim. Final adapter5a555277... matches cloud.
Two earlier optimized attempts were rejected for invalid page IDs/cross-page quotes;
root causes were repaired instead of relaxing validation. Public response unchanged.
41 focused Python cases passed across the focused run and two corrected-fixture
reruns;7Node cases passed; synthetic browser cancellation/progress checked.
See docs/ASK_ATLAS_SPEED_20261025.md for exact hashes, artifacts and rollback.
No new infrastructure/IAM/hosting settings, customer sends, DDL or live deployment.
Required integrated release gates and in-app acceptance remain before deployment;
38 reviewed page representations/8 source holds remain unchanged.


## Ask Atlas structured-answer acceptance passed - October 25, 2026

Completed the formatting/citation repair and proceeded through the next checks.
Final adapter normalized SHA256:
83d94a6dee64d67ad575901f9f2ef348ae4d3d3a455c7d013627c400bd45c5e7.
Preserve special tokens for the pinned vLLM reasoning parser; reasoning remains on.
Require a JSON final answer and continuous page-specific verbatim supporting quotes.
Do not strip arbitrary prefixes, accept partial JSON, fuzzy-match quotes or auto-retry.

Actual private Gemma31B acceptance through GuidelinesGemma, all using the complete
reviewed17-page context with pinned corrections and strict server validation:
- Hand signals/STOP-SLOW: validated draft,80.86s,22983 input/2545 output tokens.
- Virginia flagger qualifications: validated draft,87.74s,22980 input/2819 output.
- Contextual follow-up asking to skip training for10 minutes: validated draft,33.52s,
  23134 input/892 output. Rejected the invented exception, retained conversation,
  and distinguished traffic delay guidance from the worker's assignment duration.
All answers passed JSON/schema/exact-quote/citation checks; final prose was reviewed.
No field approval implied.34-88s latency remains a UX/performance limitation, not an
instant-response claim. No customer data, IAM changes, new infrastructure or deployment.

37 focused Python tests and6 Node Ask Atlas tests passed. The final prompt-specific
regression passed after adding the cross-page quote instruction. Existing access,
cancellation, conflict-notice, context-budget and formula safeguards retained.
Do not repeat these checks unless affected code/source/model configuration changes.

Cloud evidence folder: /home/admin_/atlas-acceptance-6329a06.
Accepted artifacts: acceptance-pages-result.json, acceptance-qualification-result.json,
acceptance-followup-result.json and corresponding logs. Synthetic-only raw diagnostic
responses are separate in that isolated folder; never enable production raw logging.
Source package remains .local-data/atlas-release-sources-20261025 (ignored),52 files;
38 page representations reviewed,8 VWAPM holds retained. Broader source review remains
open. The live app is unchanged. This completes the bounded answer-path repair and
acceptance; deployment/in-app acceptance and broader manual coverage are separate.
Rollback: revert DOT request/prompt changes; no database or source schema changes.


## Diagnostic acceptance result - October 25, 2026

User authorized one diagnostic run. Isolated adapter matched normalized SHA256
6b4d099fc7cedd21392db4526520b8a855143f5b8cfc7672119b492cf81cccb2 (commit16b85f5).
One generation attempt completed in66.93s. Actual input22828 tokens, capacity32767;
completion2009 tokens, total24837, finish_reason=stop, content_present=true.
Adapter rejected response at validate_draft with JSONDecodeError. Context overflow
is repaired; output truncation is not the observed cause. Citation/schema validation
has not run successfully because JSON decoding failed first. Exact formatting cause
is unknown because raw output was intentionally not retained. Do not claim markdown
fences, parser tags or a specific provider bug without inspecting evidence.

Cloud artifacts: /home/admin_/atlas-acceptance-6329a06/acceptance-diagnostic.log
and acceptance-diagnostic-result.json. No automatic retry, IAM change, deployment,
new workload or customer data. Prior local tests were not repeated.
Next: repair the structured-response/parser boundary using targeted format evidence;
keep strict schema, citations and source holds. Do not rerun the same blind check.


## Model context repair - October 25, 2026

### Bounded cloud result and next checkpoint

Repaired attempt finished in96.17s with generic draft-validation failure. Server logs
confirm POST /tokenize HTTP200 at06:34:16Z and /v1/chat/completions HTTP200 at06:35:51Z.
Thus the context guard passed, but answer acceptance did NOT pass. The old adapter
suppressed the precise failure and no raw response was retained; do not claim a
specific quote, schema or output-limit cause. No second generation was launched.
Added safe stage/error-type diagnostics (no question, answer, token or exception text)
and explicit output-limit handling. Focused output-limit/privacy test passed.
Next: use instrumented adapter for one bounded diagnostic acceptance, then fix the
observed cause before release. Preserve all source holds. Source package and prior
20 passing reasoning tests need not be repeated for unchanged code.


The isolated real adapter check stopped before generation: actual /tokenize input
27808 tokens against max_model_len32767, plus unchanged4096 output and4096 safety
reserve exceeded capacity. No generated answer was produced by that attempt.
Removed repeated retrieval/audit metadata from model input, grouped source metadata
once, and retained complete text of all17 pages, captions, headings, applicability,
page notes, citation IDs, corrections, formulas and conversation context. Full original
packet remains server-side for citation validation and audit. No source text clipping,
window increase, IAM change or production deployment.
Packet decreased from93353 to78113 UTF-8 bytes.20 focused reasoning tests passed;
additional inconsistent-source-metadata assertion passed in the affected test.
Cloud isolated adapter normalized SHA256 matches local:
5f4c90809a8b11fa8b9aa919fbc67438071f399ec4d495b5faca08c2a90ea8f9.
Original failure preserved as acceptance-result.json in
/home/admin_/atlas-acceptance-6329a06; repaired bounded attempt writes
acceptance-compact-result.json. No automatic paid retries.


## Source review batch2 - October25

Five more page transcriptions accepted (seven total). Twelve pages inspected;
found hidden extracted taper content, merged-cell loss and image-only correction
table. Manual table transcription saved but ambiguous source cell remains blocked;
review withdrawal preserved. See ASK_ATLAS_SOURCE_REVIEW_20261025.md, batch2.
Next: verified replacement-text/table mechanism; no broad approval or activation.

## Source review started - October25

First batch: VWAPM pages34/36 extraction fidelity reviewed; figure35 held.
Added separately pinned Virginia MUTCD known-errors companion (five pages),
not a replacement for the three-page VWAPM list. Strike-through/diagram semantics
remain blockers. See ASK_ATLAS_SOURCE_REVIEW_20261025.md. No live activation.

## Ask Atlas conversation repair - October24 (pending release)

User reported source dumps and confirmed the gray Ask Atlas button, not the
floating assistant. Fresh Cloud Shell readback: enterprise-gemma2,
admin@workzoneos.org; live ui-8cb99c2 at100%. DOT_ENABLED and
DOT_INFERENCE_ENABLED unset/off, VLLM_ENABLED=0; FIELD_VOICE_ENABLED=1.
This establishes the disabled-button cause; the exact earlier response was not
captured and must not be attributed to Gemma without evidence.

Local repair: answer-first conversational guidance, focused clarification,
bounded four-turn transient context, expandable sources, new-conversation reset,
and unavailable-button explanation. Source eligibility, citation/quote checks,
calculation rules and access boundaries retained. No migration, hosting,
permission or production change. History clears on navigation/session/date reset;
never persisted. Assistant prose is not used for retrieval.

Checks: 28 DOT Python + 5 Ask Atlas Node PASS. Intelligence transport suite:
24/25 initially passed; prompt-size limit caught oversized instructions. After
shortening, all13 affected Atlas intelligence checks PASS (other12 unchanged).
No paid inference/customer sends. Browser visual check, PostgreSQL release gate,
source/page/table/correction review and real-model quality acceptance remain open.
NOT live activation. Reuse unrelated accepted human tests. Bulk-account work
remains separately undeployed; isolate this change from live8cb99c2 for release.


## User-confirmed acceptance — October23

- [x] App loading time tested, diagnosed, repaired and improved; Ray confirmed
  successful device acceptance. Close the pending installed-phone launch check.

- [x] Created a work report using voice and WZOS successfully.
- [x] Created a Daily Work Report using voice and WZOS successfully.
- [x] Reviewed the resulting form and cleared the notification area.
- [x] Created an organization successfully.
- [x] Uploaded the employee roster successfully using CSV.

Evidence: Ray explicitly confirmed these completed workflows in chat. Exact test
time/release and report identifiers were not supplied. Reuse this acceptance;
do not repeat unchanged successful scenarios. Voice failure recovery,
permission edge cases and employee credential provisioning remain separate.

## Managed onboarding — October23

- [x] Admin-created username/password accounts; optional invitations; first-login
  password change; admin/member and seat/isolation enforcement. Deployed7a674b3.
- [x]937PostgreSQL/181Node checks, zero skips; schema/config/public/auth boundary
  acceptance. Reuse evidence in MANAGED_ONBOARDING_20261023.md.
- [x] Approved Google create/update runtime permissions, independent IAM readback.
- [x] Ray Enterprise25 email-bound organization creation grant, seven-day expiry;
  CSV email replacement and backup complete.
- [x] Human acceptance: Ray confirmed organization creation and CSV roster upload.
- [ ] Human acceptance: create an employee login and have the employee change the
  initial password. Roster upload alone does not establish account provisioning.
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

## October25 - source replacement batch3

PASS: test_dot_reasoning.py16/16 and test_dot_manuals.py16/16. Includes four new
replacement integrity, review invalidation and snapshot cases. Logs preserved in
.local-data/dot-manuals/review-20261025/batch3-*. No cloud inference or deployment.

PASS: real local index rebuilt at schema7; both replacement pages reviewed and
selected. Flagger and taper context checks remain blocked pending remaining source
review. Evidence: batch3-rebuild.json, batch3-flagger.json, batch3-taper.json.

## October25 - source review batch4

PASS: local index rebuild; pages24/52/53 select reviewed replacements.55 table
rows mapped; blank minimum, six notes, units and required/optional buffer text
preserved. Targeted Variable Speed Limit context includes both52 and53. Three
additional context checks (signs/taper/flagger) retain source-review blocking.
Artifacts: review-20261025/batch4-*. No runtime code changes; prior32 DOT tests
not repeated. No cloud calls, customer sends or deployment.

## October25 - source review batch5

PASS: local rebuild selects reviewed replacement35; all six-panel labels, scope
and dimensions retained. Correction3 still not answer-eligible. Flagger packet
remains image_review_required. Publisher SHA matches pinned three-page original.
Evidence: review-20261025/batch5-*. No runtime changes; prior32 DOT tests not
repeated. No paid model invocation or production deployment.

## October25 - batch6 and explicit correction precedence

PASS:34 focused DOT tests (after new holds, then after user precedence change).
Second run justified by prompt/policy change. Mock transport confirms correction
precedence; does not claim live model compliance. Source-review fidelity32 pages;
3 reviewed pages retain independent conflict holds. Evidence batch6-final-tests.log
and batch6-final-rebuild/context artifacts. No paid inference or deployment.

### Batch6 final local readiness check

Rebuilt the schema8 index after recording the completed sampled extraction
reviews through the existing source-review API. The old source-level
extraction_checked flags were still false; individual page review and issue
holds remain independently enforced. This does not approve the whole manual.

Final local evidence-packet checks passed: hand signaling flaggers is
ready_for_reviewed_answer with no unreviewed or held dependencies. Taper lengths
and variable-speed-limit queries remain needs_clarification with the documented
source holds/unreviewed diagrams. This is retrieval readiness, not live model
acceptance. Evidence: batch6-final-rebuild.json, batch6-final-flagger.json,
batch6-final-taper.json, batch6-final-signs.json and batch6-final-remaining.json
under the ignored local review-20261025 artifact directory. No paid calls.

## VDOT contradiction wording - October 25, 2026

Added user-requested concise update notice to Atlas guidance instructions. Use
only for documented unresolved VDOT contradictions after applicable known-errors
corrections. Identify the affected item; direct users to check VDOT's website.
Do not assert latest-release currency or active revisions without evidence.
Difficult questions, missing inputs/sources, extraction review gaps and model
errors require their actual explanation, not this notice. Existing source holds
remain intact; this change does not route held evidence into inference.
Focused mocked prompt/token-budget test passed (1 test, no paid inference).
No schema changes or deployment. Initial test command had an incorrect Python
path; rerunning with the verified absolute interpreter passed.

## Source review batch7 validation - October 25, 2026

Real local index rebuild completed. All three new representations bind to
reviewed originals. Assertions passed: physical page49 answer_eligible=true;
pages48/142 page_reviewed=true and answer_eligible=false with original issue
notes retained. Evidence: review-20261025/batch7-validation.json and
batch7-rebuild.json. No application code changed; previous passing tests reused.
No paid model test, production activation or full-manual approval claimed.

## Source review batch8 validation - October 25, 2026

Local index rebuilt successfully. Assertions passed for all three pages157-159:
page_reviewed=true, answer_eligible=false, nonempty original source-issue holds.
Evidence: review-20261025/batch8-validation.json, batch8-rebuild.json and
batch8-reviews.json. Original PDFs unchanged; no runtime code changes, so passing
application suites were not repeated. Source snapshot packaging remains required
before release; ignored source artifacts are not backed up by the Git commit.

## Ask Atlas answer-path readiness - October 25, 2026

Fixed a gap in VDOT notice delivery: held source packets never reach Gemma, so
prompt instructions alone could not display the requested notice. The server now
returns concise discrepancy wording and affected source links only for recorded
VDOT page issues. The UI displays this without fabricating a model answer; missing
sources, difficult questions and unreviewed pages alone do not trigger the claim.
No assertion of latest-publication currency. Existing holds and permissions retained.
Also removed misleading 'this copy alone' warning when no evidence fits the context
budget. Budget remains unchanged; no clipping or added inference calls.

Eight real local retrieval probes: hand signaling flaggers, flagger qualifications,
and STOP SLOW paddle ready for model validation. Taper query reports recorded issues.
Variable Speed Limit exceeds context capacity; pedestrian accessibility, rumble strips
and channelizer questions need additional reviewed dependencies and/or narrower scope.
See ignored review-20261025/answer-readiness.json for exact remaining pages.

Validation: 3 Python source-uncertainty tests, 1 context-budget regression, and
6 Node Ask Atlas tests passed. New Node test initially selected the matching heading
instead of button; fixed selector and reran affected file successfully. DOM simulation,
not browser screenshot or live model acceptance. No paid calls, deployment or schema
changes. Prior passing unrelated suites not repeated.
Next: package source artifacts, validate conversational model answers on ready topics,
and continue the explicitly listed dependencies for broader coverage. Live acceptance
and deployment remain outstanding.

## Verified source release package - October 25, 2026

Built .local-data/atlas-release-sources-20261025 (ignored local artifact).
Verified all52 file hashes, 173573936 bytes. Nine selected page records retain
review bindings: page49 eligible; all eight documented VWAPM holds remain blocked.
Three packaged flagger queries retain ready_for_reviewed_answer status. Evidence:
.local-data/dot-manuals/review-20261025/package-verification.json.
No model acceptance or field approval implied. Do not rebuild/repeat these checks
unless source data or index code changes. Snapshot must be transferred for deployment;
Git does not contain source PDFs or these local artifacts.

Fresh Cloud Shell cloudshell-12336 confirms project enterprise-gemma2 but has no
active CLI account; services.list failed authentication. Login initiated in browser.
Do not use the old terminal's service/flag output as current state. Next: complete
CLI sign-in, read current private model/service configuration and authorized test
path, then run bounded conversational acceptance. No model call or cloud deployment
performed this turn. No new IAM access granted.

## Cloud model access restored - October 25, 2026

Verified successful CLI sign-in as admin@workzoneos.org, project enterprise-gemma2.
Fresh service read: wzos-atlas-inference Ready=True, 20CPU/80Gi/1GPU, maxScale1,
max-model-len32767, request logging disabled. Service IAM binds WZOS app identity;
operator also has effective access (no new grant made).
GET /v1/models with operator identity timed out at25s. Cloud Run system log
confirmed autoscaling startup at2026-10-25T06:21:11Z. One subsequent bounded180s
readiness check returned HTTP200 and google/gemma-4-31B-it. No generation calls.
This proves reachability and existing invocation access, not answer quality.

Prepared three context packets from the verified release snapshot under ignored
review-20261025/model-acceptance/context-1..3.json. Next: transfer current answer
adapter and these packets for bounded conversational acceptance; preserve token
measurement, citation validation and no automatic retries. Do not repeat the source
review/package checks. No deployment or IAM changes this turn.
Browser terminal typeText flattened a multiline command; cancelled via Cloud Shell
Send key combination Ctrl+C. Use paste for terminal commands; failed entry executed
no model probe. Successful probes used a single-line command without printing tokens.
