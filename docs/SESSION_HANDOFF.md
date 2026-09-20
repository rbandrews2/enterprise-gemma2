# WZOS V2 pause and resume handoff

Resumed 2026-09-20 at Ray's request. Development remains local; production deployment is not scheduled.

## Completed

- Preserved surviving V1 and Google Cloud source/build materials locally; recovery history is documented in the existing recovery reports.
- Established the separate local-only V2 backend on `enterprise-v2`.
- Implemented the Virginia agency catalog, preserved document revisions, extraction and searchable citations. Six sources were ingested; the OSHA fact-sheet download remains unavailable (HTTP 403). Applicability is not approved.
- Added validated customer intake, proactive JSA recommendation, job-specific reference discovery, and saved projects with evidence references and revision/conflict handling.
- Located existing Street View retrieval and fixed-position overlay code in recovered V17 sources. No satellite/Earth acquisition was found in the inspected Python sources.
- Added the Street View metadata availability adapter and local endpoint. Google access is disabled by default; image downloading, geographic placement, and image export are not implemented.
- Latest implementation commit: `bfc08dbecad727478ddc094ef3c77493368dd06b`, pushed to GitHub `enterprise-v2`. All 62 V2 tests passed, plus a real loopback HTTP check. V1 and cloud services were unchanged.

## Resume here

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
