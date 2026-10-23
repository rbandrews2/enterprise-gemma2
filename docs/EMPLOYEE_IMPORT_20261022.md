# Employee CSV import

Admin-only Organization management action: template, UTF-8 CSV upload, row review,
then explicit confirmation. Applies to both editions; never grants membership,
consumes a licensed login, sends invitations or changes existing employee records.
Required columns: name, email, employee_number. Optional: phone (international +).
Maximum 500 rows / 512 KiB. All rows must be valid before confirmation; duplicates
are visibly skipped. Imported roster records remain organization-private. Existing
account membership/invitation and licensing checks remain authoritative.

## Additive database change / rollback

Reviewable SQL: [employee-import-additive.sql](employee-import-additive.sql).
DDL lives in services/workspace_preview/employee_import.py: employee_roster stores
normalized imported employee records; employee_import_batches stores actor-scoped,
30-minute reviewed candidates and their roster/member fingerprint for confirmation.
No raw CSV retention. Unique organization/email and organization/employee-number
constraints. Confirmation locks the organization row, rechecks admin access and
the fingerprint, and commits all additions plus the receipt atomically. Repeated
confirmation returns the same receipt. Batch records expire after 30 minutes;
confirmed receipts remain until a later review clears expired batches. Audit
records contain the batch ID only; counts are kept in the receipt. No employee
names, emails or phones are placed in request URLs or application audit targets.

Rollback: disable the import entry point/routes by rolling back application code;
leave both additive tables intact. Older code ignores them. No existing schema
columns/data are rewritten. This is a roster import, not account provisioning;
admins use Team access separately when ready to invite employees.

## Validation

- Eight new import API checks PASS on local SQLite, covering admin/member and
  tenant denial, Core support, pagination, duplicate emails/numbers, invalid CSV,
  BOM, row limits, explicit confirmation, expiration/staleness, atomic error
  blocking, repeat receipts and unchanged memberships/invitation count.
- Eight existing employee regression cases PASS. Combined initial run:
  15 cases/88.032s, zero skips; added Core/pagination case passed separately
  in5.830s. Seven initial import checks were rerun once with employee regressions;
  do not count that repeat as extra coverage. Total16unique backend checks.
- Existing account UI/auth suite:26Node checks PASS, zero skips. Changed
  employees/organization scripts pass Node syntax checks.
- Local browser: upload three synthetic rows, display2ready/1duplicate, require
  review checkbox before confirmation, import2/skip1 and show visible receipt;
  no invitations sent. Screenshot outside Git:
  .local-data/employee-import-browser.png. Isolated test harness on loopback8084,
  synthetic verifier/data only. It adapts the fixed local-preview Host allowlist;
  does not change production security headers. Embedded narrow preview was
  correctly blocked by existing frame protections; true mobile-width acceptance
  remains open. No production protection was relaxed for that test.
- Code review caught the dashboard fetch-options/account-body helper mismatch;
  dashboard adapter now supplies POST/JSON explicitly. Account menu and employee
  directory use their existing account helper.
- PostgreSQL additive-schema/integration acceptance and integrated mobile view
  remain OPEN. Cloud Shell control returned stale-page errors on two attempts;
  no cloud tests, live data writes, provisioning or deployment were performed.
  Full exact-candidate release gates still apply before a later deployment.

Local raw backend log: .local-data/employee-import-tests.log. Preserve these
passing results; do not repeat unrelated Voice/Speech/SMS/model or payment tests.
The user message ended with an unfinished additional-name request; clarification
was requested. The implemented label stays **Import employees** meanwhile.
