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
