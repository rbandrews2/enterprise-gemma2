# WZOS V2 pause and resume handoff

Ray authorized a separate restricted Google Cloud V2 staging deployment. Production cutover is not scheduled.

## Latest resume checkpoint

Visual follow-up: user-provided road-work banner is now the local workspace decorative background, 17% opacity, 3px blur, subtle alternate 35-second drift. Reduced-motion preference disables animation. Browser appearance and image HTTP delivery verified. Not yet deployed to cloud staging.

2026-09-22 module integration: Forms hub (internal incident drafts) and Schedule management (admin-editable, team-readable drafts) now work locally. 116 tests passed; synthetic browser saves verified. Atlas quick guides updated. See docs/MODULE_INTEGRATION_PROGRESS.md for exact coverage and remaining V1 parity. Cloud staging has not received this increment. Resume module parity before further storage groundwork, while retaining production identity/persistence gates.

Storage groundwork: extracted SQLite transaction component and added operator consistent snapshot/restore-to-new-file command. See docs/WORKSPACE_STORAGE.md. No cloud persistence or identity enablement yet; next inspect existing cloud database resources and choose the persistent adapter while preserving clock transaction guarantees.

Final staging revision: `wzos-v2-staging-00004-swh`, app image commit `3a69b4200ff664dc79fcca71cd913f46fded8ee9`. Final browser reload passed. Next: durable cloud data and server-verified user/organization identity, followed by cloud Atlas inference and preserved source-library integration. Continue using synthetic records until those gates are complete.

Restricted staging deployed and verified (authenticated API 200, anonymous 403, browser clock-in/out succeeded); Ray authorized this environment; production apps and DNS stay in place. Gloss-black surfaces now dominate, with orange/amber accents verified against live app.superiorllc.org. Dedicated staging factory and Dockerfile reuse the tested workspace with Cloud Run IAM as the outer boundary, one fixed synthetic reviewer, and explicit ephemeral-data warnings. No customer authentication, durable storage or cloud model is claimed. See docs/CLOUD_STAGING.md for deployment verification and limits.

Module structure clarification: inspected signed-in V1 at app.superiorllc.org, including navigation and Access modules cards. See docs/WZOS_MODULE_STRUCTURE.md. Time clock remains a separate top-level module in the unified app. Work Zone Report is the comprehensive module combining the basic work order with imagery, Atlas recommendations, diagrams and required/recommended forms. Sidebar labels now reflect the user's module vocabulary; full Work Zone Report remains visibly unavailable until connected. Existing preparation tools are only part of that future workflow.

Time clock integration: read `docs/TIME_CLOCK_INTEGRATION.md` and recovery manifest. Inspected clock.superiorllc.org Netlify deployment 69fbb890a565ad9951a85943, preserved compiled assets locally, and adapted its task/shift/break workflow into V2. Time clock now shares the workspace and work orders in both editions. Server timestamps, command receipts, expected versions and a unique active-shift constraint protect recording; admins can view scoped team history. Atlas has time-clock guidance and own-user saved status but cannot mutate attendance. Supabase is still blocked; no new project or cloud deployment was made.

108 automated tests and JavaScript syntax checks passed. Core general isolation and Atlas quick-guide navigation were checked in the browser. Browser test completed and reloaded one synthetic shift with three task intervals, 31 work seconds and 14 break seconds. Next time-clock work: production database/identity design, audited corrections, date filters/export, then GPS/offline reconciliation. Full parity and actual payroll use are not claimed. Older AI latency follow-ups remain unresolved.

Live checklist evaluation: the real local request timed out after 110.2 seconds with HTTP 503 and the explicit retry message. Checklist context is verified by tests, but real generated checklist-answer quality remains unverified. Six focused intelligence tests passed after the HTTP 499 regression. Prioritize CPU inference performance before further model-heavy browser testing.

Checklist-aware Atlas increment: the assistant receives the selected accessible work order's latest saved checklist, category statuses, bounded notes (300 characters each with truncation flags), saved job revision and staleness. The response exposes checklist basis separately from generated prose. No checklist saved is distinct from work not done. Cancellation now uses an explicit disconnected state and HTTP 499 instead of propagating task cancellation through middleware as a server error.

