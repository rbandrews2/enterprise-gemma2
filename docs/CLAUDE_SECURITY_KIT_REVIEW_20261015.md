# Claude security kit review - October 15, 2026

## Conclusion

Do not deploy or merge this archive unchanged. It contains a plausible ClamAV
upload-scanning starter, not an installed WZOS V2 threat-monitoring system.
Retain the existing Google-backed WZOS security/tenant contracts and adapt only
reviewed scanner ideas. No runtime code, service settings, IAM, credentials,
customer files, database definitions or production traffic changed during review.

## Artifact and method

Actual download: `C:/Users/MolecularDev/Downloads/security-kit.zip` (15,000 bytes),
not security.zip. SHA256:
`da19cb8a022bdc4807922c22df52658876aef3481d3177680ebae1e24b8b0bd5`.
Archive contains 9 text/source files, no dependency lockfile or automated tests.
Checked entries for path traversal and bounded size before copying into ignored
`.local-data/security-kit-review/security-kit`. Archive remains unchanged.
Inspected all source; ran only isolated, reviewed pure file-type/heuristic functions
with harmless buffers. No npm install, Docker build, scanner/server startup, real
malware fixture or external file upload occurred. Reproduction harness:
`.local-data/security-kit-review/probes.cjs` (ignored local evidence).

## Verified service state

- Supabase MCP read-only metadata query against the exact project referenced in
  README (`social-highway-network`, ref ebzfbuqclkumncnugbvq): no security_events
  table, report_security_event function, any of the three threat views, or either
  quarantine/uploads bucket exists. This is not evidence of an applied migration.
- Chrome Render dashboard: R.'s workspace contains Data Matrix (data-matrix,
  superior-starter-api, superior-property-api), AIRA AI Receptionist
  (AIRA-WEB-SERVICE), superior_checkout_app (checkout), and ungrouped superior-api.
  No dedicated scanner service appeared in those project/environment inventories.
  This does not rule out other workspaces or scanner code inside another service;
  no deployed scanner endpoint or engine health result was supplied/verified.
- Netlify r-andrews project list: workzoneos/app.superiorllc.org shows last published
  May 8, 2026. Other visible sites: road-crew-connect, AIRA, workzoneos.org and clock.
  No newly published scanner frontend was evidenced. Did not inspect secrets or
  rewrite V1. Netlify connector failed after auth; used the existing Chrome tab.
- Render connector required a workspace choice; did not guess/change MCP workspace.
  Browser read-only inspection used the workspace already open for the user.

## Blocking findings

1. **Wrong integration boundary / missing tenant authorization.**
   README1-4; server.js167-178; secureUpload.ts6,35-55; SQL9-17,43-69.
   Supabase JWT/auth.users/user-folder ownership and service-role storage replace
   rather than integrate with current Firebase authentication, GoogleFiles,
   organization membership and licensed admin/member controls. No organization_id
   or membership recheck is present. Same user across organizations is not scoped.
   Reuse WZOS backend authorization and immutable SHA256 revision/file state.

2. **No alert-first response or retained quarantine evidence.**
   server.js108-116,186-197,206-209,224-236; README39-43.
   Detection writes a log (failure is swallowed), deletes rejected/infected files,
   and returns JSON. No admin notification fan-out, incident review, audit reason,
   restore flow or held-file retention exists. Removal errors are ignored. Three
   malware events automatically block scans globally for that user, without an
   organization review workflow; unscanned uploads can still enter quarantine.
   Map verdicts into existing durable incidents/holds and notify admins. Retain
   original evidence; use explicit reviewed recovery instead of silent deletion.

3. **Incomplete scan can be treated as healthy/clean.**
   start.sh5-6; Dockerfile13-16; server.js100,155-160.
   Startup allows signature refresh failure; /health only checks PONG, not signature
   age. A bare OK becomes clean. No explicit AlertExceedsMax/AlertEncrypted policy
   or scan completeness/version/hash evidence is required. Existing resource limits
   do not establish that every nested/encrypted member was inspected. Require fresh
   signatures and explicit suspicious/limit/error holds. PONG is process readiness,
   not security acceptance. Also fix Docker RUN: the trailing `|| true` on the
   multiline && chain can mask earlier setup errors, not just freshclam failure.

