# Google imagery backend

## Implemented locally

`POST /v2/imagery/streetview/availability` accepts the existing location contract:
`{"address":"Richmond, VA"}` or `{"latitude":37.54,"longitude":-77.43}`.
Coordinates take precedence when both are supplied. This does not verify the address matches the coordinates.

The default application returns `status=not_configured`, `reason=google_access_disabled`.
An operator must explicitly inject `StreetViewMetadata(api_key=...)` into `create_app(imagery_provider=...)` to enable network access. The application does not read existing Google secrets or enable access through environment variables automatically. Do not put credentials in source or request bodies.

The adapter requests only the fixed HTTPS Google Street View metadata endpoint. Redirects are refused, response bodies are limited to 64 KiB, and network operations have a 10-second timeout. Provider errors are sanitized. There are no retries. The timeout is per network operation, not a total job deadline. Transport-level debug logging must remain disabled when credentials are supplied.

Responses distinguish available, empty, unavailable, and not-configured states. Valid requests return HTTP 200 with these explicit states; invalid locations return 422 and remote clients 403. Successful responses include panorama ID, returned coordinates, attribution when present, and capture date at the precision Google supplies. Missing dates remain null. Site matching and current conditions require review; field approval is always false.

This increment downloads no image bytes, stores no Google metadata, changes no saved project, and generates no placements, PDFs, or emails. Availability does not establish image currency, geometry, traffic intensity, or permitted export.

## Recovery and next implementation

Recovered API V17 `main.py` contains `fetch_streetview_image` (line 163), `draw_workzone_overlay` (261), and `/streetview-visual` (1168). Its overlay uses fixed pixels. Preserve that code as a reference; it is not a placement algorithm.

The intended imagery sources are Google Maps satellite/hybrid for overhead context, Street View for ground context, and customer field photos for current conditions. No Earth/satellite retrieval was found in the inspected historical Python sources.

Next: resolve Google imagery display/storage/export permissions for the intended workflow; implement the map display and geographic annotation contract, then connect reviewed evidence and agency references to proposed placements. Traffic overlays require separate dated traffic evidence. Do not infer traffic volume from the number of vehicles visible in a photograph.

## Official references checked 2026-09-17

- [Street View metadata](https://developers.google.com/maps/documentation/streetview/metadata): availability, panorama coordinates, optional partial capture dates and status codes. Google documents metadata calls as free; loading images is separate.
- [Maps Static API](https://developers.google.com/maps/documentation/maps-static/start): map types, custom markers and paths.
- [Street View policies](https://developers.google.com/maps/documentation/streetview/policies): storage and attribution requirements. Permanent image retention and PDF/email embedding are not enabled by this increment.

## Validation

Mock-provider tests exercise partial/missing dates, malformed payloads, missing imagery, denied/quota errors, oversized responses, redirects, coordinate selection, timeouts, redaction, default-disabled behavior and the local-only boundary. These tests do not verify live Google credentials or service availability.

All 62 V2 tests passed. A real Uvicorn loopback request returned HTTP 200 with Google access disabled and field approval false. No cloud resources or V1 code were changed.
