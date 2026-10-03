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

Seven new metric/preflight tests and three existing credential-expiry tests passed. A mocked operator run confirms absent metrics prevent any inference POST. Live acceptance pending.

## October 3 live checkpoint — verification required

Preflight: Cloud Shell checkout synced to ff0aa5d; app was 00021-fkf and trial inference absent. Fresh cumulative monitored compute was 3,360.475 seconds (~$2.978), no additional metric pages. Historical instance metrics demonstrate explicit active/idle zero samples are available for this service. New synthetic account preparation passed IAM/sign-in/refresh/verified-email/admin/member/tenant/last-admin checks.

Commands were submitted to start a 30-minute disable/delete guard and deploy the existing pinned inference configuration. Browser control then failed. Deployment result, guard process state and current resource state are NOT verified. The later app-enable/IAM command failed before terminal input; no inference test was sent. Do not record cold-start acceptance or assume cleanup completed.

Immediate recovery actions in Cloud Shell:
1. Inspect `/home/admin_/wzos-evidence/cold-model-deploy-20261003.log` and `cold-guard-20261003.log`, service state and guard PID.
2. If the test cannot safely finish within the remaining guarded window, disable Atlas and delete only trial service `wzos-atlas-inference` in enterprise-gemma2/us-central1; verify completion.
3. Disable/revoke the disposable fixture using `/home/admin_/wzos-grounding-ZCyfzy/operator-accounts.py disable --state /home/admin_/wzos-grounding-ZCyfzy/cold-fixtures-20261003.json` with that directory's venv Python while the SQL proxy is available.
4. Verify the app is Ready with Atlas=0, inference listing empty and fixtures disabled before stopping the recorded proxy/guard PIDs. Refresh compute usage.

Helpers/evidence are `/home/admin_/wzos-evidence/cold-{proxy,guard,accounts,model-deploy}-20261003.*`. No new app image was built, and no production/V1/DNS changes were attempted.
