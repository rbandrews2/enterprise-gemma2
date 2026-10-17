# Active hourly job-weather monitor

Ray approved this pilot on October17 at ONCE PER HOUR, superseding the earlier five-minute proposal. Activation is COMPLETE: hourly Scheduler enabled, private bounded worker verified, app coverage deployed to weather-hourly-1017. Weather SMS remains OFF. Weather SMS stays OFF. Exact application sourcec6adf9f36b6c2ed25882785b5abe96e4b1ba8224;
image sha256:edb4a3c4dde24cb6fe57d65ad79f1cfd611ab507d1d1bf03ea70e18f972e92ed
was initially deployed as wzos-v2-accounts-weather-c6adf9f. The same immutable image
is now served by wzos-v2-accounts-weather-hourly-1017 at100% traffic.
Current app identity/configuration independently inspected in Cloud
Shell; no credentials or values were printed.

## Separate app deployment

The card, permission-controlled foreground location, job-site settings, manual job
checks, acknowledgements and geofence prompts can deploy using the existing service
identity/bindings. Three additive weather tables and one index; no old-table changes.
Rollback traffic to wzos-v2-accounts-brand-4e281c6, retaining new evidence tables.
No new IAM grant, browser source origin, production SMS mode or recording change.

## Approved hourly independent monitor pilot (activation pending)

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
  Weather SMS stays OFF for this activation; do not copy Twilio bindings or enable customer SMS.
  No other secret bindings.
- Create dedicated wzos-weather-scheduler caller identity with only roles/run.invoker
  on this job (not a project-wide grant). Cloud Scheduler uses its OAuth identity
  to invoke the Google Run jobs API; no public app cron/authentication bypass.
- Scheduler wzos-weather-monitor runs once per hour (cron `0 * * * *`, time zone `America/New_York`), no automatic retries. Normal
  executions finish before the next tick; database deduplication handles accidental
  concurrent invocation. Initial pilot scope is one organization/up to5 active sites.
  More sites or organizations require explicit capacity/configuration review.
- Enable the web coverage flag only for the exact activated organization ID and
  only after schedule/job/readback and one bounded execution succeed. Other tenants
  must continue to see automatic monitoring inactive.
- No device location tracking in this worker: it fetches only admin-configured job
  points and public NWS data. Monitoring windows remain explicit; only current
  affected assigned workers, job owner and org admins can receive notices.
- Weather is supplementary: polling adds up to one hour plus provider/delivery delay;
  do not claim instantaneous warning or replace official emergency channels.

## Cost estimate and controls

At current us-central1 on-demand rates, one CPU costs$0.000018/second and memory
$0.000002/GiB-second. Jobs have a minimum one-minute charge. At24 executions/day,
one CPU/512MiB finishing within that minute is about$0.028/day before free allowances.
At the180sec task limit it is about$0.083/day for CPU/RAM; startup/shutdown, Scheduler,
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

## Activation progress (October17)

- Reconnected Cloud Shell and verified enterprise-gemma2 / admin@workzoneos.org.
- Scheduler API enabled successfully; its Google-managed service agent has the
  standard roles/cloudscheduler.serviceAgent role. No manual project-wide grant.
- Read-only database lookup uniquely confirmed the approved organization and found
  zero configured job sites. Temporary SQL proxy/socket removed in a finally block;
  credentials stayed in process memory and were not printed.
- Created private wzos-weather-monitor using the approved edb4a3c4 image, one task,
  parallelism1, 1CPU/512MiB,180s timeout,retries0; only existing DB secret/SQL binding.
  WZOS_WEATHER_POLLER_ENABLED=1; WZOS_WEATHER_SMS_ENABLED=0. No Twilio bindings.
- Initial execution wzos-weather-monitor-tpbhg SUCCEEDED (exit0): checked0, notices0, unavailable0. Empty live configuration; this is workload/database acceptance, not actual hazard-delivery acceptance.
- Created wzos-weather-scheduler identity. Immediate scoped invocation binding hit
  service-account propagation delay; retry succeeded. Readback confirms ONLY the
  scheduler identity has roles/run.invoker on this job. No broad role substituted.
- Scheduler readback: ENABLED, cron `0 * * * *`, America/New_York, OAuth to exact
  jobs:run endpoint, no retries. A manual Scheduler dispatch verified the caller path:
  AttemptFinished at2026-10-17T19:51:52Z returned HTTP200.
- Web coverage revision weather-hourly-1017 is Ready and100% traffic, same image.
  Exact runtime comparison preserved secrets, service identity, resources, ingress
  and SQL instance, changing only the three weather flags for the approved org.
- Do not claim real job hazard delivery from an empty pass. Admin must configure
  reviewed site coordinates and monitoring windows; no synthetic job added to live DB.

## Active checkpoint

Schedule `0 * * * *` / America/New_York (top of each hour), one organization,
up to5 active sites/pass. No device/background employee GPS collection, no SMS.
Hourly polling can delay alerts up to an hour plus provider/delivery latency.
Zero job sites were configured at activation: admins must save reviewed coordinates
and explicit monitoring windows in Weather -> Job weather & arrival settings.
No fake sites were inserted and no actual hazard-delivery acceptance is claimed.
Evidence: $HOME/wzos-weather-path.txt -> monitor-job.json, monitor-iam.json,
monitor-execution.json, monitor-first-run.log, monitor-scheduler.json,
monitor-scheduler-events.json, monitor-web-before/staged/revision/live.json.
Live proof: .local-data/release-20261017/live-weather-hourly.png (outside Git).
Rollback: pause Scheduler first, disable the organization's coverage flags (or
restore traffic to weather-c6adf9f), keep SMS off; remove worker/caller access only
after active execution ends. Retain weather/site/receipt records. Existing app image,
authentication, secrets, SQL connection and public ingress restrictions preserved.

Final acceptance: Scheduler-triggered execution wzos-weather-monitor-m5fcz also
SUCCEEDED (one successful task,zero failed). Public version HTTP200 and anonymous
weather notices HTTP401 passed. Signed-in Weather card rendered with background
monitoring active; no real GPS permission requested. No source/runtime rebuild or
unrelated full-suite rerun was needed for this approved configuration activation.
