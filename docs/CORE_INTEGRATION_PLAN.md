# One WZOS platform: Core and Enterprise

Decision proposal, 2026-09-20. Owner: Molecular Project Development LLC. No production migration or DNS change has been performed.

## Recommendation

### Confirmed product direction — 2026-09-20

Ray selected `https://app.workzoneos.org` as the eventual shared Core/Enterprise application address. `https://workzoneos.org` will carry product explanations and module/function descriptions. Design the signed-in application as a task-focused workspace with persistent navigation, direct access to tools, compact project context and responsive mobile layouts. Keep promotional sections and long module introductions on the public website; retain contextual help where it supports a task. This direction does not authorize a production cutover or replacement of the existing V1 deployment yet.

Reuse the editable Core React application and migrate it in stages into `enterprise-gemma2`. Keep one frontend, one organization/account model and a shared API. Treat Core and Enterprise as organization entitlements, with general and admin permissions inside each edition. Enterprise includes Core capabilities plus advanced Atlas workflows. Rebuild deficient modules selectively; do not recreate the whole product or maintain separate edition forks.

The fastest safe transition is a source-based rebuild with a temporary compatibility adapter for the existing backend. Hosting the frontend on Google Cloud while it still calls Supabase is only an intermediate milestone. The final target moves application compute, data, files, identity and operational configuration to Google Cloud. External providers such as Maps, payments and video meetings remain integrations where appropriate.

## Evidence and limits of this inspection

- Current Core production: `https://app.superiorllc.org`, as supplied by Ray and confirmed in Netlify and the live page.
- Netlify project `workzoneos`, published deploy `69fe1fe30ce8180923504b8f`, May 8, 2026. Netlify reports deployment through Drop, with build stages skipped; no commit-to-deploy identity was established.
- Initially preserved 72 public deployed code/config files; subsequently recovered and verified the complete 98-file deployment ZIP. Hashes and provenance are in `CORE_RECOVERY_MANIFEST.json` and `CORE_DEPLOY_ARCHIVE_MANIFEST.json`. This frontend archive is not a customer-data or off-device backup.
- Found editable source in `rbandrews2/dev`, commit `e5d7167bd1834a393fae8e2e19ed8b515f08c0e9` (July 2, 2026). It contains React/TypeScript/Vite, 274 files under `src`, SQL scripts, and 12 Supabase function directories plus shared code. Its date is newer than production; exact parity must be established before importing it as the baseline.
- Also preserved an older `rbandrews2/work-zone` source checkout locally. It is a historical reference, not the chosen production baseline.
- The live Core page was signed out. Inspection covered its visible homepage, deployed code, and recovered source. No account was created, license accepted, customer record read/changed, message sent, purchase made or administrative action executed. Backend deployment/schema/RLS, account behavior, billing and real data remain unverified.

## Core capability inventory

| Capability | Evidence observed | Integration treatment |
|---|---|---|
| Accounts and organizations | Supabase Auth, profiles, organizations, membership roles; organization activation flow | Preserve account/organization IDs and mappings; enforce organization membership on the server |
| General/admin navigation | Member, admin and owner logic; shared admin dashboard | Preserve the general/admin distinction; separate platform operations from customer organization administration |
| Work orders | Editable form, job-title lookup, browser-local storage and sample roster | Reuse form; replace device-only records with organization-scoped persistence; import local records before changing origin |
| Time clock and timesheets | Time entries, jobs/tasks, rate snapshots, CSV export, admin edits | Reuse workflows; validate server-side timestamps/permissions and pay calculations before relying on totals |
| Forms | C85, JSA, DVIR, incident, whistleblower, company forms and time off | Reuse field definitions/templates; add durable drafts/submission receipts and accurate failures |
| Messaging | EchoChat conversations/messages with Supabase realtime subscriptions | Preserve conversation/user mapping; replace realtime adapter when backend migrates |
| Scheduling | Calendar/day/editor routes; schedule events and assignments; another schedules table path | Reconcile overlapping schemas; preserve assignments and admin editing |
| Dispatch | Admin dispatch jobs, locations, status and assignment fields | Reuse UI, migrate persistence and access checks |
| Training | Course catalog, videos, progress, quizzes/certificates and admin content management | Preserve content and completion records; reconcile local progress with server records; verify certification claims |
| Navigation and hazards | Google navigation/places code, hazard records, Leaflet offline view, weather route | Reuse selected UI/logic with shared Maps configuration; test actual offline behavior and map licensing separately |
| Meetings | Zoom join/launch links | Preserve integration; this is not a self-hosted conferencing service |
| Assistant | Shared assistant UI and Supabase assistant functions | Retain existing Core assistant capability; route advanced Enterprise work-zone features through the Atlas API |
| Integrations, licensing and administration | Provider adapters, vault references, activation, checkout, purchase status, webhook and owner/admin functions | Port selectively after access-control and secrets review; preserve paid entitlements and webhook idempotency |

Code presence does not establish that a feature is fully configured or working in production. C85/JSA currently offer browser print/JSON export rather than evidence of shared server storage. Some submission failure branches use demo-success messaging; those must become honest failure states. The downloaded navigation build has an empty Maps configuration. The service worker caches the shell but does not establish full offline mapping or synchronized offline forms.

## Edition and access design

| Edition / role | Intended access |
|---|---|
| Core / general | Current Core crew capabilities, scoped to permitted jobs, own records and authorized conversations |
| Core / admin | Core capabilities plus management of that organization's crews, schedules, dispatch, forms and settings |
| Enterprise / general | Core general capabilities plus entitled Atlas planning, references, imagery and package workflows |
| Enterprise / admin | All enabled organization capabilities and their administrative controls |

