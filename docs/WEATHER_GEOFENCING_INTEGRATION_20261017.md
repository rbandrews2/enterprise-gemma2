# Weather and geofencing integration strategy

October 17, 2026. Planning/static inspection only; no application code, cloud resources,
location collection, notifications or production settings changed.

## Combined weather experience (Ray's confirmed direction)

The fixed card and assignment alerts are complementary parts of one feature;
the card does not replace the alert plan below.

- Everyday view: a fixed compact glass card follows the user's permitted foreground
  location and refreshes basic conditions as they move.
- Personal hazards: show relevant official alerts for that location in the card;
  use an accessible severity indicator and expandable source details.
- Assigned-site hazards: server monitoring independently checks active assigned
  sites during configured monitoring windows, even when the worker is elsewhere
  or WZOS is closed. Notify affected assigned workers and relevant org admins
  through durable in-app notices and consent-controlled SMS when activated.
- Each alert says whether it concerns current location or a named assigned job,
  includes validity/source time and opens the relevant details. Do not silently
  switch the card's location when a job alert arrives. Retain deduplication,
  updates/cancellations/expiry and acknowledgement tracking from the alert plan.
- Closed-app personal-location alerts are not promised: only assigned sites can
  be monitored without continuous background device tracking. Foreground GPS
  following, server job monitoring and delivery status remain distinct.
- Geofence arrival prompts remain connected to My jobs/Time Tracker, with explicit
  user confirmation; weather warnings never automatically change attendance.

Ray prefers one fixed weather card with basic live information that follows the
user's changing location. Keep a consistent responsive placement and compact size
in the existing glass/amber design; do not introduce a floating overlay that covers
mobile controls. Show locality, condition icon/text, temperature, feels-like,
wind/gusts, precipitation and source update time. Hazard details may expand only
when relevant. Location-following is the normal mode after explicit permission;
selected-job weather is an explicitly labeled fallback, not a silent replacement.
This preference updates the plan; implementation/deployment is still pending.

## Source examined

Read-only source: C:/Users/MolecularDev/GEMINI_WZOS_V1, HEAD
07b8eef28d255f52a07697032371cf2ae2dc86b2. Working tree reported clean.
This React/TypeScript/Vite app is distinct from the current Python/vanilla-JS V2.
Reuse algorithms, interaction patterns and appropriate text; do not transplant its
React state/auth/storage architecture or add a second runtime.

| Feature | Source location | Observed behavior |
| --- | --- | --- |
| Weather | src/components/weather/WorkZoneWeatherWidget.tsx:44 | Browser GPS request; Open-Meteo current temperature, apparent temperature, humidity, wind/gusts, precipitation and WMO code; local hazard banner/chime and drill drawer. |
| Dashboard placement | src/components/dashboard/WorkZoneDashboardTab.tsx:239 | Renders the weather widget. |
| Distance | src/utils/geofencing.ts:7 | Haversine distance, formatting, nearest-job sorting and circular 150/350/800m presets. |
| GPS lifecycle | src/hooks/useGeofencing.ts:18 | watchPosition, accuracy display, arrival detection, dismissal and simulated arrival/travel. |
| Clock interactions | src/components/clock/TimeClockTab.tsx:70 | Arrival suggests/selects a job; explicit handlers clock in or switch task. |
| Arrival/config UI | src/components/clock/GeofenceArrivalCard.tsx; GeofenceMonitorBar.tsx | Arrival prompt, radius selection and test controls. |
| Notification UI | src/components/notifications/NotificationsTab.tsx:104; src/context/AppContext.tsx:1186 | Weather template/type exists; addNotification updates React state. Widget does not call it. |

## Findings that must be corrected before reuse

1. Weather fetch failures manufacture fixed readings (68F, 14mph wind, 22mph gusts)
   and label them cached offline with a fresh display time. These are not cached
   observations. Gusts also use an invented multiplier when missing. Preserve nulls;
   show unavailable or an actual last successful snapshot with its original time.
2. Widget requests current conditions, not official alert/CAP data or hourly forecast.
   No timed polling, durable alert ingestion, background delivery or SMS hookup was
   found in it. It cannot establish imminent dangerous weather from that request.
3. Hard-coded wind/heat/fog/rain rules return only one hazard. WMO weather codes do
   not establish measured lightning distance, pavement traction or safe visibility.
   Apparent temperature is displayed as heat index. Fixed ballast, taper percentages,
   rest schedules and blanket MUTCD/OSHA/Caltrans compliance claims are unsupported
   by this code. Do not copy them into authoritative operating instructions.
