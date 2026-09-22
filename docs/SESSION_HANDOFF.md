# WZOS V2 pause and resume handoff

Resumed at Ray's request. Development remains local; production deployment is not scheduled.

## Latest resume checkpoint

2026-09-21: completed saved readiness checklists in the isolated app workspace at `http://127.0.0.1:8083`. Run `.venv/Scripts/python.exe scripts/start_workspace_preview.py`; see `docs/WORKSPACE_PREVIEW.md`. Checklists retain authors/timestamps and job-version links, preserve history, reject stale writes, enforce the parent work-order scope, and show stale/read-only revision states. All 94 tests passed; real browser save, server-restart persistence and historical revision checks passed. The synthetic Norfolk sample is job revision 3 with checklist revision 2. Preview server was left running for review; restart if unavailable.

Next: connect the saved work order to the existing V2 project/geometry and cited-reference workflow through an adapter, avoiding divergent job records. Atlas currently runs intake rules only; checklist claims are not verified evidence. Continue local synthetic development. No production/cloud/Cloud Shell changes, new paid services or deployment date. Supabase 2FA recovery, live backend inventory, router upgrade, production authentication and off-device backup remain open. Original Core recovery files are preserved.

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