Platform support/billing administration is a separate internal permission, never automatically granted to every customer admin. Qualified plan approval is also a distinct permission; buying Enterprise or being an admin does not establish engineering qualifications. Core's existing assistant/features should not be removed merely because Enterprise is added.

Use server-validated identity plus membership, edition entitlements and action-level permissions. UI flags are presentation only. Test all four combinations, unauthenticated users, cross-organization IDs, expired/revoked memberships, edition downgrades and attempted role/plan spoofing. Default-deny newly introduced permissions.

## Google Cloud destination

- **Cloud Run:** shared frontend and application API containers in the existing project, with staging isolated from production data. Keep Atlas inference separate from routine Core requests so everyday operations do not require GPU activity.
- **Cloud SQL for PostgreSQL:** preferred relational destination for existing organizations, scheduling, forms and timesheets. Supabase is more than PostgreSQL: its auth helpers, realtime, storage and functions need explicit replacements. A SQL restore alone is insufficient.
- **Identity Platform:** target for application identity. Inventory auth providers, password formats, IDs and MFA first; rehearse import and rollback. Google documents BCRYPT import, but password preservation depends on the actual export. Do not assume active sessions or every identity provider migrate unchanged.
- **Cloud Storage and Secret Manager:** private attachments/source documents and service credentials, with access mediated by the application. Keep static presentation assets separate from customer evidence.
- **Background jobs:** introduce Cloud Tasks or equivalent only where needed for exports, delivery and retries; avoid provisioning extra infrastructure before load and requirements justify it.

The selected application hostname is `app.workzoneos.org`, serving both editions. Keep `app.superiorllc.org` working during migration and preserve the existing V1 at `app.workzoneos.org` until the approved cutover. Domain moves affect localStorage, service workers, cookies, login callbacks and Maps referrers.

Cost approach: reuse the frontend and relational model; start with a small number of services, bounded instances/connections, on-demand Atlas calls and measured request costs. Cloud SQL has a running-instance cost and continuing storage charges, so size from real usage and retain the existing backend only during the limited transition. Do not self-host the entire Supabase stack by default: it adds operational components and maintenance. No new paid resources are provisioned in this plan.

## Numbered migration sequence and completion gates

1. **Preserve and reconcile.** Complete the deployed ZIP/media backup; identify the exact source baseline; archive hashes. Recover live schema, policies, functions/configuration, auth settings and object inventory separately. Treat SQL snippets as candidates, not proof of the installed schema. Gate: reproducible local build and a route/feature parity checklist against production.
2. **Prepare a clean import.** Bring reviewed Core source into `apps/wzos-web` in a dedicated branch/commit. Exclude environment files, private data, cached dependencies, nested Git history and generated bundles. Keep recovery copies unchanged. Build with synthetic configuration, run dependency/credential checks, then isolate backend calls behind adapters.
3. **Unify organization access.** Define the server-side edition/role permission matrix and preserve stable user/organization IDs. Implement and test membership enforcement before connecting real data. Gate: four-role regression tests and negative cross-tenant tests pass; local-only V2 is not exposed publicly.
4. **Integrate one complete workflow locally.** Use organization → work order → form/time entry → Atlas planning as the first vertical slice with synthetic data. Reuse Core UI and connect the completed V2 planning APIs. Remove sample-success behavior and preserve failed drafts. Gate: real save/reload/error behavior plus cited Atlas preparation for a saved project.
5. **Stage the frontend/API on Google Cloud.** After the build and identity controls pass, prepare a staging deployment using a separate test backend. A controlled compatibility adapter may temporarily retain Supabase; this is not the final all-Google-Cloud state. Gate: general/admin behavior, Core/Enterprise entitlements and provider configuration match the test matrix. Production remains on Netlify.
6. **Migrate backend capabilities in groups.** Port identity/membership first, then jobs/time/forms, scheduling/dispatch, messages, training, storage, integrations/licensing and background delivery. Use a single authoritative writer per dataset; avoid uncontrolled dual writes. Preserve IDs, timestamps, file hashes, organization links and audit trails. Rehearse customer-data restores with access controls before the real migration.
7. **Rehearse cutover and rollback.** Capture database/object backups and browser-local exports, freeze affected writes or replay a verified delta, reconcile counts/checksums and representative records, verify login/provider callbacks, purchase webhooks and permission tests. Test new-origin storage and PWA behavior. Keep Netlify and the prior backend recoverable; define how any post-cutover writes are reconciled before rollback.
8. **Schedule production with Ray.** Only after acceptance, cost review and backup/restore evidence: approve the hostname/DNS switch, monitor the pilot, then retire old services after a retention window. No production date is assumed.

### Immediate next task

The source-parity inventory and isolated Core builds now exist; see [baseline status](CORE_BASELINE_STATUS.md). Next complete live backend inventory after Supabase sign-in, authenticated parity and durable backup. Repair the six TypeScript errors and triage dependency findings in a separate change. Resolve known persistence/error-handling and access-control findings before importing production credentials or data. Do not deploy the downloaded minified files as the permanent V2 foundation.

## Primary technical references checked

- [Cloud Run with PostgreSQL on Cloud SQL](https://docs.cloud.google.com/sql/docs/postgres/connect-run)
- [Identity Platform user migration](https://docs.cloud.google.com/identity-platform/docs/migrating-users)
- [Cloud SQL pricing](https://cloud.google.com/sql/pricing) and [storage billing FAQ](https://docs.cloud.google.com/sql/docs/postgres/faq)
- [Supabase backup/restore](https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore) and [self-hosting responsibilities](https://supabase.com/docs/guides/self-hosting)
