# WZOS remaining tasks - current October 20, 2026

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


## Employee import — October22 development

- [x] Admin-only Organization management / Account / Employees import action,
  template, UTF-8 upload, row review, duplicate/error handling and confirmation.
- [x] Organization-private roster, no automatic accounts/invitations/sends;
  atomic/stale/idempotency guards.16unique backend and26account Node checks PASS.
- [x] Synthetic desktop browser upload/review/import receipt (2imported/1skipped).
- [x] PostgreSQL/additive-schema gate, narrow-screen import acceptance and release:
  919PostgreSQL/179Node PASS, zero skips; live ui-a1d24d1 at100%. Signed-in
  dashboard/dialog/roster read accepted. See AVAILABLE_UPDATES_RELEASE_20261023.md.

## October 22 operational completion / accepted Voice flow

- [x] Ray accepted Voice incident contents, in-app notification and review-clear
  behavior; prelaunch requirement checked. Do not repeat this accepted scenario.
- [x] Preserve all accepted tests/repairs/reuse rules in VALIDATION_LEDGER_20261022.md.
- [x] Live numeric secret pinning at pins-1022181839, same80c3819aimage; bounded
  config/readiness/public acceptance and independent readback PASS. Rollback ui-16d0905.
- [x] Alert routing: four existing policies connected to enabled info@workzoneos.org
  channel; full conditions unchanged on readback. No test delivery claimed.
- [x] Cleanup access: approved storage.objects.delete-only role bound on the one
  file bucket to the app runtime; exact additive readback PASS, no customer cleanup.
- [x] Close the three operational configuration follow-ups on the prelaunch list.

Exact outcomes/receipts: OPERATIONAL_FOLLOWUPS_20261022.md. Five targeted guard
checks passed; no broad suite rerun or new application image. Earlier sweep
snapshots below are historical; use this checkpoint for current live state.

## October 22 sweep 2 follow-ups

- [x] Focused cloud-file adapter/cache/update checks: 18 passed, zero skips.
- [x] Read direct runtime IAM, bound-secret scope, private model/scanner invocation,
  operational policies, redacted error metadata and bucket lifecycle configuration.
- [x] Match vendored Daily SDK to official npm bytes; package advisory query empty.
- [x] Attach approved info@workzoneos.org to the four existing alert policies.
  Enabled channel/unchanged conditions verified; no test alert sent.
- [x] Pin the two latest secret references to verified version1 on the same image;
  live pins-1022181839. See OPERATIONAL_FOLLOWUPS_20261022.md for checks/rollback.
- [x] Apply approved narrow object-delete repair; exact role/bucket binding readback
  PASS. Effective-policy troubleshooting and real cleanup/recovery remain separate.

Evidence/limits: PRELAUNCH_SWEEP2_20261022.md. No new full-suite rerun or deployment;
direct principal checks do not close effective group access or OS/bundle review.

## October22 unassisted prelaunch testing

See PRELAUNCH_ENGINEERING_RESULTS_20261022.md and the updated Codex/human lists.
Node174PASS; broad PostgreSQL890run found one stale synthetic demo error; repaired
full gate891PASS,zero skips at8d29bbf. Dependency advisory repairdfef889 has separate
affected checks. Synthetic signed-form dump/restore PASS; native
cluster cleaned up. Core communications entitlement and browser CSP repairs are
committed on the development branch, not deployed. Latest live remainsui-16d0905.
Read-only runtime checks verified hourly weather successes, SMS test mode,
Voice model target/scaling, backup/storage safeguards and existing budget alerts.
Local DOT index rebuilt; content review/activation not established. Device,
provider, managed recovery, privacy/business decisions and final release gates
remain. Do not repeat paid pilots or treat activity as guaranteed CLI sign-in.

## Form signature follow-up

- [x] Local printable-form signing pad, typed alternative, safe persistence and
  office/print/download rendering;12focused checks pass (4Node,8SQLite).
