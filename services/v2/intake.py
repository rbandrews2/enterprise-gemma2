"""Transparent prompts for missing context, never inferred site conditions or rules."""
from shared.intake import (
    AttentionItem, FormRecommendation, IntakeAssessment, IntakeRequest, OutputAssessment,
)


OUTPUT_GAPS = {
    "work_zone_setup": "Applicable-rule selection, verified roadway geometry, and reviewed sign/flagger placement are not implemented.",
    "required_forms": "Jurisdiction and activity-specific form applicability has not been evaluated.",
    "recommended_forms": "Project-specific form inventory, applicability review and form generation are not implemented.",
    "annotated_image": "Geographic annotation editing exists; actual site imagery and verified placement are not connected.",
    "traffic_overlay": "Geolocated, dated traffic measurements and map rendering are not connected. A photograph alone does not establish traffic volume or current conditions.",
    "pdf_package": "Structured package composition and PDF rendering are not implemented in V2.",
    "email_delivery": "Recipient approval, durable delivery, and an email provider are not connected.",
}


def assess(request: IntakeRequest) -> IntakeAssessment:
    items = []

    def add(item_id, category, message):
        items.append(AttentionItem(id=item_id, category=category, message=message))

    add("verify_location", "context_review", "Confirm the work-zone location, road ownership, and project limits against the actual site.")
    if request.location.address and request.location.latitude is not None:
        add("reconcile_location", "context_review", "Check that the supplied address and coordinates identify the same job; neither has been verified.")
    for field, label in [("locality", "city/county"), ("road_authority", "governing road authority")]:
        if getattr(request.location, field) is None:
            add(field, "missing_information", f"Identify the {label} for applicable requirements and forms.")
    if request.project_date is None:
        add("project_date", "missing_information", "Provide the work date; contract and permit dates may also affect the applicable edition.")

    setup_requested = bool(set(request.requested_outputs) & {"work_zone_setup", "annotated_image", "traffic_overlay"})
    if setup_requested:
        for field, message in [
            ("speed_limit_mph", "Provide the posted speed and its source; a setup cannot use a guessed speed."),
            ("lane_count", "Provide lane count and roadway geometry, including widths, direction, and work limits."),
            ("traffic_notes", "Provide traffic information with collection date, units, road segment, and direction."),
        ]:
            if getattr(request.site, field) is None:
                add(field, "missing_information", message)
        add("verify_site_evidence", "context_review", "Verify supplied speed, traffic, geometry, and imagery before choosing sign, buffer, or flagger positions. Customer entries are not verified measurements.")
        add("placement_engine", "capability_gap", "No site-specific placement or high-traffic map is produced by this intake assessment.")

    if request.site.work_period == "unknown":
        add("work_period", "missing_information", "Confirm whether work occurs during the day, at night, or both.")
    elif request.site.work_period in {"night", "mixed"}:
        add("night_work", "context_review", "Include visibility, lighting, and nighttime working conditions in the job review.")

    for field, label in [("pedestrians_present", "pedestrian and accessible-route needs"),
                         ("intersections_present", "intersections, access points, and turning movements")]:
        value = getattr(request.site, field)
        if value is None:
            add(field, "missing_information", f"Check the site for {label}; this information is unknown.")
        elif value:
            add(field, "context_review", f"Include {label} in the planning review.")

    if request.work_type == "underground_utility" or request.site.excavation_planned:
        add("utility_work", "context_review", "Confirm utility-location, excavation, permit, and access conditions with the responsible personnel; do not assume which requirements apply.")
        if request.site.excavation_planned is None:
            add("excavation_planned", "missing_information", "Confirm whether excavation is part of this underground-utility job.")
    if request.work_type == "line_striping":
        add("striping_operation", "context_review", "Confirm whether striping is moving or stationary, and describe crew/equipment movements and traffic exposure.")

    requested = "jsa" in request.requested_forms
    jsa = FormRecommendation(
        customer_requested=requested,
        reason=("Include the requested JSA in the job review." if requested else
                "WZOS strongly recommends a JSA even though it was not requested, to review job tasks, hazards, and controls with the crew.")
               + " Whether a particular form is legally required has not been determined.",
    )
    return IntakeAssessment(
        form_recommendations=[jsa], attention_items=items,
        requested_outputs=[OutputAssessment(output=output, reason=OUTPUT_GAPS[output])
                           for output in request.requested_outputs],
    )
