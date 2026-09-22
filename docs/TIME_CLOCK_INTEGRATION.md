# Time clock integration and recovery

## Source inspected

Netlify project `remarkable-muffin-a25dc8` (`01ac459c-00de-4660-9558-7fd1a45a8724`) serves https://clock.superiorllc.org. Inspected its open deployment file browser and preserved public assets from deployment `69fbb890a565ad9951a85943` in ignored `.local-recovery/clock-netlify/`. Hashes are recorded in `docs/TIME_CLOCK_RECOVERY_MANIFEST.json`. This is compiled client code, not a complete source/database backup. Netlify lists two deployed functions; their source and server configuration have not been recovered. `netlify.toml` is visible in the deploy browser but unavailable at its public URL (404).

The clock bundle uses Supabase tables `memberships_2`, `profiles_2`, `companies_2`, `company_billing_2`, `job_sites_2`, `work_types_2`, `time_entries_2`, `time_entry_segments_2`, and `gps_markers_2`. This differs from the Core time tracker using `job_titles`, `job_tasks`, and `time_entries`. Do not assume the schemas or identity IDs match.

Observed clock capabilities: company membership and admin/crew access; clock in/out; task segments; Job Site, Setup, Teardown, Travel Time and Other defaults; breaks; recent shifts; job-site administration (active/on-hold/completed); location markers; local offline queue; account confirmation and subscription checkout. The separate recovered Core tracker also contains rate snapshots and export workflows. No production employee data or database credentials were needed or imported.

## V2 implementation

The existing FastAPI workspace now contains a Time clock view sharing its organization, identity, navigation, work-order list, Atlas companion and green/gold/black theme. Reused the standalone clock's task vocabulary, shift/segment/break concepts and history workflow. Reimplemented storage operations server-side rather than copying compiled Supabase calls or deploying another app.

- Both editions can clock themselves in/out, switch tasks, start/end breaks and view paginated personal history.
- A shift may link an accessible V2 work order; its title is snapshotted. Unassigned work is explicitly supported. Job-site administration maps to work orders for this increment; site status/client management is not yet at parity.
- Admins can read team history within their own organization. They cannot clock another employee in/out through this API.
- Server UTC timestamps, transactional commands, unique active-shift constraint, expected versions and scoped UUID retry IDs prevent duplicate active shifts and stale updates.
- `preview_shifts` stores current snapshots; `preview_clock_events` retains command receipts. Task intervals pause during breaks. Clock-out while on break closes the break. Work duration excludes recorded breaks for display only, with no payroll, overtime or wage determination.
- Atlas receives only the current user's saved clock summary, even for admins. Clock controls perform actions; generated replies cannot mutate records. The quick guide works without inference. CPU AI latency remains unresolved.
- Failed/unconfirmed actions retain their retry ID while the page/identity remains active. This is not durable offline synchronization. Refresh/reconcile status after reopening the page; the unique active-shift constraint still prevents a second clock-in.

## Backend independence and production gates

The preview uses the existing ignored SQLite database, not the inaccessible Supabase project. Timekeeping has a dedicated module (`services/workspace_preview/timeclock.py`) and a provider-neutral HTTP contract. A production PostgreSQL adapter/migration still needs implementation and testing; SQLite preview is not a claim of production database readiness.

Do not create a second Supabase project merely to unblock local work. Once the support outcome is known, select recovered Supabase, replacement Supabase, or the planned Google Cloud relational backend. Rehearse schema/data migration, membership mapping, database policies, transactions, backups and recovery before switching writers. Keep original IDs in a migration crosswalk.

Remaining parity/launch work: production sign-in and organization authorization; database adapter; approved time corrections with audit trail; task/site administration; date filters and validated exports; GPS consent/retention and actual accuracy; durable offline queue, timestamp trust and conflict reconciliation; payroll/break/overtime policy and rate snapshots; source/function recovery; billing and employee migration. Never copy the old service worker into the unified app because it may cache stale identity-scoped data.

## Validation

Automated coverage includes exact work/break totals, task segments, clock-out during break, invalid transitions, backwards clock, retry replay/payload conflicts, spoofed employee/timestamp rejection, stale versions, concurrent clock-in, record persistence, history limits, cross-organization access and Atlas context isolation.

Real browser: synthetic Enterprise admin shift linked to Norfolk sample; clock in as Setup, switch to Travel Time, start/end break, clock out, reload. History retained three segments, 31 work seconds and 14 break seconds. No real attendance/payroll records, production deployments, Supabase changes or Netlify changes.

Final validation: 108 automated tests passed, including concurrent clock-in prevention. JavaScript syntax checks passed. Core general browser check showed no Enterprise records or team controls; Atlas quick-guide navigation opened the time-clock view. Generated model time-clock response quality was not retested; scoped context and no-action behavior were verified with test transports.
