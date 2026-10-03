# Atlas scale-from-zero validation

## Scope

One synthetic request through the existing restricted application after the private inference service reaches zero instances. No application image change, customer messages, model training, or production changes. Claude owns Time Clock in a separate worktree; this pass changes only Atlas operator tooling and evidence.

## Evidence requirements

`scripts/validate_atlas_cold_start.py` rejects missing, stale, incomplete, nonzero, wrong-project/revision, duplicate-state and mismatched metric samples. It requires two consecutive matching explicit zero samples for both active and idle states. The operator must also confirm no other serving revision or concurrent tester can handle/warm the model. No model readiness probes are allowed during the idle wait.

Google documents instance-count monitoring and metric sampling/visibility delay. Metrics are retrospective: even a zero preflight plus a successful HTTP response remains provisional until service startup logs identify a new instance starting during that request. Absence of a metric is never interpreted as zero. If this service omits zero samples, retain the inconclusive result and establish an alternative documented instance-state observation before spending on another inference attempt.

Official references:
- https://docs.cloud.google.com/monitoring/api/metrics_gcp_p_z
- https://docs.cloud.google.com/run/docs/about-instance-autoscaling
- https://docs.cloud.google.com/run/docs/container-contract

## Procedure

1. Recheck active credentials, service state, Git state and cumulative trial usage. Use disposable verified member credentials and the existing private app/model IAM.
2. Install a 30-minute independent disable/delete guard before model creation. At the previously recorded approximately $3.19/instance-hour, that bounds nominal single-instance compute near $1.60, excluding cleanup time, storage/builds and billing lag. Keep total within the approved $15 trial. No new app build is required.
3. Deploy the existing pinned full-size configuration, min=0/max=1; enable the restricted app. Wait for deployment completion and natural scale-down. Deployment initialization does not count as the tested startup.
4. Observe control-plane metrics at bounded intervals. Do not call model readiness/status or send warmup requests. Stop at the guard deadline if zero cannot be evidenced.
5. Refresh fixture credentials if required without calling model endpoints. Run the validator once with active private `--state` and a new `--output`. There are no automatic inference retries. Transport failure requests explicit cancellation.
6. Correlate request timestamps with startup logs and revision/instance identity. Record latency and success/failure honestly; one sample is not a capacity benchmark. Record monitored usage separately from an invoice.
7. Disable Atlas, delete trial inference, revoke/disable fixtures, verify live state, then stop helpers/guard. Preserve sanitized evidence and update the handoff.

## Local validation

Nine new metric/preflight tests and three existing credential-expiry tests passed. A mocked operator run confirms absent metrics prevent any inference POST. Live acceptance pending.

## October 3 live checkpoint — verification required

Preflight: Cloud Shell checkout synced to ff0aa5d; app was 00021-fkf and trial inference absent. Fresh cumulative monitored compute was 3,360.475 seconds (~$2.978), no additional metric pages. Historical instance metrics demonstrate explicit active/idle zero samples are available for this service. New synthetic account preparation passed IAM/sign-in/refresh/verified-email/admin/member/tenant/last-admin checks.

Commands were submitted to start a 30-minute disable/delete guard and deploy the existing pinned inference configuration. Browser control then failed. Deployment result, guard process state and current resource state are NOT verified. The later app-enable/IAM command failed before terminal input; no inference test was sent. Do not record cold-start acceptance or assume cleanup completed.

Immediate recovery actions in Cloud Shell:
1. Inspect `/home/admin_/wzos-evidence/cold-model-deploy-20261003.log` and `cold-guard-20261003.log`, service state and guard PID.
2. If the test cannot safely finish within the remaining guarded window, disable Atlas and delete only trial service `wzos-atlas-inference` in enterprise-gemma2/us-central1; verify completion.
3. Disable/revoke the disposable fixture using `/home/admin_/wzos-grounding-ZCyfzy/operator-accounts.py disable --state /home/admin_/wzos-grounding-ZCyfzy/cold-fixtures-20261003.json` with that directory's venv Python while the SQL proxy is available.
4. Verify the app is Ready with Atlas=0, inference listing empty and fixtures disabled before stopping the recorded proxy/guard PIDs. Refresh compute usage.

Helpers/evidence are `/home/admin_/wzos-evidence/cold-{proxy,guard,accounts,model-deploy}-20261003.*`. No new app image was built, and no production/V1/DNS changes were attempted.

### Reconnection update

A later reconnection confirmed inference revision `00001-7wz` Ready=True and guard PID1349 running at elapsed07:43. Private app-invoker binding and Atlas enable completed. An initial observation showed active=1/idle=0, correctly refusing cold-start acceptance.

A bounded Cloud Shell observer was launched as PID1515 from `/home/admin_/wzos-evidence/cold-session-20261003.py`, logging to `cold-session-20261003.log`. It observes once per minute for at most12 minutes (also constrained by guard time remaining), invokes the single-request validator only after explicit zeros, and attempts app disable, inference deletion and fixture revocation in its finally path. The separate guard remains independent. Browser control stalled again before the observer result could be read. Check these logs and verify final state; do not start another trial while this one is unresolved.

Local credential/CLI fallback is unavailable. The GitHub collaboration contract is `docs/COLLABORATION_CONTRACT.md`; Claude's module worktree has not been modified.

## Recovered results and verified cleanup

Browser restart restored access. The cloud-side observer completed and all three cleanup commands returned0. The one inference attempt failed; no retry was sent.

- Explicit active=0/idle=0 samples:21:09:00 and21:10:00 UTC. Observation21:10:25.653964.
- Request42f68f8a-a157-410d-9e5c-6db63e252f4d started21:10:25.654263 UTC.
- HTTP503 after286.397s at21:15:12.050903; response not validated.
- App logs: ReadTimeout, code=timeout, correlation c52d9f5396af4d0c9117731d7eb72046.
- Inference request log at21:10:27.003603 UTC records POST HTTP500 with reported latency0s, trace0d68c00ffffc2005d3fb3f674b7e6c67. No diagnostic payload was present. Correlation to the measured application request is not established; preserve this evidence without assigning a root cause.
- Model autoscaling startup log21:10:20.887283 precedes the measured request by about4.77s. Thus zero metrics were retrospective; this run does NOT prove that this request triggered startup.
- Model startup completed and TCP probe succeeded21:13:38.187305, before the application timeout. Startup delay alone does not explain the entire failure; request routing/processing needs further diagnosis.

Direct cleanup verification: app00024-xqr Ready=True with Atlas=0; trial inference listing empty; cold fixture state disabled=True. Independent guard had completed after the observer cleanup, creating another disabled app revision; its exit1 is consistent with attempting deletion of the already-absent service, not evidence of a remaining GPU. Guard and observer processes were absent; SQL proxy PID1201 was identified and stopped. No V1/DNS/production changes.

Post-cleanup monitored cumulative inference time:3,981.013 seconds, approximately$3.528 compute at the recorded rate, no additional metric pages (21:31:22 UTC). Approximately$0.55 above preflight; excludes storage/builds and billing lag. Recheck before another trial.

**Outcome: cold-start acceptance FAILED/open.** Next inspect the existing request/startup logs and request-queue behavior, improve timestamp correlation, and prepare a focused repair before another paid trial. Do not simply increase timeouts or describe this as production-ready. The earlier October2 cancellation acceptance remains separate.
