# Atlas explicit cancellation — October 2, 2026

## Implementation

The browser supplies a UUID per reply. Authenticated POST `/api/assistant/requests/{id}/cancel` and GET `/api/assistant/requests/{id}` use the same identity, organization and origin boundaries as chat. Only the originating user in the originating organization can stop/read a request; admin does not override that ownership.

A shared database table stores identifiers, state and expiry only—no prompts, replies or tokens. PostgreSQL staging and local SQLite use the existing storage boundary. Cancellation is durable across application instances. The generating instance polls every 0.5 seconds without holding a transaction during inference; confirmed cancellation cancels its task, closes its upstream transport and releases its local request gate. Provider/GPU stop is always reported as unverified.

Records expire logically after ten minutes and are removed on subsequent state-changing calls. A per-user/organization limit of 64 unexpired records bounds rapid repeated calls. Duplicate IDs cannot replay inference. A cancellation arriving before the original request records a stop intent; the later request returns 499 without starting inference. A 300-second outer deadline bounds application work; terminal races do not turn a cancellation into a successful reply.

The browser preserves the original identity/organization headers, sends stop through a separate request, and waits up to eight seconds for acknowledgement before aborting its own transport. Failed acknowledgement is shown as unconfirmed. Context switches use the same stop path. No inference retries or automatic writes to work orders are introduced.

## Local validation

- Two independently constructed app instances sharing a database: stop via the other instance; owner/admin/tenant checks; cancelled state; subsequent recovery; duplicate denial.
- Stop before registration: idempotent and zero provider calls.
- Deadline and provider failure: task cleanup, released gate and terminal failure.
- Real loopback HTTP: explicit cancellation closes the actual provider socket even when the client connection stays open; next request succeeds. Synthetic provider only.
- Browser-function tests: captured scope, acknowledgement, failed cancellation, already-aborted input, listener cleanup.
- Full Python suite: 206 total, 190 passed, 16 PostgreSQL-dependent skips. Existing and new Node tests are also run. Live PostgreSQL and real-model acceptance remain separate gates.

## Staging procedure

Refresh auth and cumulative approved trial usage. Sync enterprise-v2; build with the preserved scoped source snapshot. Deploy restricted accounts service, preserve private IAM and configuration. Prepare new disposable managed-account fixtures and a fallback cleanup guard. Enable the existing approved private full-size inference configuration only for the bounded trial.

Run `scripts/validate_atlas_cancellation_staging.py --state PRIVATE_FIXTURE_PATH --output NEW_EVIDENCE_PATH`. It tests pre-start cancellation and unauthorized callers without inference, then at most one cancellable attempt and one recovery reply. It checks unchanged saved orders and records application cancellation separately from provider stop and cross-instance cloud routing. If the reply finishes before cancellation, record inconclusive, never claim success or loop automatically.

Finally disable Atlas, delete trial inference, disable/revoke synthetic identities and organizations, stop helpers, verify cleanup, and record actual results. Multi-instance behavior is locally verified; a live test routed to one instance is not proof of cross-instance cloud routing. Model stop, true cold start, capacity and cost-per-workflow remain open unless separately evidenced.

## Live result

Pending deployment and bounded validation.
