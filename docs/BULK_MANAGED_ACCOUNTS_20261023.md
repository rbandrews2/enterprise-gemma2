# Bulk employee accounts

Admin-only CSV / XLSX upload and spreadsheet paste, preview then explicit creation.
Reuses managed account provisioning, organization locks, licensed-seat checks,
Google identity refusal for existing emails and first-login password change.
Invitations remain optional. No customer messages are sent.

API: `/api/account/managed/bulk/review` and `/bulk/create` accept an in-memory
upload and batch UUID. Creation runs at most five rows per request. Stable
per-row request UUIDs allow retry after an interrupted response without resetting
passwords or duplicating accounts. Results are per row; partial success is explicit.
Review is advisory: permissions, existing identities and seats are rechecked on
each creation. No all-or-nothing claim across Google and the app database.

No schema migration, new IAM, secrets or dependencies. Existing managed-account
tables provide durable idempotency. Uploads/passwords are not stored in the app
database, browser storage or receipts. Responses omit passwords and are no-store.
Closing the dialog or changing session clears the upload. Reloading loses the
in-memory batch; reserved incomplete identities may need support recovery.

Accept UTF-8 CSV, tab-separated spreadsheet paste, or a single worksheet XLSX.
Limit 500 employees, 1 MiB input, 8 MiB uncompressed XLSX, 200 ZIP members.
Reject formulas, macros, external links, XML entities and oversized sheets.
Required columns: name,email,username,password,role (admin/member only).
Recognize ACCESS LEVEL as role; original POSITION,COMPANY_ID,TELEPHONE columns
are explicitly ignored. Imported account identity is scoped to the signed-in
organization, never COMPANY_ID. Roster import remains a separate operation.

Release acceptance: focused parser/API/UI tests, PostgreSQL and Node gates,
synthetic browser review. No real account provisioning in automated tests.
Rollback previous application image; existing accounts remain usable.