- [x] Affected PostgreSQL submission/signature tests8PASS; deployed with compact
  weather and visible report review as ui-358cf45. See FORMS_WEATHER_RELEASE_20261022.md.
- [ ] Real-phone handwriting and actual PDF visual check. Full consolidated launch
  acceptance list: PRELAUNCH_REQUIREMENTS_20261022.md.

## Latest release acceptance (supersedes earlier local-only release entries)

- [x] Receipt/admin office alert deployed100% as ui-edd310b; PostgreSQL878/Node163PASS,
  zero failures/errors/skips. Backup/schema/build/stage/public auth/assets/version/
  traffic PASS. See OPERATIONS_RELEASE_20261020.md.
- [x] User confirms real Voice report counts/objects; live read-only inspection finds
  the October19 report in draft state. Do not treat it as delivered.
- [x] Authenticated office alert and Open office forms link accepted on ui-edd310b.
- [x] Final placement repair3737af7: PostgreSQL878/Node163PASS; public serving assets,
  API denial/CSP/version06cb438e96196bd4b724c67b independently PASS.
- [ ] Recover Cloud Shell/browser to read final build/traffic/runner artifacts and
  visually accept follow-up alert placement. Do not repeat completed gates/builds.
- [ ] Ask Atlas DOT source/page/table/correction review and bounded provider pilot;
  DOT flags remain off. Voice/weather/IAM/runtime policy preserved.

Use SESSION_HANDOFF.md for source/live provenance and COLLABORATION_CONTRACT.md for
ownership. This checklist supersedes historical status entries, which are preserved
in history/REMAINING_TASKS_before_sms_acceptance_20261017.md. Product decisions and
older evidence remain there; do not silently discard or re-open completed gates.

## Latest priority - Ask Atlas Work Zone Guardian

- [x] Local dedicated Enterprise page and featured mobile/desktop launch cards;
  typed/recorded questions, cited replies, optional local Read aloud, cancellation.
- [x] Local context-first Gemma transport, actual tokenizer budget check, source/
  correction/page review gates, shared request controls and reviewed arithmetic.
- [x] Three new work-zone originals matched to fresh official downloads; seven-PDF
  local index covers2627physical pages. This is indexing, not full source review.
- [x] Legacy visible report builder retired; historical reports/PDF access preserved.
- [ ] Reconnect Cloud Shell and verify current account/project/live state.
- [ ] Run bounded CPU OCR and visual review of initial traffic-control sources,
  corrections, tables and formulas; pavement markings next. No full-coverage claim.
- [ ] Package verified library; run frozen-candidate PostgreSQL release gate.
- [ ] One bounded synthetic pilot within approved$5: max1Speech/3Gemma generations,
  existing model only; no automatic repeats/new GPU/workload/permissions.
- [ ] Verify installed-device permission reuse, audio shutdown and local Read aloud;
  organization allowlist/roles/Core denial; staged rollback and limited activation.

Keep Voice reporting separate/stable. Maps/navigation is unrelated. Weather
configuration remains on hold. No new public release is claimed by these checks.
Implementation, source hashes and exact restart steps: ASK_ATLAS_ENTERPRISE_20261020.md.

## Closed latest checkpoint

- [x] October20 UI organization/mobile Home/top account/Clock In/Voice copy and
  public-shell startup/shortcut refresh deployed: source6047e5b, ui-6047e5b100%,
  image2b194352..., version270e2a2ea96f733144a59d9b. Cloud155Node/849PostgreSQL,
  backup/schema/runtime/public hashes/auth/traffic and browser review PASS.
  Weather configuration unchanged under hold; Voice activation preserved.
  User-approved cleanup reclaimed2.13GB from twelve old dependency environments,
  preserving source/logs/credentials/evidence; Cloud Shell home52% used.
  See UI_RELEASE_20261020.md. Actual installed-device launch/update acceptance open.

