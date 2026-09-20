# Local project and evidence workspace

The V2 backend now saves project intake, evidence references, and unresolved source-applicability questions. This is a single local development workspace, not an authenticated customer or organization store. It remains loopback-only and must not be deployed or exposed through a proxy.

## Endpoints

| Endpoint | Behavior |
| --- | --- |
| `POST /v2/projects` | Create revision 1; requires an `Idempotency-Key` header of 8–128 letters, digits, dots, underscores, colons or hyphens |
| `GET /v2/projects?limit=20&offset=0` | List latest project summaries; limit 1–50, offset nonnegative |
| `GET /v2/projects/{uuid}` | Retrieve latest saved revision |
| `GET /v2/projects/{uuid}?version=1` | Retrieve a historical revision |
| `PUT /v2/projects/{uuid}` | Replace the full draft, appending a revision; requires `expected_version` |
| `GET /v2/projects/{uuid}/references` | Discover agency reference candidates using the latest saved intake; returns the project version used |

Create accepts `name`, `intake` (the existing intake contract), and optional `evidence` and `applicability_notes` lists. Updates use the same full payload plus `expected_version`; omitted lists become empty in the new revision. Historical revisions remain intact. A stale edit returns HTTP 409 rather than overwriting newer work.

An identical create retry with the same key returns the original project and revision 1, even if later edits exist. Reusing a key with different content returns HTTP 409. Keys are local-workspace scoped. Unknown projects/revisions return 404; invalid inputs return 422; unavailable or detected corrupt storage returns 503. Creation/replay returns 201.

## Evidence records

Projects also support proposed geographic annotations and a version-selectable GeoJSON endpoint. See [geographic annotation contract](GEOGRAPHIC_ANNOTATIONS.md). Full updates must include annotations to retain them in the new revision.

Every record has a unique `id`, `kind`, `source_name`, `source_reference`, `basis`, `road_segment`, optional `observed_on`, and optional `notes`. Basis distinguishes customer reports, official-record claims, field observations, and estimates. The service has not verified any of those claims.

- **Speed:** `kind=speed`, `speed_type` (`posted`, `temporary_authorized`, `design`, `observed`), and `value_mph`. Other speed types do not satisfy the prompt for posted-speed evidence.
- **Traffic:** `kind=traffic`, `metric` (`aadt`, `hourly_volume`, `observed_count`), numeric `value`, `units`, and `direction`. Units must respectively be `vehicles_per_day`, `vehicles_per_hour`, or `vehicles`. Observed counts require `duration_minutes`; durations on other metrics are rejected. No conversion or traffic-intensity inference is performed.
- **Imagery:** `kind=imagery`, `image_type` (`field_photo`, `street_imagery`, `aerial_imagery`, `generated_illustration`), `attribution`, `usage_permission_note`, and optional `declared_sha256`. These are reference records only; no image bytes are uploaded, retrieved, or hash-verified yet. A generated illustration is not counted as actual-site imagery.

Source references are stored as text and never fetched or executed. The evidence review identifies missing dates, future dates, evidence that postdates the job, an intake/posted-speed discrepancy, and missing visual-workflow evidence. It is recalculated on retrieval with an `evidence_review_as_of` date; it is not a saved professional decision. Numeric bounds are input limits, not regulatory rules.

## Applicability questions

Each note contains a catalog `source_id`, preserved document `revision` hash, `section`, and `question`. The server rejects unknown source revisions. The section text itself is a user-entered locator, not a validated citation. Status can only be `pending_review`; the API does not offer approval or a way to declare evidence verified. Full applicability resolution needs qualified reviewer identity, road ownership, dates, project conditions, and official forms.

## Persistence and integration

The database is `.local-data/projects/projects.sqlite`, excluded from Git and cloud/container uploads. Transactions serialize edits; previous revisions are retained, and each payload has a SHA-256 consistency check. Checksums detect accidental content changes, not malicious edits by someone who controls the database. Back up this database separately from the rebuildable agency index. No automated backup or customer data migration is enabled.

The saved-reference endpoint uses the saved intake and the current local agency index. It does not yet incorporate attached evidence into rule applicability or store the returned reference selection as an approved snapshot. Multi-organization access control, attachments, signed asset access, identity-bound review, and production durability remain required before customer use.

## Example create body

```json
{
  "name": "Example striping job",
  "intake": {
    "work_type": "line_striping",
    "location": {"latitude": 37.54, "longitude": -77.43},
    "requested_outputs": ["work_zone_setup", "annotated_image"]
  },
  "evidence": [{
    "id": "speed-01",
    "kind": "speed",
    "source_name": "Crew site observation",
    "source_reference": "Speed-sign photo to be attached later",
    "basis": "customer_report",
    "road_segment": "Confirm project limits",
    "speed_type": "posted",
    "value_mph": 35
  }]
}
```

The response remains `verification_status=not_verified` and `approved_for_field_use=false`. A recorded speed and image reference do not authorize placement.

## Validation

All 56 tests passed across the V2 suite. Project tests cover retries, restart persistence, history, stale/concurrent edits, traffic unit validation, unverified imagery, date/speed discrepancies, pending source notes, corruption detection, pagination, and rejection of nonlocal clients. A real HTTP test created and edited a project, restarted the server, then retrieved both revisions and reference discovery using the saved intake. Only synthetic test data was used; V1 and cloud resources were unchanged.
