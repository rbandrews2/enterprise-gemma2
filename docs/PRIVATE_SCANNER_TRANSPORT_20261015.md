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