- [x] Atlas real app metadata invocation and synthetic saved-job/reference plumbing:
  2/2 requests, stale409/cross-tenant404/Core403 denied before inference. Workloads
  deleted, guard stopped, production unchanged. See ATLAS_APP_WORKFLOW_RESULTS_20261018.md.

- [x] Private full-size Atlas31B operator pilot:8/8 synthetic responses, mean2.86s
  warm; verified service deletion/guard stop/production unchanged. No customer Atlas
  activation. See ATLAS_PILOT_RESULTS_20261018.md. Context corrections local27 PASS;
  release gates and app/source integration remain below.

- [x] Core-admin Enterprise upgrade implementation deployed, sourcebf9f524/image
  f347f690…,100% upgrade-live-bf9f524. Final810 PostgreSQL/136 Node/7 SDK gates pass;
  persisted Stripe permissions, non-persisted credit/tax preview, schema, public
  assets/auth/policy and real Enterprise-admin dashboard checks passed. No charge.
  Paid existing-subscription acceptance remains separate below. Same-image paused
  rollback prepared; see CORE_UPGRADE_RELEASE_20261018.md.

- [x] Fixed weather card, NWS adapter, scoped manual job-alert checks/receipts and
  foreground arrival prompts deployed; approved hourly monitor now active (SMS off).

- [x] Completed-form Send to office, immutable office receipt and admin in-app notice
  validated on the live app with a synthetic form.
- [x] SMS verification completed by Ray; ordinary one-way text notification received
  on the approved phone. Controlled test-recipient acceptance is complete.
- [x] SMS challenge overlap repair deployed;19 local/8 PostgreSQL checks passed.
- [x] Supplied WZOS logo/favicon/device icons and exact Daily fallback policy deployed
  as brand-4e281c6;25 public asset hashes/config/policy checks passed. Media retest open.
- [x] Local generated test cache removed; fresh Cloud Shell has no owned temporary
  test cluster, proxy or deployment helper running.

## Next execution order

1. [x] Restore Cloud Shell CLI sign-in and verify project/account/live revision.
   admin@workzoneos.org/enterprise-gemma2; brand-4e281c6 ready and100% traffic.
2. [ ] Complete remaining installed-app acceptance. Ray confirmed Android home-screen
   launch has no browser address bar and no repeated Install WZOS prompt (October17).
   Update prompt and pending-draft preservation remain separate checks; do not mark
   them accepted from this result. No forced uninstall/storage clearing.
3. [ ] Daily embedded meetings: admin creates; organization member joins; two consenting
   devices see/hear each other inside WZOS; Leave stops camera/microphone; validate
   cancellation/expiry and participant revocation behavior. Recording/transcription off;
   approved initial session maximum two devices/five minutes. See DAILY_MEETINGS_INTEGRATION_20261014.md.
4. [ ] Atlas in-app integration: private31B operator inference passed8/8. GCS loading
   needs no HF_TOKEN binding; no model service remains after bounded cleanup.
   Integrated gates for the current-capability context patch PASS (811 PostgreSQL,
   136 Node, no failures/skips); isolated synthetic harness local check passes.
   Test-only image eaa44f81… passed2/2 real metadata-authenticated app requests and
   synthetic source provenance/tenant checks; both workloads removed. See
   ATLAS_APP_WORKFLOW_RESULTS_20261018.md. Next validate reviewed authoritative
   sources, customer-app browser inference, real cold requests and security/source
   evaluations. Ongoing hosting and public activation remain open.
   Do not equate UI/retrieval/scanner or operator-token success with app acceptance.
   Price further resource changes and obtain scoped workload access approval.
5. [ ] User-led paid Core-to-Enterprise acceptance remains. Implementation is live,
   key permissions saved and non-persisted provider preview passed. No real payment
   attempted. See CORE_UPGRADE_RELEASE_20261018.md. Validate one-time $20
   credit, existing Core subscription transition, seat/edition consistency and
   webhook retries/rollback. Upgrade prompts admin-only. New-customer checkout is
   integrated; real payment acceptance remains separate. See FINAL_CHECKOUT_VALIDATION_20261016.md.
