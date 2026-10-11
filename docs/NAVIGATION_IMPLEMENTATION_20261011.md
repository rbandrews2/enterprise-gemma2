# In-app Navigation implementation — October 11, 2026

## Implemented locally

- Authenticated availability and read-only route endpoints; only permitted
  organization work orders or the current employee's active Enterprise dispatch
  assignment may supply a destination. Assignment destinations are frozen.
- Dedicated server Routes credential, explicit enable flag, fixed HTTPS provider
  endpoint, narrow field mask, one request, bounded response/timeout, rate and
  concurrency limits. No startup DDL or new dependency.
- Responsive glass-card route panel: manual starting address or explicit location
  request, manual calculation, route line, directions, distance and timestamped
  duration. Google traffic fallback status is visible. Text directions remain
  when map rendering fails. Session/view/offline changes clear routes and cancel
  browser requests; no background tracking or offline-routing claim.
- Missing assignment endpoint no longer hides permitted work orders. HTTP 403
  still blocks display; optional unavailable assignments are explicitly labeled.
- Atlas app guidance describes the new controls and configuration dependency.
  Google Maps external directions and saved destination sheets remain fallbacks.

## Actual evidence

- Focused Python: 16 cases, 10 passed, six PostgreSQL cases skipped because a
  dedicated test database was not configured locally. Provider transport is fake;
  access checks use the real account/dispatch application with synthetic users.
- Full Node: 56 passed, zero failures/skips. Includes manual location/calculate,
  disabled provider, successful map drawing, failed map retaining directions,
  session cancellation, and unavailable/forbidden assignment responses.
- Real local HTTP: authenticated synthetic admin session and Navigation config
  returned successfully; routes/maps unavailable flags are accurate. A newly
  created UUID work order returned503 for unconfigured routing; a member requesting
  that private admin work order returned404; anonymous config returned401. Historical
  seeded preview IDs are non-UUID and correctly fail request validation; provider
  acceptance must use normally created UUID jobs.
- Real desktop browser: permitted work-order destination and Route inside WZOS
  panel rendered. Calculate is disabled until routing is configured. No location
  permission was requested automatically.
- Phone-sized browser: document width/scroll width both375px; route panel fits.
  This is a responsive browser check, not Android device acceptance.
- Screenshots in ignored `.local-data/navigation-route-desktop-20261011.png` and
  `navigation-route-mobile-20261011.png`. Local preview on127.0.0.1:8083.
- Full Python regression was started, log `.local-data/navigation-python-gate.log`;
  final result must be captured before release acceptance. It had reached the
  messaging tests with no observed failure when Cloud Shell control stalled.

## Cloud status and next checkpoint

Ray explicitly approved NAVIGATION_STAGING_ACTIVATION.md: Routes API enablement,
dedicated Routes-only key, secret, and secret-scoped runtime accessor grant.
Read-only inventory showed no dedicated Routes key/secret before execution.
The Cloud Shell command was submitted, then browser control timed out before its
result could be read. Ray subsequently reported `ROUTES_SETUP_COMPLETE` while
refreshing the shell connection. **Independent completion verification remains
open.** Do not create duplicates or
repeat grants blindly. Inspect key restriction metadata, API enablement, secret
version metadata and IAM binding without revealing the key value.

No routing deployment, live Google route request, main traffic promotion, V1/DNS
change or Twilio send occurred in this increment. Twilio remains on hold.

Next: collect full local Python result; commit/push the candidate; run exact
candidate disposable PostgreSQL gate and verify cleanup; reconcile cloud setup;
inspect/apply low aggregate quotas and current billing; build/private-tag candidate
with pinned Routes secret; perform capped twenty-route/twenty-map synthetic
provider checks and Android acceptance. Main accepted revision remains unchanged.
No claims of background/voice/native turn-by-turn navigation in this web viewer.

Review contracts: NAVIGATION_API_CONTRACT.md and NAVIGATION_STAGING_ACTIVATION.md.