102 full-suite tests passed, covering latest/stale/missing checklist context and cross-organization isolation. Next: improve local inference latency/streaming and verify completed-reply navigation in the browser; then reuse Maps display. Production remains unchanged.


2026-09-21 integration follow-up: Atlas replies now offer application-owned navigation to the job board, readiness checklist, measured approaches and Enterprise planning references. Stop reply aborts the browser request and cancels server inference on disconnect. A real browser test exposed the middleware/polling disconnect issue; replaced polling with a receive watcher and retested cancellation followed by another request. No autonomous mutations added.

101 automated tests pass. Real local AI explained measured-approach entry (78.8 seconds) and refused a prompt to falsely claim crew dispatch (92.8 seconds). CPU latency remains unacceptable for production. Next: streaming/performance, more grounded-answer evaluations, saved checklist context, then reuse existing Maps display. The post-cancellation browser request was accepted but timed out; retry controls recovered. Successful navigation metadata was verified over HTTP; completed-reply button click-through remains pending. All production/cloud boundaries remain unchanged.

2026-09-21: completed measured-approach editor reuse and real local Atlas inference. Read `docs/ATLAS_LOCAL_INTELLIGENCE.md`. Work-order form now saves shared JobGeometry fields and approach paths; synthetic Norfolk sample is revision 5. The assistant question box now calls a real local model through scoped API context, bounded history, timeouts and explicit error states; no autonomous actions. Customer-facing brand is "WZOS powered by Atlas AI Assistant". Technical model names are confined to operator/backend material.

99 automated tests passed; final bounded-history change passed the three focused intelligence tests. Real API response explained creating a work order (cold CPU request about 64 seconds). Real browser conversation declined an unavailable clock-in action. Runtime and preview were left running for review on loopback ports 11435 and 8083. Restart with `.venv/Scripts/python.exe scripts/start_atlas_runtime.py` and `.venv/Scripts/python.exe scripts/start_workspace_preview.py --atlas`. Model weights/binaries are ignored local files, not in GitHub. No cloud deployment or production changes occurred.

Next: improve interactive latency/streaming and cancellation, test broader app guidance and grounded answers, then integrate existing Maps display into this workspace. Production model hosting, licensing/distribution review, identity/organization authorization, qualified placement review and remaining launch gates are unfinished. Older checkpoints below are historical.

2026-09-21 Atlas scope correction: Atlas is the app-wide assistant for all functions and both editions. Restored the user-supplied image, persistent avatar, dismissible greeting, local topic/question guide and section navigation in the single-page preview. Recovered Core assistant components and knowledge inventory remain the React reuse foundation. This guide is explicitly local keyword-based help, not Gemma chat. Browser guidance/dismissal checks and 11 preview tests passed. Next preserve this companion while integrating measured geometry; later wire verified module context and Gemma/tool guidance across all routed pages.

2026-09-21: connected the work-order preview to existing V2 Atlas preparation through `services/workspace_preview/atlas_adapter.py`. One saved work-order record feeds ProjectDraft, source discovery, evidence review and placement readiness without writing a second project. Added reported authority/speed/lane-count/work-period fields and preserved API-supplied JobGeometry during browser edits. Gloss-black theme retains recovered V17 green/gold styling cues. Read `docs/V1_REUSE_DECISIONS.md` and `docs/WORKSPACE_PREVIEW.md`.

All 95 tests pass. Real browser saved the Norfolk sample at job revision 4 and returned 17 candidate passages across six topics, with VDOT/FHWA citation details visibly checked. Checklist revision 2 is now correctly stale. Preview remains at http://127.0.0.1:8083; run `.venv/Scripts/python.exe scripts/start_workspace_preview.py` if stopped. No Gemma call, new download, imagery generation, field approval, production/cloud change or paid service.

Next: reuse the existing measured-approach and geometry editor in this app workspace, followed by Maps/imagery integration with existing restricted credentials. Geometry is validated through the shared schema today but lacks an editor on port 8083. Checklist claims remain separate and unverified. Supabase 2FA, live backend inventory, router upgrade, production authentication and off-device backup remain open. Preserve all recovery materials.

## Previous pause checkpoint — historical

