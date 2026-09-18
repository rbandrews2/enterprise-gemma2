# Customer workflow and situational assessment

## Confirmed product direction

WZOS 2.0 brings work-zone planning and workforce operations into one customer experience. Customers supply work type, job location (address or latitude/longitude), and desired outputs: setup, required/recommended forms, annotated imagery, traffic visualization, PDF, and email delivery. Atlas/Gemma should proactively identify missing information and useful recommendations beyond the customer's selected outputs.

The unified product also includes time clock/tracking, employee messaging, integrations, dispatch, navigation, video training, and schedule management. Those modules should share authenticated organization, employee, and job context. Their integrations remain future work; this backend does not claim to provide them.

## Implemented intake increment

`POST /v2/intake/assess` accepts:

- `work_type`: `line_striping`, `underground_utility`, `road_maintenance`, or `other` (with `work_description`).
- `location`: address and/or a complete numeric coordinate pair. `state` defaults to VA for this service market; `locality` and `road_authority` can initially be unknown. Coordinates are range-checked but not geocoded; a VA label does not prove the coordinates lie in Virginia. When both location formats are supplied, reconciliation is explicitly requested.
- `requested_outputs`: one or more of `work_zone_setup`, `required_forms`, `recommended_forms`, `annotated_image`, `traffic_overlay`, `pdf_package`, `email_delivery`.
- Optional `requested_forms: ["jsa"]`, `project_date`, and `site` context: speed in mph, lane count, traffic notes, work period, pedestrians, intersections, excavation.

The response contains a strong JSA recommendation, missing-information and context-review items, and an honest status for each requested output. A requested JSA is acknowledged once; an omitted JSA is proactively recommended. This is WZOS product policy requested by Ray, not a determination that every job legally requires a JSA form.

Rules prompt for unknown conditions and call attention to supplied night work, pedestrians, intersections, utility work, and striping operation details. They do not infer those conditions from photographs or free text. Nullable flags distinguish unknown from customer-reported absence. Supplied values remain unverified. Numeric caps are input sanity limits, not regulatory thresholds.

Example:

```json
{
  "work_type": "underground_utility",
  "location": {"latitude": 37.54, "longitude": -77.43},
  "requested_outputs": ["work_zone_setup", "required_forms", "annotated_image"],
  "site": {"work_period": "night", "pedestrians_present": true}
}
```

The assessment prompts for missing jurisdiction, dates, traffic, speed, roadway information, and excavation context; raises night/pedestrian review topics; and strongly recommends a JSA. It does not create a layout or approved package. All generated deliverables remain `not_implemented`; `regulatory_requirements_status` remains `not_evaluated` and `approved_for_field_use` remains false. The standalone assessment does not persist intake or send it elsewhere. The separate [project workspace](PROJECT_WORKSPACE.md) now supports saving intake and evidence references locally with revision history.

## Next workflow increments

1. Resolve/confirm the location, roadway ownership and project dates, then select applicable agency material and form versions with citations. Separate verified requirements, recommendations and unanswered questions in the customer experience.
2. Connect actual site imagery and dated, geolocated traffic evidence. A high-traffic overlay must state what was measured or estimated, the time period, units, segment and direction; image appearance alone cannot establish traffic volume.
3. Add editable image annotations for signs, flaggers and other devices. Proposed placement needs site geometry, sight-distance/context checks, applicable VDOT/FHWA provisions, and qualified review. Do not treat an icon on an uncalibrated photograph as a measured setup.
4. Assemble forms and images into a versioned PDF, bind approval to the revision and recipients, and implement delivery with recorded outcomes.
5. Integrate these job records into the unified WZOS workforce modules. Replace the historical V1 UI through a separate design/integration milestone.

The current increment is a deterministic intake assistant behind the future interface, not model-driven situational awareness. It makes gaps explicit while the evidence-backed planning capabilities are developed. The live V1 site, Cloud Shell checkout, and Google Cloud deployment remain unchanged.

Validation: 35 automated tests passed across intake, source ingestion/search, and the existing preview. A real loopback HTTP request verified coordinate intake, an unrequested strong JSA recommendation, night-work context, and unapproved output status. V1 main.py remains unchanged.
