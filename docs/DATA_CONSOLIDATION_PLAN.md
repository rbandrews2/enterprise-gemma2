# WZOS 2.0 data consolidation and release cleanup

Updated 2026-09-24. One product: WZOS powered by Atlas AI Assistant.
Runtime target: Google Cloud. Supabase is a recovery source only.
This is a mapping plan, not a completed import or authorization to provision.

## Sample-data clarification — supersedes customer-preservation assumptions

Ray confirmed on 2026-09-24 that V1 was never publicly operated and its customer
accounts/records are artificial placeholders. Migration can replace or discard
those samples. The preferred path is to consolidate useful schemas, templates,
business rules and assets, then seed a coherent V2 demonstration dataset. Do not
spend time reproducing every legacy account, duplicate row or obsolete sample.
This does not classify deployment credentials or Ray's operator accounts as disposable.

The source-to-target map below remains useful for feature coverage. Detailed legacy
customer-row crosswalk/import is optional, needed only for samples selected for reuse.
New V2 demonstration records should retain useful geometry/report examples; rebuild
others as repeatable fixtures. Keep fixture seeding explicit and local/test-only.

## Inventory tooling and observed result

`scripts/inventory_consolidation.py` reads SQLite databases in read-only transactions
and reports table names, columns and counts without exporting row values. Supply
repeated `--database`, optional `--definitions`, and a new `--output` path. Output
creation is exclusive. This is inventory tooling, not a completed importer.

2026-09-24 local inventory saved to ignored `.local-data/consolidation-inventory-20260924.json`:

- Current account validation: 16 tables, 15 rows; includes two attachment records.
- Current workspace preview: 9 tables, 15 rows; includes orders, clock events,
  forms, checklists and a report snapshot.
- Older checkpoint: 6 tables, 15 rows. Treat as recovery evidence, not an additional
  dataset to append to the current preview.
- Legacy catalog: 91 table definitions; customer row exports are unnecessary for
  disposable samples unless a selected feature example requires them.

Next: select/rebuild representative Core and Enterprise demo scenarios, preserve
useful new geometry/report fixtures, and create a file-level release reuse/removal
manifest. No blanket deletion or paid provisioning was performed.

## Evidence and boundaries

Recovered 91 table definitions, policies, triggers, indexes, bucket configurations
and 23 edge-function archives are preserved locally. Customer rows, authentication
records and bucket objects have not been exported. Table names alone do not establish
which generation contains the authoritative data. Local V2 data includes synthetic
preview/emulator fixtures; these must never become customer accounts or payroll.

## Source-to-target map

| Domain | Recovered candidates | Existing V2 destination / action |
|---|---|---|
| Identity | users, profiles, profiles_2, user_profiles, customer_profiles | accounts; verified old UID to new Firebase UID crosswalk; no email-only account merge |
| Organizations / roles | organizations, organization_members, companies_2, memberships_2 | organizations, memberships; explicit organization crosswalk; owner/admin -> admin, member -> member; unknown roles blocked for review |
| Employee qualifications | certifications, work_experience, job_titles | New organization-scoped employee/qualification schema required before dispatch; retain source evidence, expiry and review state |
| Time clock | time_entries, time_entries_2, time_entry_segments_2, job_sites_2, work_types_2 | preview_shifts, preview_clock_events; compare both generations, reconcile durations/breaks/timezones; do not invent event history from totals |
| Work orders / geometry | job_sites_2, job_tasks plus recovered source definitions | preview_orders; preserve new V2 geometry and versions; legacy field mapping still requires row samples |
| Forms | incident_reports, incidents, dvir_reports | module_records and module_revisions; preserve original signed/completed records separately rather than reducing them to editable drafts |
| Scheduling | schedules, schedule_events, schedule_assignments, schedule_notes, schedule_sources, schedule_mappings | module_records (schedule); preserve assignment UIDs, timezone and cancellations; provider-sync metadata needs separate schema |
| Messaging | messages, org_messages, conversations, conversation_participants | Existing fixture_messages is only a basic direct-message model; richer participant/thread/delivery schema required before import |
| Training | training_courses, training_modules, training_progress, course_progress, training_certificates | study_plans is study intent, not certification; preserve completion/certificate evidence in a separate target schema |
| Attachments | six recovered storage bucket definitions and future object exports | private Cloud Storage + workspace_files; authorized parent link, size/hash manifest, scanning/quarantine; no inherited public access |
| New V2 reports / checks | preview_checklists, report_snapshots, module_revisions | Preserve immutable snapshots, revisions and cited source hashes; remap organization/user/parent references together |
| New V2 access data | accounts, organizations, memberships, access_audit | Preserve approved real records and audit history; exclude emulator identities; expire unconsumed invitations/activation codes at cutover |
| Agency knowledge | catalog metadata, preserved originals and local SQLite index | Preserve catalog and document revisions; rebuild index from originals; never substitute current text for historical report citations |
| Payments / integrations | processed_stripe_events, purchases, org_integrations, notification_preferences | Separate reviewed mapping; do not infer edition grants or copy secrets into application tables |

Other recovered social, marketplace, analytics and assistant-call tables remain
archive-only candidates until their product scope and retention are decided.
No unsupported data is silently discarded.

## Ordered execution

1. Inventory every data source with origin, environment, organization, record counts,
   snapshot time and checksum. Classify real, synthetic, duplicate or unresolved.
2. Export approved legacy rows/objects read-only; take consistent backups of new V2
   databases and files too. Verify restoration to separate locations before cleanup.
3. Define field mappings and explicit UID/organization/record crosswalks. Reject
   missing parent links, ambiguous identity matches and unknown access roles.
4. Build an operator-run dry-run importer. Use `(source system, table, source ID)`
   as an import ledger key. Same hash is a no-op; changed data becomes a reviewable
   revision/conflict. Never use last-write-wins across sources or overwrite newer V2 work.
5. Reconcile per-organization counts, clock durations, revisions and file hashes.
   Test member/admin isolation and prohibit cross-organization links. Produce accepted,
   duplicate, conflict and rejected counts with reasons; require totals to balance.
6. Price the exact Google deployment and obtain configuration acceptance before
   provisioning. Run the import against an isolated database, then verify rollback.
7. Establish a cutover write boundary, capture a final delta, reconcile again and
   switch only after acceptance. Preserve the source snapshots through rollback.

## Release cleanup

User requested eliminating staged/historical material from the unified release.
Treat release cleanup separately from deleting recovery evidence. The accounts
Dockerfile already copies selected runtime directories and `.dockerignore` excludes
local recovery/data, credentials, Git and environments. Runtime directories still
contain shared preview code; removing that code now would break the account app.

- Reuse audited business rules, templates, imagery and styling; remove superseded
  runtime copies only after references and regression tests prove them unused.
- Produce a file-level keep/reuse/archive/remove manifest before deleting files.
- Exclude synthetic seed data and legacy deployment scripts from the release artifact.
- Retain source revision, hashes and a tested off-device archive before deleting any
  sole surviving local material. Git does not back up ignored recovery/data files.
- Remove obsolete staging services only after replacement acceptance and rollback
  readiness; no staging service or production site is removed in this pass.

## Immediate next work

Local form-file browser upload is verified. Prepare inventory/dry-run tooling
for both recovered and new records. Actual customer-row mapping, imports, richer target
schemas, off-device backup, cloud acceptance and final cleanup remain open.