6. [ ] Finish practical multi-role/multi-organization journeys: dispatch -> My jobs ->
   acknowledgement -> navigation -> time -> completed form -> office review/text;
   course link editing/playback/qualification completion; session/passkey/device
   persistence and offline reconciliation. Reuse accepted tests; focus on real gaps.
   Navigation uses in-PWA routes and Google Maps for active turn-by-turn guidance.
7. [ ] Broader SMS activation only after sender/registration/consent/opt-out and
   tenant coverage review. Current runtime remains approved-recipient test mode.
   Verify office-form SMS and assignment notification delivery without duplicate sends.
8. [ ] Provider connectors: scoped WZOS export API exists; QuickBooks/Workday/payroll
   synchronization is not implemented. Choose actual provider, authorized OAuth and
   field mapping before claiming a connector works. No secrets in chat or Git.
9. [ ] Operational/security release closure: monitor remaining distro-image findings,
   assess patched images, retention/deletion/access reviews, alert delivery, backups,
   object recovery, incident runbook, budget controls, accessibility/load/reconnect
   pilot. Atlas scanning/holds are implemented; no SOC2 certification claim.
10. [ ] Consolidate final acceptance and support/operating-cost documentation, resolve
    or explicitly defer remaining gaps with Ray, then deploy any new accepted updates
    with configuration preservation and billing/security-compatible rollback.

## Planned integrations

- [ ] Atlas DOT manual-grounded Ask Atlas and report references: local Python
  foundation complete; four supplied VDOT PDFs2117pages indexed,42focused checks
  PASS. Hash-pinned imports/full-page citations/section browsing/diagram candidates/
  source and image-review gates/disabled Enterprise API/private Gemma adapter added.
  See ATLAS_DOT_KNOWLEDGE_20261020.md. No live activation. Finish source currency,
  applicability and visual/OCR review, VDOT reuse rights, user-facing Ask Atlas and
  report citation selections, release gates and bounded real-model acceptance.
 2019 training presentation not ingested; NCDOT/Caltrans not populated. Do not treat
  source indexing, exact quote checks or a diagram keyword hit as field approval.

- [x] Weather/geofencing implementation c6adf9f deployed; hourly pilot activated.
  Ray chose a fixed compact weather card showing basic live conditions, following
  user location after permission; label source time/stale data and location fallback.
  Combine with official local hazards and independent assigned-site alert monitoring:
  notify affected workers/admins, clearly distinguish location versus job alerts.
  Implemented: location contract, weather card, durable notices/acknowledgements,
  consent-gated SMS integration and foreground arrival prompts. Cloud suite769,
  weather PostgreSQL23, local Node133 and Cloud frontend6 passed without skips. See
  WEATHER_GEOFENCING_INTEGRATION_20261017.md for reuse, defects and product decisions.
  Public weather-c6adf9f100% passed runtime/28 asset/policy/auth checks.
  Hourly pilot active per WEATHER_MONITOR_ACTIVATION_20261017.md: first worker pass
  succeeded; Scheduler caller returnedHTTP200; web exact-org coverage100% deployed.
  SMS remains OFF. Zero configured sites: admin must review/save coordinates/windows;
  actual hazard delivery and moving-device arrival acceptance remain open.

## Included polish

- 2f44ed3 fixes one encoding artifact in SMS request guidance; deployed with4e281c6.

## Rules and product decisions

- Admin high access, member basic access; organization isolation applies to both.
- Core/Enterprise entitlements and all active-login seat counts, including admins.
- Daily meeting creation admin-only; members can join authorized meetings.
- One-way SMS notifications; user-owned consent and verified phone required.
- Existing-Core upgrade credit is one-time $20; Enterprise offer approved in commerce docs.
- Preserve approved black/amber glass design; mobile landing uses its launch cards.
- Later production target dates are unset. Work efficiently; do not manufacture
  readiness claims or repeat large suites for documentation-only changes.


