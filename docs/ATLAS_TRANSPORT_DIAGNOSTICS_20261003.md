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

## Restricted staging preparation completed

The saved trace query returned only the previously observed HTTP500/0s entry,
without an explanatory payload. Filtered inference logs showed route registration
and startup but no completed generation; this is not proof of a specific failure cause.

Source snapshot verification passed for the preserved scoped October 1 library.
The full archive upload was slow but completed; no fallback/duplicate build ran.
Cloud Build `20f701b4-1936-41ce-a209-29ae64a4ac0a` succeeded from code `85cf1ca`.
Image digest: `sha256:81fa66d7ff26e45b8e7e1f09366aa3b5bcb0df599d142f7f0abc24eca45248e4`.
Two diagnostic tests also passed in Cloud Shell.

Deployed only `wzos-v2-accounts` revision `00025-r6q` with Atlas explicitly disabled.
Direct verification: Ready=True, Atlas=0, authenticated `/api/identities` HTTP200
with `X-WZOS-Authorization`, anonymous request HTTP403, inference service absent.
No live inference ran. Build/storage costs are separate from recorded GPU compute.
V1, production and public DNS were unchanged; Claude module branches were not included.

Next: refresh cumulative trial spend and disposable fixtures, then run one guarded
cold-start attempt with the deployed diagnostics and correlate request timestamps
with startup logs. Cold-start acceptance remains open. Rollback image is
`us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:4a32b4e4c6276caec34d43bec4d3173f08def5680ddbf0a1f7ba65a2caf6dd61`;
keep Atlas disabled if rolling back.
