# Proposed closed-app job-weather activation

Not applied. Exact tested application source4abb067; image digest to be recorded
after build. Current app identity/configuration independently inspected in Cloud
Shell; no credentials or values were printed.

## Separate app deployment

The card, permission-controlled foreground location, job-site settings, manual job
checks, acknowledgements and geofence prompts can deploy using the existing service
identity/bindings. Three additive weather tables and one index; no old-table changes.
Rollback traffic to wzos-v2-accounts-brand-4e281c6, retaining new evidence tables.
No new IAM grant, browser source origin, production SMS mode or recording change.

## Proposed independent monitor pilot (needs action-time approval)

- Project enterprise-gemma2, region us-central1. New private Cloud Run job
  wzos-weather-monitor, one task/parallelism1,1CPU/512MiB,180sec timeout, retries0.
  Execute only reviewed scripts/poll_weather.py with the selected Molecular Project
  Development LLC organization ID and at most5 configured sites/pass.
- Attach existing wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com as its
  runtime identity. That identity retains its existing effective permissions while
  attached; no claim that the worker has a newly restricted database role.
- Bind the existing wzos-v2-staging-database-url secret and the same SQL instance
  enterprise-gemma2:us-central1:wzos-v2-staging-db. If controlled SMS is activated,
  copy only the three existing Twilio secret references, current test mode/allowlist
  and public callback base from the app metadata; no secret values in docs or Git.
  No other secret bindings. Do not enable broad customer SMS.
- Create dedicated wzos-weather-scheduler caller identity with only roles/run.invoker
  on this job (not a project-wide grant). Cloud Scheduler uses its OAuth identity
  to invoke the Google Run jobs API; no public app cron/authentication bypass.
- Scheduler wzos-weather-monitor runs every5minutes, no automatic retries. Normal
  executions finish before the next tick; database deduplication handles accidental
  concurrent invocation. Initial pilot scope is one organization/up to5 active sites.
  More sites or organizations require explicit capacity/configuration review.
- Enable the web coverage flag only for the exact activated organization ID and
  only after schedule/job/readback and one bounded execution succeed. Other tenants
  must continue to see automatic monitoring inactive.
- No device location tracking in this worker: it fetches only admin-configured job
  points and public NWS data. Monitoring windows remain explicit; only current
  affected assigned workers, job owner and org admins can receive notices.
- Weather is supplementary: polling adds up to5minutes plus provider/delivery delay;
  do not claim instantaneous warning or replace official emergency channels.

## Cost estimate and controls

At current us-central1 on-demand rates, one CPU costs$0.000018/second and memory
$0.000002/GiB-second. Jobs have a minimum one-minute charge. At288 executions/day,
one CPU/512MiB finishing within that minute is about$0.33/day before free allowances.
At the180sec task limit it is about$0.99/day for CPU/RAM; startup/shutdown, Scheduler,
network, database/logging/storage and SMS are additional, so this is not a hard bill cap.
No GPU/model instance. Monitor actual usage; alert polling/delivery must be bounded.

Official sources checked October17:
https://cloud.google.com/run/pricing
https://docs.cloud.google.com/run/docs/execute/jobs-on-schedule

## Verification and rollback

Before mutations: verify exact built digest, approved org ID, scheduler API/service
agent readiness and current secret reference versions without reading them aloud.
Apply only the above resources/grants; any additional required IAM permission needs
separate review. First run must show a successful bounded pass and no cross-org
notices/unauthorized SMS. Check receipt deduplication and existing source timestamps.

Rollback: pause the Scheduler job first; disable the organization's coverage flag
and weather SMS; stop/remove the worker after execution ends, remove its scoped
invoker binding and unused scheduler caller identity. Retain database notices,
receipts, settings and release evidence. No customer data deletion or old-release
billing/security bypass is part of rollback.
