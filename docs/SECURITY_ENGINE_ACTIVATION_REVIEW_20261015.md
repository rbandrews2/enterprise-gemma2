## Current status - October15

Private transport, supervisor and immutable image are implemented; Cloud Build
image gate PASSED. See SECURITY_CUTOVER_20261015.md for current artifacts and
remaining live identity/IAM, schema, vulnerability and rollout gates. Older
implementation-pending statements below are historical. No live scanner activated.

# Next checkpoint: real scanner acceptance and activation

Prepared only; no production engine activated or paid resources provisioned.
Disposable Cloud Shell acceptance now passed; see the latest SESSION_HANDOFF.md.

## Why activation is separate

The application now enforces file holds and records incidents, but it cannot
identify malware without a configured, validated engine. The current adapter
supports an operator-installed local ClamAV CLI or private Unix-socket daemon,
not an authenticated remote scanner service.
ClamAV recommends 3–4 GiB RAM with standard signatures. Do not add it blindly to
the small web container or the user's laptop. Verify measured peak memory and
cold-start/scan durations before selecting a deployment profile. The accepted
ClamAV1.5.4/28154 test measured child peak RSS995716KiB (~973MiB). This is one
synthetic run, not production capacity evidence or a reason to ignore headroom.
Oversized ZIP content was initially reported clean by the engine; the independent
adapter completeness guard now holds it. Other container formats still need review.

## Recommended next work

1. Use a disposable Cloud Shell test directory after the PostgreSQL gate finishes.
   Check available memory, install from the official OS package repository if
   needed, and obtain current official signatures. No customer files or public
   malware samples. Verify benign scanning, a controlled safe detection fixture,
   missing/stale signatures, encrypted/over-limit input and timeout handling.
2. Test the actual application path: upload → durable admin alert/hold → blocked
   member/admin download → admin rescan/release or close-contained → audit history.
   Preserve the original private bytes/hash; closing a case never requires release.
3. Prefer an isolated, private, scale-to-zero scanner for production isolation;
   that requires a reviewed transport adapter, authenticated result contract,
   signature-update mechanism and narrowly scoped invocation identity. The private
   transport and identity-bound result contract are now prepared in source; see
   PRIVATE_SCANNER_TRANSPORT_20261015.md. They are disabled, not live IAM acceptance.
   Signature supervision and isolated image/deployment still need implementation
   and acceptance. The scanner should not inherit database/secret access merely
   because it analyzes an upload. Never send documents to a public scan service.
4. After those tests and deployment review, enable mandatory scanning and backfill
   the existing-file inventory. Publish scanner-coverage status, alert delivery
   expectations and rollback instructions; do not label legacy files clean.

## Cost illustration, not an approved configuration

Google's us-central1 request-based active rates inspected October15 are
USD0.000024/vCPU-second and USD0.0000025/GiB-second. A hypothetical private scanner
at1vCPU/4GiB costs `(0.000024 + 4*0.0000025) = 0.000034` per billable active second,
or USD0.1224 per billable hour, before free allowances. At1000 hypothetical20-second
scans, active compute alone is USD0.68. These are arithmetic examples, not measured
throughput or a monthly quote: cold starts, signature loading/updates, request
charges, builds, image storage, network, logs and existing database costs are extra.
Keep minimum instances0, maximum instances1 and scan concurrency1 for an initial
controlled pilot; validate memory/CPU compatibility and current billing first.
No assumption that free-tier allowance is unused. Budget alerts are not a hard cap.

## Remaining security coverage

Authentication-provider/WAF/infrastructure feeds, browser push and out-of-app admin
alerts, immutable audit retention and restore/incident exercises remain separate
work. Application evidence cannot establish that a phone or laptop is compromised.
No SOC2 certification or comprehensive malware-prevention claim is supported.

Primary references:

- [ClamAV system recommendations](https://docs.clamav.net/)
- [ClamAV container memory guidance](https://docs.clamav.net/manual/Installing/Docker.html)
- [ClamAV scanning controls](https://docs.clamav.net/manual/Usage/Scanning.html)
- [Google Cloud Run pricing](https://cloud.google.com/run/pricing)