## October 18 current local candidate
- [x] Personal weather independent of job selection; four-day NWS outlook and high/low values.
- [x] Location permission checks before weather foreground restarts, navigation fixes and Time Tracker captures; setup remains the explicit prompt point.
- [x] Reuse sidebar glass cards in a visible vertical mobile list; no duplicate landing-page menu.
- [ ] Read earlier Smart Field Voice cloud exit files, then validate integrated current candidate. No claim that f176c53 gate covers later UI/weather changes.
- [ ] Real Android retained/revoked location and mobile menu checks, forecast visual acceptance, then approved release. No deployment yet.
- [ ] Plan confirmed PWA + Android first, then iOS; no native build started.


## Mobile simulator — October 18
Local simulator implemented in scripts/run_mobile_preview.py and scripts/mobile_preview/. Open http://127.0.0.1:8083/__simulator; see MOBILE_PREVIEW.md for restart and isolation. Six focused checks PASS; actual iframe and rotation observed. Original foreground exec session94769 ended; earlier voice preview stopped. Browser automation repeatedly timed out during final screenshot/interaction, so no final screenshot acceptance claim. Fixed dashboard single-column selector specificity after simulator revealed two columns. Public site unchanged; prior voice/audio fixtures remain separate unfinished work. Continue preview review before release gates/deployment.


### Simulator loading repair
Added scripts/start_mobile_preview.ps1, with hidden background launch, readiness check, saved process/log pointers, and guarded -Stop. The new launcher returned SIMULATOR_READY and independent HTTP checks returned200 for simulator/app. State: .local-data/mobile-simulator/server-8083.json. Keep this process available for user preview. Browser URL policy blocked automated visual verification; ask user to refresh the existing simulator tab, do not bypass the block. Live site unchanged.

### Shared mobile Home
- [x] Same styled full-page Home for both roles, authorized cards only; module pages retain Home return; desktop unchanged. Browser verified locally; see MOBILE_HOME_20261018.md.
- [ ] User visual acceptance, then current integrated gates before public release. No live update in this increment.

### October 18 live release closure
- [x] User-authorized mobile Home/weather release deployed at100%; PostgreSQL831 + Node148 PASS, no skips, schema/backup/config/public checks PASS. See MOBILE_RELEASE_20261018.md. Earlier local-only gate/deployment items above are superseded for c944173.
- [ ] Real Android retained/revoked permissions and location-weather movement checks. Smart Field Voice source95bc0f8 passed832 PostgreSQL/149 Node checks; app798c479c… and pilot5f666853… built successfully. Scoped Speech permission is approved and verified. Private model pilot approved but not launched; disposable job identity approval pending. Ten-recording real-provider pilot, ongoing model hosting approval, public feature activation and installed-Android recording acceptance remain open. Voice processing is disabled. See FIELD_VOICE_ACTIVATION_20261018.md.

- [ ] Field Voice diagnostic completed, cleanup verified; four semantic cases show later-sentence recognition loss. Frozen repair35b409f cloud gates running. Prepare exact-image CPU-only US long recognition acceptance; obtain approval before new app-identity job/model choice. Then full workflow acceptance, ongoing hosting/activation approval and Android hardware checks. Production Voice remains OFF.

- [x] Long Speech-only pilot finished:3/4PASS; arrow boards not recognized. Job cleanup independently verified,0model/0SMS.
- [x] Vocabulary repairc7669cc passed834 PostgreSQL/149Node/mocked workflow; conditional CPU-to-GPU guard4checksPASS. Immutable appc6e687b8…/test86c814b8… built/verified.
- [ ] Exact-image combined CPU4/conditionalGemma10 approval and real acceptance. No new pilot or public activation yet. Scope FIELD_VOICE_ACTIVATION_20261018.md; ongoing hosting and Android hardware acceptance remain open.