4. **Confirmed type-validation defects.** server.js35-53,56-65.
   Both DOCX and XLSX use isZip; find() always selects DOCX first. Reproduction:
   ZIP header named sheet.xlsx => extension mismatch, always rejected; same six-byte
   non-document header named fake.docx => accepted as DOCX. Validate OOXML package
   contents, lengths and supported formats. Plain-text PDF regex catches /JS but
   misses /J#53; this proves only heuristic incompleteness, NOT a ClamAV bypass.
   The production allowlist must match WZOS's supported file types.

5. **Resource/abuse limits are incomplete.** server.js73-81,88-98,124-132,186-204.
   Entire blobs are downloaded/buffered before size rejection; no bounded concurrent
   scan queue/download deadline; rate state is per-process and user keys never
   expire from Map. Failed/missing-file retries consume quota; invalid-path logging
   happens before rate limiting. Concurrent requests can race the three-hit check.
   Use authenticated backend requests, bounded payload/queue/time, replay-safe IDs,
   durable shared admission policy and tenant/user quotas before expensive work.

6. **Client reports are untrusted and minimally constrained.**
   SQL74-114; security.ts8-40. Anonymous SECURITY DEFINER RPC accepts arbitrary JSON,
   strips only a top-level password field, and derives IP from forwarded headers.
   COUNT-then-INSERT is not an atomic rate gate. Client login events can be fabricated
   or omitted; localStorage lockout is bypassable. No payload field-size allowlist,
   trusted auth-provider events or secret-safe structured schema is enforced. Do not
   interpret this telemetry as verified compromise; use provider/server evidence.

7. **Not a drop-in hardened deployment.**
   frontend/public/_headers12 has YOUR-SCANNER placeholder, old origins and a CSP
   missing current Google Maps/Firebase/Daily requirements; replacing current policy
   would break integrations. Broad preexisting Supabase policies are not audited or
   removed by this migration, so added restrictive policies alone do not prove
   exclusive bucket access. Existing bucket names would be changed on conflict.
   Service-role key has broad database/storage authority. Dependencies use caret
   ranges without a lockfile; container has no explicit non-root app user. Review
   least privilege, dependency locking, existing policies and isolated engine runtime.

## What is useful

Private staging-before-promotion, server-side validation, ClamAV INSTREAM transport,
explicit loopback daemon binding and withholding downloads on scanner errors are
useful starting concepts. Keep the engine behind the current WZOS backend, without
Supabase service-role credentials or a second account/storage authority. The
existing scanner adapter already enforces fresh signatures, bounded work and
reviewed holds, but its real-engine acceptance remains open.

## Next implementation sequence

1. Keep current WZOS security source c4a8b5f and its 651 Python/PostgreSQL +108 Node
   accepted tests as the baseline (not a claim that this kit passed those tests).
2. Validate real ClamAV in disposable cloud testing with fresh signatures and safe
   vendor test fixtures; do not enable client-download release on PONG alone.
3. If a warm daemon is required, implement a private authenticated scanner adapter,
   byte/hash correlation, bounded concurrency and structured verdicts. Preserve
   existing org auth, incident persistence, storage holds and audited recovery.
4. Test stale signatures, limit/encryption cases, engine failure, concurrency,
   replay/idempotency, membership revocation, tenant leakage and legacy backfill.
5. Review cost/resource/IAM/schema/rollback implications before deployment. No
   Render/Supabase/Netlify provisioning or migration is needed just to adopt ClamAV.

Official reference checked: https://docs.clamav.net/manual/Usage/Scanning.html
ClamAV documents daemon/signature requirements, TCP isolation and scan-limit
caveats. The Supabase changelog.md request returned unsupported content type;
no Supabase implementation change was made based on assumed API behavior.
