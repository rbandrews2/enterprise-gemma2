# Day and night inspections and employee qualification wallets

This candidate branches from `codex/preproduction-modules` at `e28d55a`.

## Crew workflows

Open **Day and night inspections** from the workspace navigation. Choose an accessible work order, closure, date, and shift. Schedule one check per device or route segment and identify its location. The inspector records an observation and either passes the item or names a repair owner. Closing a defect requires a recheck note and photo. WZOS records the inspector, rechecker, and timestamps.

Enterprise users with full report access to the work order can save a dated report to the existing Work Zone Report archive. It includes checks due on the chosen date, earlier outstanding defects, and repairs rechecked on that UTC date. The PDF contains a thumbnail. The inspection retains the larger photo. Dispatched crew members can update assigned inspections under the existing active-assignment access rules.

Open **My qualification wallet** to list credentials, add a qualification, or upload front and back photos. A member's submission starts unreviewed. Organization admins review qualifications from Employees. Dispatch uses the existing qualification review and expiry records. Photos are private to the employee and their organization's admins. Each side accepts one JPEG, PNG or WebP up to 1 MiB. The server validates the image, strips metadata and stores a resized JPEG. A renewal can be submitted as a separate qualification so the original evidence remains available.

## Database and release

Startup creates two additive tables. Review the SQL in `services/workspace_preview/field_inspections.py` (`DDL`) and `services/workspace_preview/employees.py` (`DDL`). The composite keys scope inspections to an organization and order, and certificate photos to an organization, employee, qualification and side. Both tables contain private field records. Existing qualifications and report snapshots are readable without backfill. The older app can run against the expanded schema. A rollback should preserve both tables and existing report snapshots.

Browser acceptance used mobile-sized Chrome and a synthetic member on loopback. It covered uploading and reopening a wallet photo, scheduling and recording a night check, confirming a repair with a photo, and archiving the report. Targeted tests cover member and organization boundaries, status transitions, retries and PDF export. Run the full integration and deployment gates before a shared release.