- Latest code checkpoint: `b711b41` on `enterprise-v2`, following repair commit `d53cc85`. Both pushed to GitHub. The sections below retain chronological history; older counts and pending items are superseded by this checkpoint.
- Core recovery: complete 98-file Netlify archive verified locally; 309-file source export preserved. Separate Core repair candidate passes TypeScript, Vite production build and local shell/guest-admin redirect checks. All six original type errors are fixed; dependency audit now reports two moderate React Router advisories, zero high/critical. The existing V2 suite last passed all 84 tests during the recovery increment.
- Resume with `docs/CORE_REPAIR_STATUS.md`, `docs/CORE_INTEGRATION_PLAN.md` and `docs/MUST_COMPLETE_BEFORE_LAUNCH.md`, then verify Git status before editing. Next local milestone: app-style Core/Enterprise workspace with synthetic organizations, test identities and records, followed by one complete saved work-order workflow. Keep test identity handling separate from production authentication.
- Domain/design decision: `workzoneos.org` contains product/module explanations; `app.workzoneos.org` is the future shared functional app. Both editions have general/admin roles. Preserve current Core at `app.superiorllc.org` and V1 at `app.workzoneos.org` until an approved cutover.
- Blockers/open gates: Ray's Supabase 2FA-app issue prevents live backend inventory and backup. Do not repeatedly ask for sign-in or bypass authentication. Authenticated parity, off-device backup/restore and a tested router major upgrade remain open.
- Recovery archives, original source, local databases and credentials remain in ignored local directories; GitHub preserves code, repair patch, tested dependency lock, manifests and plans, not those local materials. Off-device backup is not complete.
- Temporary Core preview servers were stopped and verification tabs closed. No production deployment, DNS change, cloud migration, customer-data change or Cloud Shell checkout update occurred. No automatic continuation is scheduled; wait for Ray to resume.

## Completed

- Preserved surviving V1 and Google Cloud source/build materials locally; recovery history is documented in the existing recovery reports.
- Established the separate local-only V2 backend on `enterprise-v2`.
- Implemented the Virginia agency catalog, preserved document revisions, extraction and searchable citations. Six sources were ingested; the OSHA fact-sheet download remains unavailable (HTTP 403). Applicability is not approved.
- Added validated customer intake, proactive JSA recommendation, job-specific reference discovery, and saved projects with evidence references and revision/conflict handling.
- Located existing Street View retrieval and fixed-position overlay code in recovered V17 sources. No satellite/Earth acquisition was found in the inspected Python sources.
- Added the Street View metadata availability adapter and local endpoint. Google access is disabled by default; image downloading, geographic placement, and image export are not implemented.
- Latest implementation commit: `bfc08dbecad727478ddc094ef3c77493368dd06b`, pushed to GitHub `enterprise-v2`. All 62 V2 tests passed, plus a real loopback HTTP check. V1 and cloud services were unchanged.

## Resume here

2026-09-20 repair candidate: all six Core TypeScript errors fixed through a tracked patch, with preserved source unchanged. Updated dependencies within existing ranges; typecheck/build and local guest/admin redirect checks pass. Audit now has two moderate React Router findings, no high/critical findings; a separately tested major upgrade remains. Read `docs/CORE_REPAIR_STATUS.md`; exact dependency manifest/lock are saved under `scripts/core-repair-dependencies/`. Ray cannot access Supabase because of a 2FA app issue; do not repeatedly request sign-in or attempt to bypass it. Continue a synthetic-data app-style workspace locally. Live backend inventory, authenticated parity and off-device backup remain open.

2026-09-20 Core recovery continuation: full 98-file Netlify deployment ZIP verified and preserved locally; exported 309 source/assets/config files into an isolated synthetic build. Two Vite builds pass with identical output hashes; local browser shell and guest redirect pass. TypeScript has six existing errors and dependency audit reports 16 high/19 moderate/7 low findings requiring triage. Read `docs/CORE_BASELINE_STATUS.md` and its three evidence JSON files. Supabase dashboard requires user sign-in for live backend inventory. Source remains outside the main app; no production migration occurred. Next: authenticated backend inventory and parity, then separate type/dependency repairs before clean import acceptance. Recovery remains local-only pending off-device backup.

