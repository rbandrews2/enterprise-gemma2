# Atlas Security: implementation and response protocol

## Scope and boundaries

This increment adds organization-scoped incidents, durable admin alerts, audited
containment, repeated known-user denied-request signals, and a file-scanner boundary. It is application protection, not an
endpoint antivirus, device-compromise detector, SOC2 certification, or a claim
that an absence of alerts means the system is secure. Atlas explains bounded
server facts; model text cannot authorize containment or mark a file clean.

## Response protocol

1. Persist the incident and its admin notification before returning the affected
   request. The dashboard and persistent admin banner surface it; open admin tabs
   poll once per minute and refresh when made visible. A closed app
   does not receive browser push, email or SMS in this increment.
2. Hold scanner-positive files and files whose integrity fails immediately;
   preserve their private originals and hashes. When scan enforcement is enabled,
   pending/unscanned files cannot be downloaded. Do not transmit files to public
   scanning services or include their bytes in model context.
3. Admins acknowledge, investigate evidence and record reasons. They may quarantine
   a file, suspend an organization member, or revoke an integration credential.
   Automatic user suspension is not triggered by an AI guess. Preserve another
   active admin; prevent self/last-admin suspension. Other organizations remain
   unaffected. Existing provider calls already in progress cannot be recalled.
4. File release requires a recent clean scan of the preserved hash and explicit
   admin review. Scanner errors, missing signatures or unavailable engines never
   become clean results. User restoration requires explicit review and available
   licensed capacity. Resolving an incident does not silently undo containment.
5. Keep an append-only action trail, verify recovery, and resolve the incident.
   Notify the platform operator separately for app-wide incidents or last-admin
   compromise. No destructive deletion, firewall changes or account-wide Google
   revocation is automated here.

## API and startup schema review

New `security_incidents`, `security_actions`, `security_file_states` and
`security_alert_reads` tables plus three lookup/rate/audit indexes are defined in
`services/workspace_preview/security.py:DDL`. Startup applies additive DDL;
deployment is a migration and requires PostgreSQL validation and schema review.
No existing row is rewritten at startup. Retain the tables on rollback; older
code does not enforce these holds, so rollback must retain security enforcement
or disable file delivery and affected memberships first.

Admin-only, tenant-scoped routes: GET `/api/admin/security`, GET
`/api/admin/security/summary`, POST `/api/admin/security/reports`, POST
`/api/admin/security/incidents/{id}/actions`. Bounded request bodies, pagination,
optimistic incident versions and audited reasons are required. There is no
public scanner-result or autonomous model-action endpoint.

## Scanner activation

`WZOS_FILE_SCAN_REQUIRED=1` blocks new and legacy files without a clean scan.
Without this opt-in, existing unscanned files retain their previous download
behavior and are visibly marked unscanned; explicit quarantine always blocks.
`WZOS_CLAMSCAN_PATH` must point to an operator-installed absolute ClamAV binary.
The adapter checks the signature database age and uses stdin, no shell, bounded
execution time, and no raw scanner output in responses. Missing/stale signatures
or scanner errors hold files when scanning is configured. No scanner is installed
or cloud service provisioned by this source change. Production activation requires
fresh-signature updates, resource/concurrency sizing and controlled engine tests.

## Evidence and remaining acceptance

Record actual tests in the session handoff. Cloud PostgreSQL, actual scanner,
multi-admin/device notification and deployment checks remain gates until run.
No customer messages or changes to production permissions are authorized here.

References: [OWASP File Upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
and [NIST SP 800-61r3](https://csrc.nist.gov/pubs/sp/800/61/r3/final), plus
[ClamAV scanning](https://docs.clamav.net/manual/Usage/Scanning.html) and
[signature updates](https://docs.clamav.net/manual/Usage/SignatureManagement.html).

Known-user signals count five HTTP403/429 results within one minute, deduplicated
per user/hour. Only an actor already verified against an active membership is
attributed to an organization; forged org headers and failed unauthenticated
logins cannot create an incident against a guessed tenant. No request bodies,
URLs, tokens, IPs or device identifiers enter these signals. This is not a
replacement for perimeter/WAF, authentication-provider or infrastructure alerts.
File bytes never enter Atlas context. Security questions use trusted count/status
guidance without a model call, reducing latency and avoiding invented containment.
