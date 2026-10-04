# Atlas waiting and concurrency preparation

## Local changes

- October 3 follow-up: each outcome records its generated request ID and UTC
  start time, including transport/contract failures. The concurrent pair is
  awaited fully even when one request fails, preserving the other bounded
  outcome without retrying. Successful responses require explicit model use,
  false field approval, and no actions. Three focused tests passed, including
  timeout, non-object JSON and malformed-success cases; peer completion and
  omission of private exception text are verified with mocked HTTP.
- Cloud preflight remains pending: Cloud Shell is visible, but desktop input
  reports address-bar focus after terminal clicks. No commands were entered
  into uncertain focus. User asked to focus the terminal. No new authentication,
  cloud state, budget, deployment or live inference verification this pass.

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

### Desktop-browser follow-up, October 3

Chrome desktop control recovered the previously blocked interactions using the
same disposable local database and 180-second synthetic engine. Actual browser
observations and displayed screenshots verified:

- Stop during a pending request shows the cancellation acknowledgement, hides
  Stop, and enables Ask Atlas again. The acknowledgement does not promise that
  background GPU processing has stopped.
- A second request can start after cancellation. Its delayed notice appeared.
- Closing the assistant and choosing New work order during that request resets
  the question and conversation to work-order guidance; reopening shows enabled
  controls, no pending reply and no Stop button. A subsequent observation retained
  that cleared state.

Focused regression rerun: three Node reply/wait tests and two Python concurrency
acceptance tests passed. The Python runner uses mocked HTTP; it is not a live
two-request inference result. Late callback suppression is covered by the Node
test. Completed-reply retention was then observed with a two-second synthetic
engine at 27, 102, 161 and 187 seconds after submission. The final foreground
Chrome screenshot confirmed the reply remained intact beyond the 150-second
timer. Screenshots were displayed in the session, not saved in Git.
Seven additional Python cancellation/transport tests and six Node cancellation/
navigation tests passed: total focused validation 9 Python and 9 Node tests.
No application code changed, no cloud deployment or paid inference ran.

Remaining: budget/authentication preflight
and guarded live two-request acceptance. The earlier Stop/context browser blocker
is resolved for these synthetic cases; this is not production/GPU acceptance.
The temporary synthetic preview was stopped after validation.

### Browser follow-up, October 3

Actual in-app browser interaction with a disposable local database and a
25-second synthetic engine verified the initial waiting message, disabled
duplicate submission, the 15-second notice, and completed reply with controls
restored. The response explicitly said no model was called. No screenshot
artifact was captured; these observations came from the browser accessibility
state. Stop clicks arrived after completion and do not establish cancellation.
Increasing only the fixture delay to 180 seconds did not resolve browser-control
timeouts. Chrome fallback also timed out during navigation.

Stop acknowledgement, context changes during a pending reply, and retention
beyond later timer thresholds remain OPEN. The temporary synthetic server was
stopped. No cloud deployment or paid inference occurred. Prior automated test
results above were not rerun for this documentation-only follow-up.

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