Product direction confirmed by Ray on 2026-09-20: `workzoneos.org` holds product/module explanations; `app.workzoneos.org` is the selected future shared Core/Enterprise app. Build an app-like, task-focused workspace rather than a promotional landing page. Preserve contextual task help. This is a design/domain decision, not authorization to replace either live application before the migration gates pass.

2026-09-20 current resume point: scenario selection, measured approach input forms and saved-revision table preview are complete. All 84 tests and a real browser save/preview passed. Current Core is `app.superiorllc.org` on Netlify; Ray wants Core and Enterprise together in Google Cloud, each with general/admin access. Inspected Core deployment and recovered its public code plus editable `rbandrews2/dev` source (newer than production; parity unverified). Read `docs/CORE_INTEGRATION_PLAN.md` and `docs/CORE_RECOVERY_MANIFEST.json`. Detailed internal findings remain in ignored `.local-recovery/core-netlify/CORE_AUDIT_PRIVATE.md`. Next: reconcile the Core source baseline and prepare a clean isolated build, then shared server-side edition/organization permissions and a local vertical slice. No Core import/deployment/DNS switch or production data migration has occurred. Full Netlify ZIP and durable recovery backup remain incomplete.

2026-09-20 table-preview increment: `/v2/placement/reference-preview` now exposes pinned, visually checked VWAPM Table 6P-V3/V4 lookups for a stationary-shoulder reference preview. All 81 tests and real local HTTP passed. See `docs/PLACEMENT_RULES.md`. TTC-4.0 has a visible Known Error label and inconsistent note/sign references; complete sign-layout/coordinate generation remains disabled. Next: workspace scenario selection and measured approach inputs, while resolving the diagram discrepancies. This preview is not qualified engineering approval or a complete plan; V1/cloud unchanged.

2026-09-20 approved credential setup completed: enabled Maps JavaScript (`maps-backend.googleapis.com`) and API Keys API in `enterprise-gemma2`. Created `projects/910004733138/locations/global/keys/wzos-v2-browser` (display name `WZOS V2 Browser Maps`). Independent describe verified Maps JavaScript-only API restriction and referrers `http://localhost:8081/*`, `http://127.0.0.1:8081/*`, `https://app.workzoneos.org/*`. No key value printed or committed; legacy key, live app and Cloud Shell checkout untouched. Next: securely configure local `WZOS_GOOGLE_MAPS_BROWSER_KEY` from this new credential and test live map/Street View, billing and quota behavior. Creation is complete; runtime integration remains pending.

Maps lookup follow-up: secret access succeeded inside Cloud Shell, but API Keys returned 403 for missing `apikeys.keys.lookup` permission under admin@workzoneos.org. No key was exposed or cloud resources changed. A metadata-only helper is saved at `scripts/check_maps_credential.py`. Separate restricted browser-key/API setup is proposed in the launch checklist and requires confirmation before creating the credential.

Launch tracking: [Must complete before launch](MUST_COMPLETE_BEFORE_LAUNCH.md) is the consolidated open checklist. Live Cloud Console inspection found `GOOGLE_MAPS_API_KEY` in Secret Manager with enabled version 1, but no API keys listed in this project's Credentials page. Key value/issuing project/restrictions were not verified. Resolve existing credential ownership and suitability before creating duplicates or exposing any key to the browser.

Job details/geometry and Google display increment: the workspace now saves structured job inputs and reported work-limit lines; Atlas checks missing geometry fields. Google hybrid map and nearby Street View code is implemented with on-demand loading and a dedicated browser-key configuration. All 76 tests plus browser save/missing-key checks passed. Live imagery remains unverified because `WZOS_GOOGLE_MAPS_BROWSER_KEY` is not configured. See [geometry and Maps setup](GEOMETRY_AND_GOOGLE_MAPS.md). Next: restricted-key setup/live provider verification and reviewed placement rules, not further placeholder-only UI.

Completed response capture and follow-up review: customers can save per-finding notes/dispositions in project revisions; Atlas reconciles them on the next run and flags context changes for reconfirmation. See [Atlas responses](ATLAS_RESPONSES.md). All 73 tests and the browser save/review flow passed. Next: structured intake/geometry answer capture and a reviewed placement-rule contract, then model integration. Free-text responses do not fill those fields automatically.