4. defaultCoords is a new array on each render; loadLocationAndWeather depends on it
   and is an effect dependency. This creates a repeated-fetch risk. warning objects
   are also recreated, making the critical chime effect prone to repeated playback.
5. Geofence classification uses distance <= radius, ignoring recorded GPS accuracy,
   fix age and simulation state. Clock notes call arrival verified even when it may
   be simulated. Device location is evidence, not proof of identity/attendance.
6. Reset-to-real-GPS calls startGpsWatcher with the previous isSimulated closure and
   the effect also restarts it. Refactor to one owned watcher with deterministic
   cleanup; clear/expire old fixes on error and actor/job changes.
7. Clock passes context jobs directly into the hook. V2 must supply only server-
   authorized jobs/assignments, not rely on client filtering as the access boundary.

## Integration sequence (proposed implementation)

### 1. Shared location contract and job settings

- Reuse V2 navigation.py coordinate validation, permitted job/assignment lookup,
  timeclock.py location evidence and current organization authorization.
- Admins set/review site center and radius; members receive only assigned permitted
  sites. Record coordinate source, reviewed_at, radius, version and updated_by.
  A map pin is a proximity reference, not an approved road-work perimeter.
- Use explicit foreground location permission with a visible stop control. Follow
  user location after permission; if denied/unavailable offer selected-job weather
  with a clear location label, or location selection. Avoid sending
  employee identity or continuous precise tracks to weather providers.
- Proposed settings/evidence DDL must be reviewed for tenant keys, constraints,
  retention and backward compatibility before implementation/deployment. Do not
  overload existing time_location_events event enums without a reviewed contract.

### 2. Weather adapter and mobile glass card

- Recommend NWS as the initial U.S. provider: official watches/warnings/advisories,
  point-based hourly forecasts and timestamped observations where available.
  Missing coverage/data must be explicit. Open-Meteo can be an optional commercially
  licensed adapter later; do not ship its current free endpoint in paid WZOS.
- Add proposed weather.py provider adapter and authenticated GET /api/weather/jobs/
  {job_id}; resolve authorized site server-side. Allowlist provider hosts/response
  links, bounded timeouts/payloads, schema validation and retry/backoff. Never fetch
  arbitrary user-provided URLs. Validate coverage, zone/polygon and effective times.
- Cache by provider/site or forecast grid, share public meteorological payloads
  while keeping organization subscriptions/recipients private. Respect provider
  cache headers. Proposed pilot intervals: alerts once/minute per unique area,
  forecasts every15 minutes; tune after request-volume/latency evidence.
- Fixed card: locality, basic conditions, temperature/feels-like, wind/gusts,
  precipitation, source timestamp and relevant active hazards. Optional expanded
  details can include the next-hours outlook; keep the default face brief.
  Reuse one foreground location subscription, debounce meaningful movement or
  forecast-area changes and cancel/ignore stale requests so an older response
  cannot overwrite the new location. Refresh on resume and bounded freshness
  timers even when stationary, without one provider call per GPS fix. Movement
  thresholds and freshness limits remain implementation settings to validate.
  Do not call old-location data current during a refresh: label it as previous
  location until replacement arrives. Use genuine last-success data offline,
  prominently stale with original source time; no simulated fallback readings.
  Live means latest available provider data, not instantaneous sensor telemetry.
  Show all applicable hazards, ordered by severity. No data is not an all-clear.
- Separate official NWS alerts from configurable organization advisories. Atlas may
  explain sourced alerts; an LLM must not decide whether an official alert is sent
  or invent safety instructions. No GPU/model calls required for ingestion/routing.

### 3. Durable weather alert delivery

- Add tenant-scoped site subscriptions, normalized source alerts, delivery records
  and acknowledgements using existing Google-backed database and messaging.py.
  Proposed keys: provider alert ID + source update/version + org + recipient + channel.
  Handle update/cancel/expiry explicitly; retain source timestamps and text.
- A scheduled bounded server poller is required for alerts while WZOS is closed;
  do not use a perpetual loop inside a scale-to-zero web request. Design/review its
  Google scheduling identity, invoker access, resource cap and budget first.
- Reuse in-app notices, verified phone consent, Twilio outbox deduplication/retry,
  opt-out and membership recheck at send time. An explicit weather-purpose branch
  must be reviewed in existing delivery authorization, not assumed compatible.
