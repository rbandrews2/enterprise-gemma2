# Atlas explicit cancellation — October 2, 2026

## Implementation

The browser supplies a UUID per reply. Authenticated POST `/api/assistant/requests/{id}/cancel` and GET `/api/assistant/requests/{id}` use the same identity, organization and origin boundaries as chat. Only the originating user in the originating organization can stop/read a request; admin does not override that ownership.

A shared database table stores identifiers, state and expiry only—no prompts, replies or tokens. PostgreSQL staging and local SQLite use the existing storage boundary. Cancellation is durable across application instances. The generating instance polls every 0.5 seconds without holding a transaction during inference; confirmed cancellation cancels its task, closes its upstream transport and releases its local request gate. Provider/GPU stop is always reported as unverified.

Records expire logically after ten minutes and are removed on subsequent state-changing calls. A per-user/organization limit of 64 unexpired records bounds rapid repeated calls. Duplicate IDs cannot replay inference within that retention window. A cancellation arriving before the original request records a stop intent; the later request returns 499 without starting inference. A 300-second outer deadline bounds application work; terminal races do not turn a cancellation into a successful reply.

The browser preserves the original identity/organization headers, sends stop through a separate request, and waits up to eight seconds for acknowledgement before aborting its own transport. Failed acknowledgement is shown as unconfirmed. Context switches use the same stop path. No inference retries or automatic writes to work orders are introduced.

## Local validation

- Two independently constructed app instances sharing a database: stop via the other instance; owner/admin/tenant checks; cancelled state; subsequent recovery; duplicate denial.
- Stop before registration: idempotent and zero provider calls.
- Deadline and provider failure: task cleanup, released gate and terminal failure.
- Real loopback HTTP: explicit cancellation closes the actual provider socket even when the client connection stays open; next request succeeds. Synthetic provider only.
- Browser-function tests: captured scope, acknowledgement, failed cancellation, already-aborted input, listener cleanup.
- Full Python suite: 206 total, 190 passed, 16 PostgreSQL-dependent skips. All eight existing and new Node tests passed. Real-model acceptance remains a separate gate.

## PostgreSQL validation

All five cancellation tests also passed against a disposable schema in the actual staging PostgreSQL database (24.155 seconds). This includes two independently constructed application instances sharing the database. The schema was removed in the test cleanup. This establishes shared PostgreSQL behavior; it does not establish routing across multiple live Cloud Run instances.

## Staging procedure

Refresh auth and cumulative approved trial usage. Sync enterprise-v2; build with the preserved scoped source snapshot. Deploy restricted accounts service, preserve private IAM and configuration. Prepare new disposable managed-account fixtures and a fallback cleanup guard. Enable the existing approved private full-size inference configuration only for the bounded trial.

Run `scripts/validate_atlas_cancellation_staging.py --state PRIVATE_FIXTURE_PATH --output NEW_EVIDENCE_PATH`. It tests pre-start cancellation and unauthorized callers without inference, then at most one cancellable attempt and one recovery reply. It checks unchanged saved orders and records application cancellation separately from provider stop and cross-instance cloud routing. If the reply finishes before cancellation, record inconclusive, never claim success or loop automatically.

Finally disable Atlas, delete trial inference, disable/revoke synthetic identities and organizations, stop helpers, verify cleanup, and record actual results. Multi-instance behavior is locally verified; a live test routed to one instance is not proof of cross-instance cloud routing. Model stop, true cold start, capacity and cost-per-workflow remain open unless separately evidenced.

## Live result

Implementation commit `aff4cd328d57` was built with the preserved scoped source snapshot. Cloud Build `a1691200-dcca-4382-a9cc-3be6a5e708d9` succeeded; initial application deployment `00019-nlp` served the new image with Atlas disabled.

Preflight cumulative monitored inference time was 3,060.471 seconds, approximately $2.712 compute at the previously recorded rate (excluding builds, storage and billing lag). Token lifetimes passed before a 20-minute fallback guard and the existing approved private full-size model configuration were started.

The bounded live run passed on app revision `00020-5z4` and private inference revision `00001-rt6`:

| Check | Actual result |
| --- | --- |
| Other admin cannot cancel member reply | HTTP 404 |
| Other organization cannot cancel | HTTP 403 |
| Cancel before request starts | HTTP 499; no inference |
| Explicit cancellation | HTTP 499 in 0.646 seconds |
| Immediate next real-model reply | HTTP 200 in 2.292 seconds; model_called=true |
| Saved orders | Unchanged; no actions performed |

Cancellation request UUID: `138db281-e03c-4456-a969-8d2676dd73eb`. Sanitized results are preserved in `knowledge/atlas-cancellation-20261002.json`; original JSONL and logs remain under `/home/admin_/wzos-evidence/cancel-*20261002*`.

**Accepted:** explicit application cancellation and immediate recovery for this bounded case. **Not established:** GPU generation stopped, routing across multiple live Cloud Run instances, cold-start performance, sustained capacity, or production readiness. Shared-state behavior was separately tested with two apps against real PostgreSQL.

Cleanup deployed app revision `00021-fkf` with Atlas disabled, deleted the trial inference service, and disabled/revoked synthetic users and organizations. Fresh service reads verified Ready=True, Atlas=0, and an empty inference-service listing. Fixture state confirmed disabled. The SQL proxy and fallback guard were stopped only after those checks. V1, public DNS and production were unchanged.

Post-cleanup monitoring at 23:22:52 UTC reported cumulative inference time 3,360.475 seconds with no further pages: approximately $2.978 compute, about $0.266 above preflight. This excludes builds/storage and may lag final billing; recheck before another trial.

Next checkpoint: true scale-from-zero and cost/latency validation, followed by capacity and model-quality gates. No further inference runs are scheduled by this document.
