"""Placement readiness policy, not a traffic engineering rule engine."""

POLICY_VERSION = "placement-readiness-1"


def assess_placement(draft, references):
    location, site, geometry = draft.intake.location, draft.intake.site, draft.job_geometry
    checks = []

    def reported(identifier, present, action):
        checks.append({"id": identifier, "status": "reported_unverified" if present else "missing",
                       "next_action": action})

    reported("location", location.latitude is not None, "Supply and confirm work-area coordinates.")
    reported("authority", bool(location.road_authority), "Confirm road ownership and governing authority; a city name is insufficient.")
    reported("work_date", draft.intake.project_date is not None, "Confirm the work date and contract/permit edition requirements.")
    reported("posted_speed", site.speed_limit_mph is not None, "Verify the posted speed using dated site evidence.")
    reported("closure", geometry is not None and geometry.closure_type != "unknown", "Confirm the closure scenario before selecting a typical application.")
    reported("work_limits", bool(geometry and geometry.work_limits), "Verify measured work limits against the site.")
    reported("sight_distance", bool(geometry and geometry.available_sight_distance_ft is not None), "Check available sight distance separately for each approach and proposed flagger station.")
    reported("lane_width", bool(geometry and geometry.lane_width_ft is not None), "Verify lane widths and usable roadway width.")
    reported("travel_direction", bool(geometry and geometry.travel_direction), "Confirm traffic direction on each affected approach.")
    reported("duration", bool(geometry and geometry.duration_hours is not None), "Confirm duration and whether the operation moves along the road.")
    reported("pedestrians", site.pedestrians_present is not None, "Verify pedestrian and accessible-route needs.")
    reported("intersections", site.intersections_present is not None, "Verify intersecting streets, driveways and access constraints.")
    # These cannot become approved from customer text or a keyword match.
    for identifier, action in (
        ("edition_applicability", "Review governing editions, permit/contract exceptions and local requirements."),
        ("approach_geometry", "Supply measured approach paths, travel orientation, lane boundaries and obstructions. Work-limit lines alone are insufficient."),
        ("reviewed_rule", "Validate the selected typical application, tables, notes and exceptions against a pinned document revision."),
        ("field_review", "Have a qualified reviewer check the resulting plan against current site conditions."),
    ):
        checks.append({"id": identifier, "status": "review_required", "next_action": action})
    return {
        "policy_version": POLICY_VERSION,
        "basis": "wzos_readiness_policy_not_agency_requirements",
        "status": "missing_inputs" if any(c["status"] == "missing" for c in checks) else "review_required",
        "checks": checks,
        "reference_candidate_count": sum(len(t.candidates) for t in references.topics),
        "reviewed_rule_count": 0,
        "can_generate_placements": False,
        "approved_for_field_use": False,
    }
