# WZOS remaining tasks - current October 18, 2026

Use SESSION_HANDOFF.md for source/live provenance and COLLABORATION_CONTRACT.md for
ownership. This checklist supersedes historical status entries, which are preserved
in history/REMAINING_TASKS_before_sms_acceptance_20261017.md. Product decisions and
older evidence remain there; do not silently discard or re-open completed gates.

## Closed latest checkpoint

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
