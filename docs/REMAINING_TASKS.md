# WZOS V2 remaining tasks — proposed execution order

## Current development/testing budget

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
9. [ ] **Finish Time clock and tracking.** Initial open-session offline support is local; see OFFLINE_CAPABILITIES.md for limits and remaining synchronization work. Validate durable clock/break/task records, admin corrections with audit history, date-filtered exports and duplicate/offline reconciliation. Define attendance/payroll boundaries and any location-consent/retention behavior. Keep it a separate module.
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
  2. Offline draft persistence: currently open-tab only; decide whether drafts survive reload/crash and define sign-out/shared-device clearing.
  3. Validation windows: currently 14-day submission age, 48-hour shift cap, and a +/-15-minute duplicate hint; confirm or revise.
  4. Active-shift corrections: currently close the shift; decide whether adjusting a still-running shift is supported.
  5. Retention and access: define audit/submission/export retention and member audit exports.
  6. Payroll scope: current exports say payroll is not calculated; confirm the intended integration scope without treating payroll exclusion as decided.