- [x] Approved vocabulary Speech retestfzr47:3/4PASS; only literal arrow_boards cuefalse. CPU job deleted/absence verified, no GPU launched. Original conditional full-pilot approval was not consumed.
- [ ] Fresh approval for unchanged full semantic workflow test, with explicit review of the single lexical mismatch; retain all report assertions and USD5/hour-cleanup limits. No new runtime build is needed; helper-only guard5checksPASS. Public/ongoing hosting remains unapproved.

- [x] Final full pilotn9c5h completed9/10expected cases,10Speech/8Gemma/0SMS; one equipment-name failure:4Aero boards. All owned workloads removed/absence verified; guard stopped.
- [x] Configuration repair implemented: require/defaultlong, specificarrowboardboost10, equipment ambiguity guidance/review warning; original quantities/name/transcript preserved. No migration/IAM/secret changes.
- [ ] Retest repaired runtime ONLY after user resumes testing; regression cases are written but unrun. Prior834/149 results/images are pre-repair. Do not auto-repeat cloud pilots. Production activation remains pending and VoiceOFF.

- [x] Repaired runtime1d2da6b: PostgreSQL836/Node149PASS, no failures/skips; focused8 and single-case mocked acceptancePASS. Preserve results; do not rerun suites.
- [ ] Finish Google CLI credential refresh (user action in SDK tab/CloudShellterminal0), then build exact repaired images. CloudShellterminal1 for checks; do not paste commands into code prompt.
- [ ] Obtain ongoing hosting + exact-image one-recording acceptance/conditional live activation approval after build. No repeat ten-clip pilot, no newDDL/credential grants. Production remainsunchanged/VoiceOFF.

## Superseding Field Voice status
- [x] Google CLI refresh, repaired exact build238ef05b/testb564dfa1 and originalRTX ongoing-hosting approval completed.
- [x] One approved activation check ran:1Speech/1Gemma/0SMS; ambiguity warning present, exactequipment gateFAIL (4Aero boards vs4arrowboards). No repeat test.
- [ ] Resolve recognition/acceptance issue before public Field Voice activation. Failed attempt removed model/job and did not cut over; see FIELD_VOICE_ACTIVATION_20261018.md. Do not treat earlier checklist approvals/build tasks as still pending or the failed live check as passed.

## Smart Field Voice live closure (supersedes earlier pending items)
- [x] User approved reviewable flagged drafts;7inertpolicychecks and focusedmockedworkflowPASS.
- [x] Approved exact6346 livecheckPASS underreviewed-equipment-v1,1Speech1Gemma0SMS; temporaryjob removed/absenceverified.
- [x] FieldVoice deployed100% voice-live-1d2da6b,version0d1aaad29aceb5c98c94772b; privateRTX31Bmin0max1 underapprovedongoinghosting. OrdinaryAtlaschatOFF. Stagedrollback/publicauth/assets/config/trafficchecksPASS; Enterprisebrowsercontrolsverified. No newDDL/customer sends. Priorfailurepreserved.
- [ ] User-led installedAndroid microphone setup/retainedpermission/30secrecording/review/send andtrackshutdown checks. Never infer these from syntheticcloud acceptance. See FIELD_VOICE_ACTIVATION_20261018.md; do not repeat completed suites or deployment.


## October 20 presentation update
- [x] Save future photo-report concept: FUTURE_PHOTO_REPORTS.md (no implementation).
- [x] Local layout/startup and supplied shortcut icon-reference updates; see UI_ORGANIZATION_20261020.md.
- [x] Simulator recovered; final mobile Home/Forms/training/routes and Core/member filtering inspected. No horizontal overflow at360/390px.
- [ ] Integrated release gates, exact build/staging verification and deployment. Live remains unchanged.
- [ ] Real installed Android repeat/cold launch and shortcut artwork refresh acceptance.
