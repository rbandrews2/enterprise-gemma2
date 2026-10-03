# Atlas waiting and concurrency preparation

## Local changes

- Waiting notices at request start, 15s, 60s and 150s explain possible startup
  delay without claiming measured progress or active generation. Completion,
  cancellation and context changes stop the notices. No additional network calls.
- Reliability acceptance now rejects timeout/provider-error HTTP503 responses;
  only successful model replies or explicit busy rejections are acceptable, with
  at least one successful reply. Every request receives a distinct request ID.
- `validate_atlas_reliability_staging.py --concurrency-only` sends only the two
  concurrent requests, avoiding another cancellation/recovery sequence. This
  two-request sample is not sustained-capacity acceptance.

## Validation

Python: 219 total, 203 passed, 16 PostgreSQL tests skipped without a configured
test database. Node: 13 passed. JavaScript syntax and diff checks passed.
Tests verify late timer suppression after completion/abort, already-aborted
signals, accepted/rejected concurrency combinations, exactly two outbound chat
requests, distinct IDs and no prompt/token content in saved evidence.

A temporary loopback preview with a synthetic delayed engine loaded in the
in-app browser. Browser control timed out before the Atlas button click could
be dispatched. Actual browser interaction/visual acceptance remains OPEN.
Do not deploy this UI change until that check passes. No paid inference or
staging changes were made in this increment; staging remains00027-2j9 Atlas0.

## Next checkpoint

1. Complete browser checks: initial wait, 15-second notice, Stop acknowledgement,
   completed reply retained after timer thresholds, and context change during wait.
2. Use fresh disposable accounts and a synthetic saved-job seed with the existing
   validator and `--concurrency-only`; first refresh budget and establish the
   independent cleanup guard. Record both outcomes and correlate model logs.
3. Verify tenant/admin/member boundaries and PostgreSQL behavior separately;
   process-local provider locking does not establish a distributed capacity limit.
4. Disable inference, revoke fixtures and verify cleanup. Record actual evidence,
   without upgrading this short sample to sustained production capacity.

Claude-owned module implementations and help text were left unchanged.
