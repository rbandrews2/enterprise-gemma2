# Structured geometry and Google site view

## Job inputs

The local workspace now edits locality, reported road authority, project coordinates/date, posted speed, lane count, work period, pedestrian/intersection conditions, closure type, duration, lane width, available sight distance, travel directions, geometry source and work-limit points. Saving appends a project revision and retains evidence, markers and review responses. Changes invalidate earlier response context fingerprints.

`job_geometry` is optional on project drafts. Work limits are a reported polyline containing at least two distinct latitude/longitude points, up to 200, and require a source reference. Coordinates must be finite and within global bounds. Numeric bounds are input limits, not agency rules. Geometry remains `customer_reported`. It is not surveyed, checked for self-intersections, snapped to roads or used to calculate regulatory spacing. This is not yet a lane model. Atlas asks for missing geometry fields and retains the verification question when fields are populated.

Existing records remain readable. Absent geometry is excluded from canonical saves and review fingerprints so older create retries and response contexts remain compatible.

## Google integration

The workspace loads Google Maps JavaScript only after **Load Google map**. It displays hybrid imagery with reported work limits and proposed marker points. Map controls allow changing map type; clicking a marker point selects its editor. **Show Street View at project location** requests a nearby panorama, reports unavailable imagery/errors, and shows the provider capture date if returned. Panoramas can be offset from the requested position; operators must confirm the site. Overhead points are not projected into Street View.

No geocoding, image download, storage, screenshot, PDF/email imagery export, traffic heatmap, or AI placement is included. Rendering uses Google's own map/panorama widgets and attribution. The application does not cache imagery. API use can incur charges and sends displayed locations to Google; no fixed cost estimate is asserted here.

### Configuration

Set `WZOS_GOOGLE_MAPS_BROWSER_KEY` only to a Maps JavaScript browser key restricted to the intended website referrers and APIs. This key is deliberately sent to the browser through the local-only `/v2/maps/config` endpoint; it is not a server secret. Configure website restrictions, enable the Maps JavaScript API and billing, and set suitable quotas in Google Cloud before live use. Do not substitute the legacy `GOOGLE_MAPS_API_KEY` server credential. Do not commit either key. `Cache-Control: no-store` is set on the configuration response.

No browser key was configured in the inspected environment. No cloud API, key, restriction or billing setting was changed. Live image rendering is therefore **not verified**. The missing-key path displays a configuration message and makes no Google script request.

Live Cloud Console follow-up on 2026-09-20 found the existing `GOOGLE_MAPS_API_KEY` secret (version 1 enabled), and enabled Geocoding, Maps Static and Street View Static APIs. The project's Credentials page listed no API keys, and Maps JavaScript was absent from the enabled-services inventory. Existing credentials must be traced and checked before adding or reusing a browser key. See [Must complete before launch](MUST_COMPLETE_BEFORE_LAUNCH.md).

Official documentation checked 2026-09-20:

- [Google Maps JavaScript setup](https://developers.google.com/maps/documentation/javascript/get-api-key)
- [Load the API](https://developers.google.com/maps/documentation/javascript/load-maps-js-api)
- [Troubleshooting key, billing and restriction failures](https://developers.google.com/maps/documentation/javascript/troubleshooting)

## Verification

### Scenario and measured approaches — 2026-09-20

The job editor now saves an explicit reference scenario and road classification. Stationary-shoulder selection requires the shoulder closure type. Up to eight named approaches each preserve an ordered upstream-to-work-area path, travel direction, measurement source/date, lane width, sight distance and obstruction/access notes. Future measurement dates, blank descriptions, duplicate IDs, invalid coordinates and consecutive duplicate points are rejected. Measurements remain customer reports, not verified engineering geometry. Blue approach polylines are added to an already-loaded Google map; work limits remain orange. The live Google rendering of the new approach lines has not yet been tested.

**Preview source table values** uses the saved scenario, road class and posted speed. It refuses unsaved edits, labels the saved revision, shows supported table values with page/hash citation, and keeps all limitations visible. It never generates markers. Optional new geometry fields are omitted when unused to preserve earlier project hashes and Atlas response fingerprints. Save operations preserve existing project evidence and history.

All 84 tests passed, including persistence/conflicts, validation, legacy hash compatibility and placement gating. A browser test on an isolated synthetic project saved measurements into revision 2 and successfully displayed the cited preview. The test server was stopped; no production data changed.

All 76 V2 tests passed, including geometry validation, compatibility and browser/server credential separation. Browser testing saved a synthetic two-point line with a source reference in revision 2 and verified the explicit missing-key state. Successful live map/Street View rendering, production referrer restrictions, quota behavior and imagery export permissions remain to be verified with the configured Google project. Tests did not call paid APIs.

## Live Maps verification — 2026-09-20

The dedicated browser key is configured locally in `.local-data/credentials/wzos-v2-browser-key.txt` (Git ignored). Run `./scripts/start_v2_local.ps1` from PowerShell; it loads the key into the child server environment without printing it, binds to 127.0.0.1:8081, and restores the prior environment on exit. An alternate key file can be supplied with `-BrowserKeyFile`.

Live browser checks against an isolated synthetic Norfolk project (36.8508, -76.2859) successfully loaded Google's hybrid map with attribution and a nearby Street View panorama. Street View reported capture date 2022-09 and a nearby location, not the exact requested coordinate. No customer project was created or changed. The test server was stopped. All 76 tests passed; launcher syntax parsing passed. No imagery was downloaded or exported. Production referrer behavior, quotas/cost limits, marker overlays, missing imagery cases and export permissions still need validation.
