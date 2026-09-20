# Geographic annotation increment

Implemented 2026-09-20. No Google calls, cloud resources or new dependencies are needed.

Project create/update bodies now accept `annotations` (maximum 200). Each marker has a unique `id`, `kind` (`sign`, `flagger`, `work_area`, `traffic_observation`), `label`, `latitude`, `longitude`, a `rationale`, optional `evidence_ids`, and a fixed `status=proposed`.

Coordinates are finite decimal degrees within global latitude/longitude bounds. They are operator-supplied, not geocoded, snapped to roads or verified against the project address. A work-area marker is a point identifying a location, not a polygon or boundary. Labels and rationale are plain untrusted text; future clients must render them as text, not HTML.

Evidence references must exist in the same project revision. Traffic markers must reference at least one traffic evidence record. This checks record linkage only, not location, date, accuracy or applicability. No high-traffic classification, regulatory spacing or automatic placement is computed. Supporting agency questions remain available in the project's applicability notes; markers do not yet have independently validated agency citations.

`GET /v2/projects/{uuid}/annotations?version=1` returns a GeoJSON FeatureCollection for the chosen revision (latest by default), with point coordinates in longitude, latitude order. It includes the project version and `approved_for_field_use=false`. An empty list is a valid empty collection; existing 404, 422, 503 and local-only access handling applies.

Annotations are saved through existing project POST/PUT operations with append-only history and stale-edit protection. PUT remains full replacement: omitted annotations become empty in the new version. Deleting evidence still referenced by a marker is rejected. Older project records load with an empty list; their original checksums remain checked against the original saved bytes. Empty annotations are omitted from canonical writes to preserve older create-idempotency hashes.

## Next

Validation: all 66 V2 tests passed, including annotation history, coordinate order, evidence linkage, invalid inputs, approval rejection and legacy canonical compatibility. A real loopback HTTP test created a temporary annotated project and retrieved its GeoJSON. No real customer data or live imagery was used.

Build map display and marker editing on top of this contract. Verify Google usage permissions before imagery retrieval, persistence or PDF/email export. Add measured road geometry and reviewed source-linked placement proposals separately. Current imagery access stays disabled by default; no field-use approval is implemented.
