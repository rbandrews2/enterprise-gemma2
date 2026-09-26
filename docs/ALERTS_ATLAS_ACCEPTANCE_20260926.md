# Scheduled staging alerts and Atlas integration — September 26, 2026

## Outcome

Partial acceptance. Four restricted-staging alert policies were created and read back as enabled. Atlas now receives the actual active module and role-specific guidance across eight modules. Regression passed, but real local inference timed out; AI end-to-end acceptance remains open. No V1, public DNS or production changes; no customer messages and no new inference service.

## Monitoring evidence

Project `enterprise-gemma2`; policies have **no notification channels**. Recipient selection is pending; no test notification was sent and delivery is not accepted.

| Policy | Threshold | Alert policy ID |
|---|---|---|
| Cloud Run service errors | At least 3 HTTP 5xx in 5 minutes | 609282251382333732 |
| SQL CPU | Above 80% for 10 minutes | 10378575521380954482 |
| SQL memory | Above 90% for 10 minutes | 3821949044718280847 |
| SQL disk | Above 80% for 5 minutes | 609282251382335722 |

Names have prefix `projects/enterprise-gemma2/alertPolicies/`. Filters scope Run to `wzos-v2-accounts` in `us-central1` and SQL to `enterprise-gemma2:wzos-v2-staging-db`. Auto-close is 1800 seconds; scale-to-zero is not an absence incident. No custom metric, polling service or deliberate capacity overload was created.

Operator tooling: `scripts/configure_staging_alerts.py`, catalog `ops/monitoring/staging-policies.json`, pushed as `7fb2455`. Applied from isolated Cloud Shell checkout `/tmp/wzos-alerts-ooqU2E`; output `/tmp/wzos-alert-apply.log`. Create and GET verification succeeded. Repeat-apply and real time-series query were not completed because browser control failed. Threshold triggering, recipient verification and notification delivery remain untested.

## Atlas capabilities and boundaries

Active-module context now covers work orders, time clock, forms, scheduling, training, messaging, navigation and Enterprise Work Zone Report. Core report requests are rejected before inference. Member scheduling guidance directs edits to an admin. Cross-module navigation and report-context changes clear conversation history and cancel pending requests. Hidden work-order selections are not attached to unrelated module questions. Historical report viewing does not pretend to be the current job.

App-owned guidance describes existing functions and missing features; this is not evidence that the model mastered them. No autonomous actions, dispatch, customer delivery, certification, payroll approval or automatic sign/flagger placement. Unsaved inputs and module records are not represented as inspected; existing scoped work-order/checklist and clock context retain their explicit boundaries.

## Validation

- Full suite: 156 run, **140 passed / 16 PostgreSQL tests skipped locally**. No new managed PostgreSQL run in this session.
- Focused integration/workspace/clock: 26 passed. Final intelligence rerun: 7 passed.
- Module coverage includes 32 role/edition/module combinations, Core report denial, invalid module rejection, empty action lists and member scheduling guidance.
- JavaScript syntax checks passed for workspace, assistant and report scripts. Final report-context event adjustment received syntax checks; browser interaction acceptance is still pending.
- New `scripts/evaluate_atlas_modules.py` exercises real HTTP against an isolated synthetic SQLite app and local model. It fails fast on a non-200 result; successful HTTP alone would not establish answer quality.
- First real evaluation: work orders HTTP 503 after 112.72 seconds; clock HTTP 503 after 130.97 seconds; remaining scenarios not run.
- Bounded two-thread retry: work orders HTTP 503 after 110.73 seconds; remaining scenarios not run. Local Gemma 3 4B CPU inference is not acceptable at this latency. Both evaluation runtime process trees were stopped.
- Actual outputs are ignored local files `.local-data/atlas-runtime/module-evaluation-20260926.json` and `module-evaluation-bounded-20260926.json`, with corresponding scheduled/bounded stderr logs. They are not GitHub backups.

## Next checkpoint

1. Obtain the alert recipient, configure/verify the channel, attach it to these policies and validate a clearly labeled test delivery without customer messages or capacity overload. Confirm time-series matching and repeat-apply behavior.
2. Resolve inference latency with a measured local option or a separately priced/approved hosted inference configuration. Existing staging approval does not cover new paid AI capacity.
3. Rerun all eight real HTTP scenarios, inspect grounded replies and navigation in the browser, then accept the four role/edition journeys on restricted staging. These code changes have not been deployed to Cloud Run; the local preview also needs a controlled restart to load the new backend.
4. Continue source-library/imagery/report-output and module production gates. September 30 test-model target is at risk until real inference and alert delivery pass.
