# Assigned jobs and Time Clock

This increment grants an Enterprise employee permission to link their own time
to an active (`sent` or `accepted`) assignment in their selected organization.
It uses only the frozen dispatched title. It does not grant original work-order
read/edit, private report/file access, another employee's time access, or receipt
confirmation. Admin and creator-owned job access remains unchanged.

`GET /api/time/jobs` returns bounded, paginated selectable job IDs/titles, with
`access_basis` distinguishing existing work orders from dispatched summaries.
Assignments must belong to a sent plan and the current employee/organization.
Declined, cancelled and replaced assignments cannot authorize a new punch or
offline submission. Existing shifts remain closable after cancellation.
Historical active assignments remain linkable for explicit offline reconciliation;
assignment times are not an attendance restriction or proof of attendance.
Legacy plans without a frozen title cannot authorize this additional access.

No DDL, provider calls or work-order permission changes. PostgreSQL and browser
acceptance remain separate release gates.
