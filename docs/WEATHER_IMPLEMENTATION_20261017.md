# Weather implementation contract

Implementation in the owned integration checkout; card/manual checks/arrival prompts
are deployed. Independent scheduled monitoring and weather SMS are not activated.
Basic card/local official hazards work for both roles/editions. Admins configure
monitored sites in their own organization; members read only permitted sites.
Existing assignment authorization and attendance reconciliation remain authoritative.

Startup DDL: weather_sites (tenant/job key, version, payload, author, updated_at),
weather_alerts (tenant/job/provider-ID key, revision hash, normalized payload),
weather_receipts (tenant/message key, job, recipient, source revision, acknowledgement).
Exact reviewable DDL is in services/workspace_preview/weather.py, DDL constant.
These are additive tables, with no alterations/backfills to existing tables.
Existing messages/SMS outbox are reused; weather delivery rechecks current site,
window, membership, assignment/ownership/admin access and source expiry at send time.
Rollback disables weather monitoring/UI and stops the poller; retain tables/evidence.

Proposed routes:
- POST /api/weather/current: authenticated coordinates, rate limited, cached NWS data.
- GET /api/weather/sites: permitted configured jobs only.
- PUT /api/weather/sites/{order_id}: admin, optimistic version, coordinate/radius and
  bounded monitoring window validation. No automatic address geocoding or Maps charge.
- POST /api/weather/poll: admin checks own organization's enabled sites; no cross-tenant scope.
- GET /api/weather/notices and POST /api/weather/notices/{id}/ack: recipient-only.
Independent closed-app site monitoring needs an authenticated scheduled workload;
prepare a bounded one-pass runner, but do not provision/claim it active without
reviewing its identity, limits and budget. Ordinary browser polling is not a substitute.

Provider requests use api.weather.gov only with bounded payloads/timeouts, no redirects,
no credentials or employee IDs. User explicitly enables foreground location following;
no live location or customer message is needed for synthetic acceptance.

## Implemented candidate behavior and bounds

- Fixed shared glass card: foreground opt-in location, one watcher,1km movement
  refresh/15min stationary refresh; stops on hidden/logout/org change, resumes only
  if previously enabled. Timestamp/basis, real stale snapshots and null missing
  values. Late responses cannot overwrite a new location or actor.
- Reviewed job coordinates/radius plus versioned monitoring window up to7days;
  max100 sites per organization. No address geocoding, sensor simulation or
  inferred coordinates. Both roles can view their permitted configured sites.
- Official public/actual NWS hazards only; current observations when fresh enough,
  hourly forecast fallback, no fabricated gusts/visibility/traction/compliance claims.
  NWS-only bounded response transport and60sec cached requests/outage backoff.
- Arrival requires uncertainty containment, fresh fix, two fixes plus5sec dwell;
  prompts review in Time Tracker. Existing clock buttons confirm attendance.
  Offline device GPS capture no longer assumes missing GPS just because internet
  is unavailable; data remains device-reported and unverified.
- Alerts persisted per org/job/source revision/recipient, transactional message and
  receipt creation, recipient acknowledgements, updated/ended notices and source
  outage preservation. Assignment revocation, entitlement downgrade, membership,
  current admin/site/window/expiry and consent rechecked before SMS delivery.
- SMS off for weather unless WZOS_WEATHER_SMS_ENABLED=1; then existing mode and
  recipient allowlist still apply. All tests use fake provider/synthetic phones.
- Bounded manual admin poll and scripts/poll_weather.py one-pass worker prepared.
  Worker requires WZOS_WEATHER_POLLER_ENABLED=1 and explicit --organization; default
  max5 sites/pass, stops starting sites after120sec; no cloud workload provisioned.
  Independent scheduled monitoring is NOT active. API/UI say so explicitly.

Focused initial local results:13 Python tests PASS. Final local Node suite133 PASS,
no skips. Full cloud PostgreSQL suite769 PASS/no skips on361a367; final weather
PostgreSQL23 PASS/no skips on4abb067. Final frontend privacy repair c6adf9f passed
all133 local Node checks and6 focused Cloud Shell Node checks. Git comparison proved
its Python backend/worker identical to the23-test PostgreSQL candidate, preserving
the evidence instead of repeating unrelated suites. Initial fixture issues corrected:
patched test clock needed matching alert timestamps; SMS opt-out request needed its
version. Assignment UI test now exercises My jobs instead of the obsolete member
Messaging render path. Offline GPS test now expects a real device fix, not invented
missing evidence. No real user GPS or customer SMS used.

Browser preview uses explicit synthetic weather and sample job coordinates. Existing
synthetic dispatch-notification404 banner is unrelated to weather. Mobile has no
horizontal overflow (390px viewport). Proof outside Git:
.local-data/release-20261017/weather-card-preview.png. Temporary viewport reset.
The duplicate broad local Python run was stopped to reduce laptop load; no full
local-Python success is claimed. Cloud full-suite result is the release gate.

Actual NWS public-city connectivity check returned ready/forecast with a source
timestamp for Norfolk. No personal coordinates were collected. Live readings remain
provider observations or forecasts, never a claim of on-site sensor telemetry.

Cloud evidence directory is recorded by $HOME/wzos-weather-path.txt. Full suite,
final PostgreSQL and frontend logs are retained there. The4abb067 build was superseded
by the frontend organization-selector privacy fix; do not deploy that older image.
Final application source c6adf9f36b6c2ed25882785b5abe96e4b1ba8224. Build afb75ef5-b2ee-
4442-8388-38fa0277d941 succeeded, image sha256:edb4a3c4dde24cb6fe57d65ad79f1cfd611ab507d1d1bf03ea70e18f972e92ed.
Guarded deployment completed with deploy.exit0: weather-c6adf9f Ready/100% traffic;
28 public asset hashes, weather markup, existing exact Daily policy, anonymous weather
401 boundaries and version endpoint passed. Runtime preserved from brand-4e281c6.
Rollback traffic to brand-4e281c6; new additive weather tables remain intact.
No independent
monitor workload/IAM or weather SMS activation has been applied.

Signed-in live browser verification: selected the existing Molecular Project
Development LLC organization; Weather card rendered with Use location and collapsed
job-location/alerts/admin settings. No GPS permission requested or accepted by agent.
Live proof: .local-data/release-20261017/live-weather-release.png (outside Git).
Synthetic preview server and duplicate broad local test process stopped; preview tab
closed. Live app and Cloud Shell retained. Monitor approval request is pending.

## Hourly pilot activation follow-up

Ray approved once-hourly monitoring onOctober17. It is now active for Molecular
only, cron0 * * * * / America/New_York; weather SMS remainsOFF. See
WEATHER_MONITOR_ACTIVATION_20261017.md for scoped identity/job/scheduler evidence.
Both direct and Scheduler-triggered live worker executions succeeded. Public app
is now weather-hourly-1017 at100% using the same edb4a3c4 immutable image; only3
weather coverage flags changed, with runtime/authentication preservation verified.
Zero configured job sites at activation; actual site/hazard/mobile acceptance open.
This supersedes earlier statements above that scheduled monitoring was inactive.
