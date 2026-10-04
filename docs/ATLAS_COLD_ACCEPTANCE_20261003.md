# Atlas cold-start acceptance: one bounded case

## Result

Accepted for this single synthetic request, after correlating zero-instance
metrics, request timestamps, model startup and the successful inference log.
This does not establish sustained capacity, production latency, source
applicability, or a repair/root cause for the earlier failed attempt.

- Code image: 85cf1ca; diagnostic build20f701b4-1936-41ce-a209-29ae64a4ac0a.
- Model revision: wzos-atlas-inference-00001-9rs.
- Both active and idle instance counts explicitly zero at22:41 and22:42 UTC.
- Test request99b45d12-d0ac-4b2a-b105-8586a04ac755 began22:42:52.562921 UTC.
- Inference request log22:42:53.640106: HTTP200, latency199.566861089s,
  trace24814a00da4773af1702a528a90fcb26, matching tested revision.
- New instance autoscaling startup22:42:53.659205, about1.096s after test start.
- Application startup completed22:46:10.679933; TCP probe passed22:46:10.957345.
- App returnedHTTP200 at22:46:13.304034, measured200.741s. Response validation
  confirmed model_called=true, no actions performed and no field-use approval.

The validator deliberately leaves cold_start_accepted=false until operator log
correlation. The correlation above satisfies that follow-up for this case; keep
the original raw evidence unchanged. Roughly198 seconds elapsed between test
start and model readiness. A 3 minute 21 second first reply still needs a better
customer waiting experience and further reliability testing.

## Guard, cost and cleanup

Fresh disposable fixture preparation passed. Initial preparation stopped on a
missing generated synthetic password before users were created; private retry
passed without printing the generated password. No customer messages were sent.
A separate30-minute guard ran before model provisioning, alongside the bounded
observer. No warmup or readiness inference calls and no automatic inference retries.

All controller cleanup commands returned0. Direct reads verified app00027-2j9
Ready=True and Atlas=0, inference service absent, and fixture disabled=True.
Only after verification were guard3327 and SQL proxy3109 stopped; observer3363
had completed. V1, DNS and production were unchanged.

Monitoring at22:47:39.866265 reported4,670.10753249346 cumulative billable seconds,
no additional pages, approximately$4.138 at the recorded rate. Preflight was
3,981.01335988446 seconds/~$3.528. Increment~$0.61. These are delayed compute
estimates, not invoices; build/storage charges are separate. Refresh before
another paid trial under the original$15 approval.

Cloud evidence: /home/admin_/wzos-evidence/cold2-*-20261003.*. Private fixture state
is outside Git at /home/admin_/wzos-grounding-ZCyfzy/cold2-fixtures-20261003.json
and is disabled. Sanitized summary: knowledge/atlas-cold-acceptance-20261003.json.

Google documents an idle retention period of up to10 minutes for GPU instances:
https://docs.cloud.google.com/run/docs/about-instance-autoscaling

## Next

Prepare bounded simultaneous-request/capacity acceptance with synthetic accounts,
preserving shared request limits and tenant isolation. Separately improve visible
cold-start waiting and cancellation behavior. Do not claim the first timeout was
fixed: this run demonstrates one successful cold path, not the absence of an
intermittent fault. No further GPU request is authorized by this document itself.
