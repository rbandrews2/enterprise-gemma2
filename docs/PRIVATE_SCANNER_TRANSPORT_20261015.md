# Private scanner transport preparation

Prepared in source only. No service, IAM grant, secret, customer send or production
configuration is created by this increment. Existing local scanner behavior is
unchanged unless an operator explicitly configures `WZOS_SCANNER_URL`.

## Proposed internal contract

Separate Cloud Run service with its own identity and **no database, bucket or
Secret Manager grants**. Cloud Run IAM must require the WZOS caller identity with
service-scoped `roles/run.invoker`. The application independently verifies the
Google-signed token audience and exact caller service-account email. No browser
access, cookie/session authentication, customer-selected URL, public scan service
or application-user identity is accepted. The daemon remains a private Unix socket
inside that scanner workload. This isolates cloud authority, not an OS sandbox
between the scanner wrapper and engine; container/engine hardening remains review.

`POST /scan`: raw application/octet-stream, 1..10MiB, exact Content-Length,
X-Scan-Request (UUID) and X-Content-SHA256. Reject content encoding and mismatches.
Reply contains exactly version=1, request_id, sha256, byte_count, status and engine.
The caller rejects mismatched identifiers/hashes/sizes, invalid status, malformed
or oversized JSON, redirects, HTTP errors and absent identity. No retries or file
names; no uploaded bytes, bearer tokens or raw engine output in response/logs.
Timeouts and unsupported archives retain existing durable file holds/incidents.

Server configuration: `WZOS_SCANNER_AUDIENCE` (its exact HTTPS run.app origin),
`WZOS_SCANNER_CALLER` (one trusted service-account email), and existing private
daemon socket/config. Caller configuration: `WZOS_SCANNER_URL` (same origin).
Partial/invalid remote configuration never falls back to a local engine.
Health endpoint is liveness only; each scan still verifies engine/signature freshness.
No schema changes. All existing tenant/admin/member/release checks remain in WZOS.

Entrypoint for the future isolated image (not the workspace account app):
`uvicorn services.workspace_preview.scanner_service:create_app --factory --host 0.0.0.0 --port 8080`.
This factory does not launch/download the engine or definitions: starting it alone
is not a complete scanner deployment. Reuse the repository's pinned dependencies;
Google identity helpers import only when used. Do not include account credentials,
the workspace data directory, source-document originals or recovery artifacts in
the scanner image/build context. Access logs must never include authorization
headers or request/response bodies.

Focused command: `python -m unittest tests.test_scanner_transport -v`.
These tests use synthetic Google claims and HTTP transports; they establish
contract behavior, not live certificate/metadata/IAM verification. The inherited
security integration test runs against SQLite and the full PostgreSQL gate.

### Bounds and failure semantics

The caller permits one active scan per web process. Identity HTTP operations use
five-second timeouts; scanner HTTP connect timeout is five seconds and other I/O
timeouts are thirty seconds. A verdict arriving after the 35-second acceptance
window is discarded. That window is not hard cancellation of an in-progress
blocking socket operation: an I/O timeout may finish later. There are no automatic
retries. The receiving service admits one request at a time, bounds upload reading
to five seconds and delegates engine work to the existing bounded adapter.
Cloud deployment must additionally cap instance count/concurrency and request
timeout; per-process admission is not a distributed rate limit.

An engine error retains the existing pending/hold behavior and durable admin
incident. Explicit admin quarantine survives a later clean rescan and requires a
separate reviewed release. This increment does not change the existing distinction
between pending scans and explicit quarantine, nor implicitly approve old files.

### Image and signature-supervisor implementation and open acceptance

Source now includes Dockerfile.scanner, requirements-scanner.txt, scanner_runtime.py
and scripts/test_scanner_image.sh. Not deployed; image acceptance is separate
from unit/regression tests. The runtime refreshes official definitions at boot
within 75 seconds, shares a 210-second boot allowance, validates a benign scan
before starting HTTP, and reserves one hour before the 24-hour signature limit.
It caps instance scan lifetime at20 hours. The next authenticated scan after
expiry returns error-held and requests worker recycling; a subsequent cold start
refreshes definitions. No timer-based idle updater or silent fallback is assumed.
This design can produce a transient scan failure during recycling/cold starts;
live cold-start latency and operational behavior still require acceptance.

- Use an immutable reviewed image, non-root foreground processes and a private
  mode700 working directory/socket. Keep the raw engine off TCP. Start HTTP only
  after the engine has loaded verified, current official signatures.
- Provide a verified signature seed and a bounded refresh step. Do not disable
  CVD certificate verification or persist unsigned definitions. Any network,
  certificate, database-test or signature-age failure must prevent readiness.
- Do not depend on idle background CPU for updates in a request-billed service.
  Select and test an explicit refresh/restart strategy before enabling traffic.
  Reject stale signatures on every scan even if an updater misses its deadline.
- Bound startup to the platform startup allowance, and size peak RSS for loading,
  refresh and scanning together. The prior ~973MiB sample did not measure all
  update/reload peaks; the web container's 512MiB configuration is unsuitable.
- Supervise engine exit and updater failure, stop the owned process on SIGTERM,
  and leave no orphan listener, original upload or file-derived temporary path.
  Engine failure must not trigger a clean/optional-scanner fallback.
- Test stale seed, broken certificates, network failure, interrupted refresh,
  engine crash, concurrent scans, shutdown, restart and max memory before rollout.
- Retain last accepted security-capable image/config for rollback. Keep holds and
  incident data intact, keep scanning mandatory where activated, and return scan
  errors if the prior scanner is unavailable. Never silently disable the gate.

## Activation still required

1. Accept contract and caller/service account isolation tests, including real
   Cloud Run Google identity; local mocks are not live identity acceptance.
2. Prepare/review immutable scanner image, non-root process supervision, bounded
   verified signature bootstrap/refresh and stale/update-failure health behavior.
   Request-based CPU cannot be assumed available for a background updater.
3. Verify current billing; review bounded resource configuration and rollback.
4. Provision only with explicit approval for new service and service-scoped IAM.
   No public invoker; no customer documents in the first acceptance exercise.
5. Validate end-to-end synthetic upload/incident/hold/recovery before enabling
   mandatory scanning and reviewing/backfilling existing files. Rollback must
   preserve holds; never fall back to a pre-security image that ignores them.

References: [Google service-to-service authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service),
[Cloud Run container contract](https://docs.cloud.google.com/run/docs/container-contract).
