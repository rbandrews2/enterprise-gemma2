# Supabase recovery review — 2026-09-24

Ray regained dashboard access. Read-only review; no database rows, policies,
functions, authentication settings or secrets were changed. The decision to use
Google Cloud for the new runtime remains in force.

## Confirmed source

Recovered `.local-recovery/core-source-work-zone/src/lib/supabase.ts` references
project `ebzfbuqclkumncnugbvq`, named **social-highway-network** in the dashboard.
This matches a recovered source variant; current live-site environment overrides
have not been verified. The other organization has no listed projects. The older
`rbandrews2's Project` is paused and was left paused.

The Core project's public-schema table picker includes organizations,
organization_members, profiles, certifications, time_entries, dvir_reports,
incident_reports, incidents, time_off_requests, crew_status_updates,
org_messages, conversations, conversation_participants, messages, schedules,
schedule_events, schedule_assignments, schedule_notes, training_modules,
training_progress and hazard tables. This is a partial inventory, not a schema
backup or proof that each module is complete or populated.

Observed organization_members columns: id, organization_id, email, role,
created_at, company_size, member_name, user_id. V2 can map these to verified
account IDs and memberships only after reconciling identity and organization
ownership. Do not grant access by email alone or copy legacy user IDs directly
into the new identity namespace.

## Edge functions

Dashboard lists 23 functions. Relevant candidates include activate,
ai-training-assistant, assistant-context-refresh, assistant-message-send,
assistant-session-init, assistant-tool-invoke, assistant-vision-describe,
assistant-analytics-record, create-conversation, generate-flashcards,
get-youtube-embed-key, schedule-sync, search-youtube (endpoint swift-function),
send-admin-notification and send-notification-email. Names establish inventory,
not verified behavior. Payment/checkout and public intake functions also exist.

Downloaded and preserved schedule-sync.zip under ignored
`.local-recovery/supabase-20260924/`. Archive contains index.ts. It uses a service
role environment variable, accepts body.rows and upserts schedules on
date,job_name. The function body has no caller membership, role, organization,
payload bound or row validation. Gateway configuration was not reviewed, so
this does not establish public exploitability. Preserve the scheduling intent;
do not transplant privileged arbitrary-row writes. V2 must authorize the caller,
derive organization on the server, validate rows, scope conflicts to organization
and record an import audit. Never execute this function against customer data
as a test.

## Next recovery pass

1. Export schema definitions, constraints, policies, triggers and function source
   into ignored local recovery storage; hash a manifest. The schema clipboard
   action reported success but returned no content, so no schema export is claimed.
2. Inspect remaining relevant function code before deciding reuse.
3. Inventory storage buckets and row counts without copying customer content
   into Git. Preserve an authorized backup before any eventual migration.
4. Build explicit old/new ID mapping and a dry-run import with validation,
   duplicate handling and reconciliation. Production migration is not performed.

Ignored recovery material is local-only and is not backed up by GitHub.
