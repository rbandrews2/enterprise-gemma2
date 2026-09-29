# Atlas reliability checkpoint — September 29

## Local checks completed

Four deterministic tests exercise the actual private VLLM adapter with a simulated HTTP provider; they make no paid calls:

- An overlapping request is rejected before a second provider request. Completing the first releases the gate and the next request succeeds.
- A client-disconnect event cancels inference while reading an upstream response, closes that response stream, releases the gate and permits the next request.
- The request deadline cancels a blocked transport without retry; readiness becomes false and a later request succeeds.
- An upstream HTTP 403 fails closed without retry or sensitive error disclosure; a later request succeeds.

Failure diagnostics now record provider mode, exception class and upstream HTTP status. They exclude response bodies, credentials and request headers. This would have identified the earlier private-service 403 without a separate log correlation step.

Full local suite: 186 tests, 170 passed and 16 database-specific skips. Four focused reliability tests passed. `git diff --check` passed.

## Important boundaries

The gate is per application process, not a distributed quota across instances. Cloud Run scaling/concurrency and provider limits still govern total service load. Cancellation closes the application's HTTP stream; these local tests do not prove that Cloud Run forwards the disconnect promptly or that model GPU work stops immediately.

No cloud deployment or paid inference was performed for these tests. The previous disabled app revision 00013-kmx is the last verified cloud checkpoint, not a newly inspected cloud state. The diagnostic change remains undeployed until the next staging image build.

## Next live test, bounded by remaining approved trial spend

1. Check cumulative usage and current private service/app state. Use fresh disposable identities and verify credential lifetimes before provisioning.
2. Deploy the source-enabled image with the diagnostics update; keep the existing full-size model, private IAM and min0/max1 limits.
3. Verify model scale-to-zero using monitored instance state, then time a real app request. Do not label deployment duration or an already-warm request as cold-start acceptance.
4. Run a bounded pair of simultaneous authenticated requests and inspect both outcomes plus provider request counts. Establish behavior across app instances, not only the local gate.
5. Disconnect one in-flight client and inspect app/provider logs for cancellation; verify the next request succeeds and saved job data is unchanged. If the platform does not propagate cancellation, document and repair that limitation.
6. Retain sanitized timing/status evidence, disable fixtures/app inference, delete the trial service and verify cleanup. Do not keep the GPU warm while waiting for a scale-to-zero observation.

True cloud cold-start, concurrent-user capacity, cancellation propagation and cost-per-workflow remain open acceptance gates.

## Live staging follow-up — partial acceptance

Cloud Build `a2cbfaba-e21e-4485-a945-a5a2316aca94` succeeded. Source-enabled image `bf5e75c242bf-sources` deployed as app revision `00014-m6x`; full-size private inference revision `00001-5bg` reached Ready. Fresh managed identity/role/tenant checks passed. The saved-job seed check succeeded before the reliability runner was allowed to execute.

Observed results:

| Case | Result |
| --- | --- |
| Concurrent A | HTTP 200, real model reply, 4.161 seconds |
| Concurrent B | HTTP 503, 0.442 seconds, no model response |
| Client disconnect | Client task cancelled after 0.25 seconds; upstream cancellation unverified |
| Recovery after 3 seconds | HTTP 503, 0.419 seconds; immediate recovery FAILED |
| Later explicit recovery observation | HTTP 200, real model reply, 4.154 seconds |

The service was not permanently stuck. These results are consistent with the original request continuing behind Cloud Run after client cancellation, but do not independently prove the cause. The current evidence records status, not the 503 response reason. Do not call cloud cancellation accepted or assert that GPU generation stopped. A single concurrent pair is not a customer-capacity benchmark.

Next repair/investigation: capture a safe structured busy/unavailable reason and correlation identifier, verify actual cancellation propagation in app/provider logs, then implement an authenticated cancellation mechanism that remains correct across app instances if transport disconnect is insufficient. Avoid an instance-local cancellation endpoint presented as a distributed solution. Re-test recovery and unchanged saved records before acceptance.

True scale-from-zero timing remains untested. This session observed deployment startup/compilation only. Do not repeat the successful citation test unnecessarily; retain the seeded scenario for the next lifecycle validation.

Evidence is preserved in Cloud Shell `/home/admin_/wzos-grounding-ZCyfzy/`: `reliability-results.jsonl`, `reliability-seed.jsonl`, build/model/proxy logs and disabled fixture state. Runner is `scripts/validate_atlas_reliability_staging.py`, bounded to two concurrent requests, one cancelled attempt and one recovery attempt; the later observation was a separate diagnostic call. No customer sends or production changes.

Pre-run usage: 2,144.485 billable inference-instance seconds, about $1.90 compute at the recorded rate, excluding this run/builds/storage and billing lag. Recheck before further paid work; the approved trial ceiling remains $15.

Cleanup: synthetic users disabled/tokens revoked/organizations disabled; inference service deletion confirmed; SQL proxy and cleanup guard stopped. Final account revision 00015-qfq is Ready after disabling Atlas, retaining the diagnostic/source image. V1 and DNS unchanged.

## Parallel-work follow-up: failure classification prepared locally

ModelUnavailable now carries an allowlisted reason. Private adapter distinguishes busy/disabled/timeout/provider_error; the API preserves the text detail and adds a random correlation ID and safe reason code, with matching server logs. Disconnect observations are logged separately. The live runner retains only allowlisted codes and validated hexadecimal correlation IDs, not error bodies or credentials. Full suite: 187 total, 171 passed/16 database skips; focused API/private-adapter checks passed. This instrumentation is not cloud-deployed and does not fix or accept cloud cancellation. Next deploy it in a bounded trial to distinguish busy from provider failure before choosing an instance-safe cancellation design.

## Pre-break socket validation

Added `tests/test_vllm_socket_reliability.py`: a real loopback HTTP server holds a synthetic provider response open. Application disconnect closes the actual upstream socket, releases the adapter gate, leaves no partial usage, and a subsequent request succeeds. Exactly two provider requests are observed; no retry, GPU, external credentials, or real inference. Production HTTPS validation is unchanged. This is transport validation, not Cloud Run proxy cancellation acceptance.

Full discovery suite: 188 total, 172 passed and 16 database skips in 44.574 seconds. An initial explicit-module invocation encountered the existing `test_knowledge` discovery-path import dependency; the standard full discovery invocation passed. No application repair was necessary for the socket test.

Read-only cloud verification after reconnect: account revision `wzos-v2-accounts-00015-qfq`, Atlas enabled `0`, inference-service listing empty. A narrow September 29 `Atlas reply failed` textPayload query returned no rows; absence of matches is not evidence that cancellation worked or that no error occurred. No deployments, paid inference or cloud configuration changes this pass.

Paused at user request. Next: refresh trial usage and credentials, deploy prepared failure-code/correlation instrumentation, perform the bounded live cancellation/recovery observation, correlate logs, and clean up. Cloud cancellation and true cold-start remain unaccepted.
