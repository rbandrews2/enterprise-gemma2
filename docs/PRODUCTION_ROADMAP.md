# WZOS V2 — remaining work to production

Owner: Molecular Project Development LLC (formerly Superior Consultation LLC).
Product: WZOS powered by Atlas AI Assistant. Updated 2026-09-22.
Target: Core and Enterprise editions at app.workzoneos.org, with general/admin access; marketing stays at workzoneos.org. No production date or cutover approval is implied.

## Current verified checkpoint

App image c4ff228, restricted Cloud Run staging wzos-v2-staging-00007-8fs in enterprise-gemma2/us-central1. Latest full suite: 118 tests passed. Local save/reopen and cloud DVIR template display verified. Existing production apps and DNS remain unchanged.

Working test scope: work orders; measured geometry; readiness checklists; time clock with breaks/task intervals; incident and vehicle-inspection drafts; admin-editable team schedule drafts; Enterprise report assembly and personal immutable report snapshots; local agency-reference preparation; Atlas quick guides; gloss-black interface and reduced-motion-aware road-work background. Local model conversation exists but has unacceptable CPU latency. Cloud model and cloud source-library data are not connected. Restricted staging uses one shared synthetic reviewer and temporary SQLite data: it is not a customer-ready deployment.

## Ordered delivery plan and completion criteria

2026-09-23: Ray combined steps 2 and 3 into one integrated workstream. Track execution and acceptance in [COMBINED_MODULE_ACCEPTANCE.md](COMBINED_MODULE_ACCEPTANCE.md). The original requirements below remain in force; this is not a scope reduction.

### 1. Site imagery inside Work Zone Report — next implementation task

- Reuse existing V2 Maps/Street View/geometry components and recovered V1 integrations.
- Verify current browser key configuration and exact local/staging origins; reuse server secrets appropriately without exposing them.
- Add map/site selection, saved work limits, approach overlays and explicit imagery provenance/availability.
- Verify Google attribution and permitted display/export before including imagery in packages.
- Done when representative Virginia jobs show the correct site, missing/wrong imagery has clear recovery, geometry stays linked to the saved job revision, and desktop/mobile interactions pass. Decorative background is never site evidence.

### 2. Finish Forms hub and operational scheduling

- Port reviewed V1 JSA, C85, incident, vehicle inspection and other recovered form definitions; verify which are official templates and which are internal worksheets.
- Add form revisions, attachments, signatures where appropriate, safe print/export, review/submission states and receipts. Finish vehicle defect repair/reinspection workflows before claiming clearance.
- Complete schedule calendar/day views, assignments, date filters, conflicts, cancellation and notification status. No silent dispatch.
- Done when intended general/admin workflows work with persistent records, failures remain visible, and each template has documented provenance and limitations.

### 3. Complete remaining V1 module parity

- Training: recovered course/video catalog, authorized media, progress, quizzes and completion records; validate certification claims.
- Navigation: approved Maps routes, destination handoff, hazards and unavailable/offline behavior.
- Messaging: member-scoped conversations, delivery state, retention and tested realtime/reconnect handling.
- Time clock: reviewed corrections with audit history, date-filtered exports, duplicate/offline reconciliation; GPS consent/retention if enabled. Define payroll integration boundaries.
- Inventory dispatch, video meetings, integrations and admin capabilities against V1, including recovered Netlify source/build evidence. Never equate a navigation link with a working feature.
- Done when a module-by-module acceptance matrix proves parity or Ray explicitly approves an exclusion. Do not silently call omitted modules complete.

### 4. Establish production identity and durable Google Cloud storage

- Inspect reusable Google resources; compare suitable persistent databases against transaction needs and measured costs. Supabase recovery remains uncertain; do not make it a prerequisite.
- Replace fixture users with verified sign-in, organization membership, Core/Enterprise entitlements and general/admin authorization enforced by the server.
- Implement durable jobs/forms/time/schedules/reports storage, private attachment storage, migrations, backups, retention and a tested restore procedure.
- Done when instance replacement loses no records, concurrent clock/report writes are correct, cross-organization access is denied, and backup restoration is demonstrated.
- Dependency: required before real messaging, attendance, customer data or shared report access. UI/template work can proceed with synthetic records first.

### 5. Connect production Atlas and the official knowledge library

- Benchmark model hosting/runtime options, response quality, latency, concurrency and cost; add streaming, cancellation and explicit provider-failure states.
- Move preserved official documents/index into an appropriate durable cloud architecture; retain original editions, hashes, page citations, extraction/review status and update procedures.
- Verify Virginia/FHWA/OSHA/VOSH coverage, road authority, project date and locality conditions. Track missing/superseded sources; use catalog-approved discovery for new jurisdictions.
- Give Atlas accurate per-module context and user-scoped data. Any future write tools need explicit user action, authorization, audit and safe retries.
- Done when grounded answer evaluations, prompt-injection/access tests and agreed latency/cost targets pass. Atlas must state uncertainty rather than invent requirements or actions.

### 6. Complete Work Zone Report outputs and review

- Connect reviewed scenario rules and measured geometry to recommendations for signs/flaggers; distinguish customer measurements, source requirements and AI suggestions.
- Add permitted site imagery overlays, readable diagrams, required/recommended form selection, report revision comparison and authorized shared review.
- Build PDF/package generation and authenticated downloads; add email preview, explicit send action, delivery receipts and retry protection.
- Done when a representative Virginia job produces a traceable reviewed package with accurate source/page/edition references and no unsupported placement or approval claims. Qualified review is required for safety-critical placement acceptance.

### 7. Migration and operational readiness

- Preserve V1 originals and off-device recovery copies. Inventory accessible legacy data and identity crosswalks; rehearse import/export and rollback without modifying originals.
- Configure least-privilege service accounts, Secret Manager, audit logs, monitoring, alerts, quotas and scaling limits. Establish a measured cost budget; alerts are not spending caps.
- Complete privacy/retention, employee location/attendance handling, access recovery and support procedures; verify dependencies and license obligations.
- Done when import reconciliation, restore/rollback drills, alert tests and credential procedures have evidence. GitHub stores source, not ignored local databases/documents/recovery archives.

### 8. Production acceptance and staged launch

- Run full regression, role/edition/tenant isolation, accessibility, mobile, browser, performance and failure/reconnect checks.
- Exercise end-to-end customer journeys: create job, plan/review report, complete forms, assign schedule, record shift, train, navigate, communicate and deliver package.
- Resolve launch blockers in MUST_COMPLETE_BEFORE_LAUNCH.md; update that detailed checklist against actual configuration rather than its historical notes.
- Ray reviews the release candidate and agrees on rollout date. Prepare app.workzoneos.org routing, authenticated access, TLS, monitoring and tested rollback; retain V1 until acceptance.
- Done when approved users can use all agreed modules securely with durable records, supported Atlas responses, monitored costs and recoverable operations. This is the production-ready endpoint, not merely a successful deployment.

## Resume procedure

Read SESSION_HANDOFF.md, this roadmap and current Git status before coding. Begin item 1, inspect existing imagery implementation and credential metadata before creating anything new. Keep local/GitHub source synchronized and record exact staging image commits. Cloud Shell proxy links are session-dependent; reconnect and check existing service state before redeploying. Use synthetic records until item 4 passes. Do not retry old deployment commands from historical handoff paragraphs.
