# Employee directory and qualification contract

October 9, 2026. Implemented candidate in `codex/integration-release`; no cloud
deployment. This is the shared foundation for Claude's dispatch/training work.

## Scope and permissions

Uses existing verified Google identity, organization membership and SQLite/
PostgreSQL interfaces. Every employee is an existing organization member; profile
creation does not create an authentication account. Both editions support employee
records. Dispatch planning remains an independent Enterprise-only entitlement.

Admins list and update employees only within their organization. Members read
only their own profile, qualifications and history. Disabled members cannot sign
in to read these records; admins can still maintain their historical records.
Home addresses and phone numbers are excluded from directory listing and the
existing public-to-team roster. No employee data is added to Atlas context.

## API for Claude

- `GET /api/account/employees?offset=0&limit=25`: admin-only member directory;
  maximum page size50. Items carry id/name/activity/employee number/profile version.
- `GET /api/account/employees/{user_id}`: own/admin profile and qualifications.
- `PUT /api/account/employees/{user_id}`: admin profile write. Required
  expected_version (0 for creation), employee_number; optional address, phone,
  starting_location and notes. Numbers normalize to uppercase and are unique per
  organization. Optional phone is international E.164-shaped input, not verified
  contact or consent to messaging.
- `PUT /api/account/employees/{user_id}/qualifications/{qualification_id}`:
  admin-only versioned qualification write. Identifier is stable,1–80 ASCII
  letters/digits/underscore/hyphen. Include title, issuer, credential_number,
  issued_on/expires_on (ISO dates or null), review_status, evidence_reference,
  review_note and expected_version.
- `GET /api/account/employees/{user_id}/history`: own/admin paginated immutable
  snapshots with actor and saved time, maximum50 per page.

Writes return409 on stale/conflicting versions. Repeating an identical write with
its immediately previous expected version returns the saved result without a new
history row. Unknown/cross-organization targets return404. No delete API is added;
rejected qualifications retain history instead of disappearing.

Qualification states: unreviewed, rejected, expired, verified_current,
verified_expiry_unknown. Verified writes require issuer, evidence reference and
review note. Evidence references are text identifiers: attachments and independent
agency verification are not implemented by this increment. Missing expiry never
establishes that a credential is perpetual. Expiry dates are valid through the
specified UTC date; dispatch must evaluate at the job date and apply its actual
qualification requirements. `qualification_state(payload,on_date)` is the shared
pure status helper; it does not determine job eligibility or issue certifications.

Dispatch must also check membership activity, availability, work-order requirements
and current profile/qualification revisions. Do not send home addresses/evidence
references to coworkers, external messages or model context. Training completion
alone must not silently grant verified qualifications.

## UI

Authenticated account toolbar exposes Employees to admins and My employee record
to members. Admins edit profiles and qualifications; members see read-only records.
The editor protects unsaved changes, reports save failures and paginates the list.
It reuses existing account dialog styling and text-only rendering of user content.

## Startup DDL and rollback

New startup tables: employee_profiles, employee_qualifications, employee_history.
Review SQL in migrations/20261009_employee_directory.sql. Deploying this branch
applies these CREATE TABLE IF NOT EXISTS statements. Existing account/roster schema
is unchanged. Older code ignores these tables; rollback code without deleting data.
No migration has been applied to shared cloud databases. PostgreSQL and browser
acceptance are required before integration/deployment. Availability inputs,
evidence uploads, external recovery/invitation delivery and entitlement lifecycle
remain subsequent work; no dispatch engine or external communications are enabled.