Latest direction: review any relevant missing form/function, not primarily JSA. Atlas preparation now returns categorized project advice with reasons and next actions across context, forms, evidence, deliverables and operations. Unknown external arrangements are not labeled missing. Next is structured answer/form inventory capture so resolved items can be tracked, followed by reviewed rules and model integration.

Atlas preparation increment: **Let Atlas help** now connects a saved project revision to context questions, JSA, evidence review and cited reference candidates. This is deterministic preparation, not Gemma-generated placements. See [Atlas workflow](ATLAS_RECOMMENDATIONS.md). All 70 tests and a browser click-through passed. Next: structured answers/geometry and reviewed placement rules, followed by model integration.

Local editor added: `/v2/workspace` loads projects, edits proposed markers and saves revisions. It uses a clearly labeled coordinate preview without imagery. See [local workspace](LOCAL_WORKSPACE.md). Next: Google map display and usage verification; full product UI remains open.

2026-09-20 increment: project revisions now preserve proposed geographic point annotations and evidence links. A version-selectable GeoJSON endpoint exposes them for future maps. See [geographic annotations](GEOGRAPHIC_ANNOTATIONS.md). Next is map display/editing and Google usage verification before enabling imagery retrieval/export.

1. Check branch, working tree, and this handoff against current code before making changes.
2. Continue the imagery workflow: define geographic annotations for signs, flaggers and work areas; preserve their evidence and review status. Existing fixed-pixel overlays are historical examples, not placement rules.
3. Verify Google display, retention and PDF/email permissions before enabling those operations. Intended sources are Maps satellite/hybrid, Street View, and optional current field photos.
4. Connect dated traffic/speed evidence, road geometry, project conditions and reviewed agency references to proposed placements. Do not treat imagery alone as proof of traffic volume or compliant placement.
5. Continue package generation and delivery preparation after those foundations. Actual email integration and production rollout remain separate steps.

## Boundaries and product direction

Molecular Project Development LLC (formerly Superior Consultation LLC) owns the project. Enterprise Gemma V2 supports Work Zone OS, Virginia first. The full destination includes planning, forms, annotated imagery, PDFs/email, time clock/tracking, messaging, integrations, dispatch, navigation, training and schedules.

Preserve useful V1 materials. Keep local code and GitHub synchronized; do not deploy or overwrite Cloud Shell in this milestone. Production timing remains to be discussed with Ray. The live site is `app.workzoneos.org`; its historical UI is not the intended V2 design.

Downloaded agency documents, the search index, project databases and recovery archives are intentionally outside Git. A GitHub push does not back up those local files. Preserve them in place; separate durable backup remains an operational follow-up.

## Detailed plans

- [Implementation plan](V2_PLAN.md)
- [Imagery backend](IMAGERY_BACKEND.md)
- [Project workspace](PROJECT_WORKSPACE.md)
- [Source coverage](SOURCE_BACKEND_STATUS.md)
- [Customer workflow](CUSTOMER_WORKFLOW.md)
- [WZOS requirements](WZOS_GEMMA_REQUIREMENTS.md)

## Live Maps verification — 2026-09-20

The dedicated browser key is configured locally in `.local-data/credentials/wzos-v2-browser-key.txt` (Git ignored). Run `./scripts/start_v2_local.ps1` from PowerShell; it loads the key into the child server environment without printing it, binds to 127.0.0.1:8081, and restores the prior environment on exit. An alternate key file can be supplied with `-BrowserKeyFile`.

Live browser checks against an isolated synthetic Norfolk project (36.8508, -76.2859) successfully loaded Google's hybrid map with attribution and a nearby Street View panorama. Street View reported capture date 2022-09 and a nearby location, not the exact requested coordinate. No customer project was created or changed. The test server was stopped. All 76 tests passed; launcher syntax parsing passed. No imagery was downloaded or exported. Production referrer behavior, quotas/cost limits, marker overlays, missing imagery cases and export permissions still need validation.

## Placement readiness — 2026-09-20
Atlas now returns versioned placement-readiness checks and displays them in the workspace. All 78 tests passed plus real HTTP workspace-script verification. See docs/PLACEMENT_RULES.md for the reviewed-rule provenance and geometry contract. No numeric agency rule or automatic placement is enabled. Next: review one stationary closure typical application, its tables/notes and measured approach geometry before implementing a narrowly scoped rule.
