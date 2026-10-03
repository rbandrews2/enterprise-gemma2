# Atlas timeout diagnostics

The saved cold trial failed after 286.397 seconds. Existing logs do not establish
whether response headers or body delivery stalled. Model startup completed before
the timeout; the separate inference HTTP500 entry is not conclusively correlated.
Do not assign a root cause or increase the timeout based on this evidence alone.

## Local change

The shared managed/private transport now records a generated attempt ID, elapsed
time, failure phase (preparation, authentication, response headers, response body,
or validation), and any received upstream status. It never logs prompts, context,
tokens, response content, or exception messages. This ID correlates transport log
entries only; it is not a Cloud Trace ID or the application's request ID.

Cancellation now clears the last-success readiness indicator and logs its phase
before propagating cancellation. The request lock still releases normally.
No timeouts, model settings, capacity limits, retries, or public APIs changed.

## Validation and next checkpoint

Two new local tests cover header timeout, body timeout, HTTP500, cancellation,
secret omission, no automatic retries, lock release, and explicit recovery.
Focused tests passed. Full-suite results are recorded in SESSION_HANDOFF.md.

This is diagnostic preparation, not a fix or acceptance of the live cold-start
failure. No deployment or paid inference was performed for this increment.
Before another trial, inspect the saved Cloud Run request/startup logs and
available trace for the failed request, then deploy the tested diagnostic image
within the existing staging authorization. Keep the independent cleanup guard,
refresh cumulative spend, and require timestamp correlation for cold acceptance.