- Notify affected assigned workers and relevant org admins together; do not delay
  worker warnings awaiting admin approval. Superseded/cancelled assignments stop
  future targeting. Link to the affected My jobs detail with a weather panel.
- Keep current approved-number SMS test gate until broader sending is authorized.
  Real web push needs subscription/delivery implementation; do not equate existing
  service worker or install support with background push acceptance.
- Preserve provider delivery status separately from human acknowledgement; no
  guarantee of immediate receipt or exclusive reliance on this app for warnings.

### 4. Foreground geofencing in Time Tracker and My jobs

- Port pure distance functions into existing JS, validate finite coordinates and
  radius; clamp floating-point distance math. One permission-controlled watcher,
  stopped on logout/org change/explicit stop/unmount; throttle battery/network work.
- Classify inside only when distance + reported accuracy <= radius; outside only
  when distance - accuracy > radius; otherwise uncertain. Require fresh fixes and
  a short dwell/hysteresis before alerting to reduce boundary chatter. Exact age,
  accuracy and dwell values are configurable proposals to verify on real devices.
- Prompt 'You appear near [job]. Start work / Switch task / Dismiss.' Explicit
  confirmation calls the existing authorized/idempotent clock operation. Never
  auto-punch, auto-approve, lock out a legitimate punch or call GPS proof of attendance.
- Retain manual flow for denied/poor GPS. Simulator is test-only and isolated from
  real attendance/delivery; always visibly simulated, never verified.
- Offline: calculate proximity locally if a fresh fix and authorized cached job are
  available. Existing timeclock.js currently skips GPS capture when navigator.onLine
  is false; revise that branch deliberately because a device may obtain GPS offline.
  Queue device-reported evidence under existing unverified reconciliation rules.
- Foreground PWA scope only; no promise of continuous locked-screen/background
  geofence arrival detection. Weather poller can monitor assigned sites without
  background worker tracking. Do not build continuous employee surveillance.

### 5. Focused validation and release

- Pure tests: known distance, boundary/uncertainty, invalid coords, stale fixes,
  permission errors, duplicate arrivals, actor/org changes, simulator isolation.
- Provider fixtures: overlapping alerts, zone-only/null polygons, updates/cancels,
  expiry, missing fields, delayed observations, outage/rate limits and stale cache.
  Fixture data stays marked synthetic and cannot enter real notification queues.
- PostgreSQL: tenant/role access, membership revocation, unique outbox keys and retry
  concurrency. Android: readable card, one chime per new alert, arrival confirmation,
  denied permission, offline/reconnect and battery/watch cleanup.
- Controlled approved-recipient SMS only after rendering/persistence checks. No
  unnecessary weather/SMS calls or repeated full-suite runs during planning.
- Deploy behind separate weather/geofence flags, verify real headers/provider data,
  notification routing and role boundaries; rollback disables flags/stops poller
  while preserving evidence. Do not roll back billing/security protections.

## Product decisions to review before activation

- Recommend basic weather warnings for admins and members in both editions; admin
  configuration/team operations follow current entitlements. This is a proposal,
  not a change to the existing Core/Enterprise contract.
- Confirm U.S.-first coverage, monitored shift windows/sites, severity/advisory policy,
  retention and SMS limits. No paid lightning-distance feed has been selected;
  official storm alerts are not live strike-distance detection.
- Cost model: cached weather fetches per unique active area, not per member; bounded
  scheduled CPU/database work plus actual opted-in SMS segments. No NWS data fee;
  Google hosting and Twilio delivery still incur usage. Measure before activation.

## Primary documentation verified October17

- NWS API: https://www.weather.gov/documentation/services-web-api — free public data,
  User-Agent requirement, forecasts/observations/alerts and cache/rate-limit behavior.
- NWS alerts: https://www.weather.gov/documentation/services-web-alerts — official
  CAP watches/warnings/advisories, update timing and polling no faster than30seconds.
- Open-Meteo terms: https://open-meteo.com/en/terms — free API non-commercial only;
  commercial subscriptions separate; attribution applies.
- Browser geolocation: https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API
  — secure context, explicit permission, getCurrentPosition/watchPosition.
- Provider-discovery prerequisite attempted: Stripe CLI absent; stripe.directory
  setup page could not be fetched (unsupported response content type). No software
  installed, account created, subscription purchased or provider credentials obtained.
  Direct official documentation above was used for the planning fallback.

This inspection did not run/import the reference app, request real GPS, exercise
providers with private coordinates, validate live alert delivery or modify V1.
