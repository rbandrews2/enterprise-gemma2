"""Prepare a traceable review packet; does not claim model-generated placements."""
from services.v2.planning import discover
from shared.projects import ProjectDraft
from services.v2.advice import review_project
from services.v2.placement import assess_placement


def prepare(record, knowledge):
    draft = ProjectDraft.model_validate(record["draft"])
    references = discover(draft.intake, knowledge)
    questions = []
    location, site = draft.intake.location, draft.intake.site
    for field, value, question in (
        ("locality", location.locality, "Which city or county contains the work area?"),
        ("road_authority", location.road_authority, "Who owns or controls this road? Confirm the responsible authority."),
        ("project_date", draft.intake.project_date, "What is the planned work date?"),
        ("speed_limit", site.speed_limit_mph, "What is the posted speed limit? Supply dated supporting evidence."),
        ("lane_count", site.lane_count, "How many lanes are present?"),
        ("pedestrians", site.pedestrians_present, "Are pedestrians present or affected?"),
        ("intersections", site.intersections_present, "Are intersections affected by the work?"),
    ):
        if value is None:
            questions.append({"id": field, "question": question})
    if site.work_period == "unknown":
        questions.append({"id": "work_period", "question": "Will work occur during daylight, at night, or both?"})
    questions += [
        {"id": "closure_geometry", "question": "Provide the closure type, work limits, travel directions and measured road geometry."},
        {"id": "duration_visibility", "question": "Confirm work duration, sight distance and visibility constraints."},
        {"id": "local_conditions", "question": "Provide applicable local permits, contract conditions and approved traffic-control plans."},
    ]
    geometry = draft.job_geometry
    if geometry:
        questions = [q for q in questions if q["id"] not in {"closure_geometry", "duration_visibility"}]
        for field, value, prompt in (
            ("closure_type", None if geometry.closure_type == "unknown" else geometry.closure_type, "What type of closure is planned?"),
            ("work_limits", geometry.work_limits or None, "Provide at least two reported work-limit points and their source."),
            ("lane_width_ft", geometry.lane_width_ft, "Provide the lane width in feet."),
            ("travel_direction", geometry.travel_direction, "Describe affected travel directions."),
            ("duration_hours", geometry.duration_hours, "Provide the planned work duration in hours."),
            ("available_sight_distance_ft", geometry.available_sight_distance_ft, "Provide measured available sight distance in feet."),
        ):
            if value is None:
                questions.append({"id":field,"question":prompt})
        questions.append({"id":"verify_geometry", "question":"Verify the reported geometry against site measurements before choosing placements."})
    advice = review_project(draft, references.assessment, record["evidence_review"])
    return {
        "project_id": record["project_id"], "project_version": record["version"],
        "project_sha256": record["sha256"], "mode": "source_grounded_preparation",
        "status": "needs_information" if any(q["id"] not in {"local_conditions", "verify_geometry"} for q in questions) else "needs_verified_rules",
        "model_called": False, "placements": [], "approved_for_field_use": False,
        "questions": questions,
        "project_advice": advice,
        "placement_readiness": assess_placement(draft, references),
        "response_summary": {state: sum(a["response_state"] == state for a in advice)
                             for state in ("unanswered", "reported_handled", "needs_help", "stale")},
        "unmatched_response_ids": [r.finding_id for r in draft.review_responses
                                   if r.finding_id not in {a["id"] for a in advice}],
        "form_recommendations": [f.model_dump(mode="json") for f in references.assessment.form_recommendations],
        "evidence_review": record["evidence_review"],
        "references": references.model_dump(mode="json"),
        "blockers": [
            "Governing authority and applicable editions have not been verified.",
            "Locality-specific coverage is not established by a Virginia or federal keyword match.",
            "Measured geometry and reviewed placement rules are not connected.",
            "Gemma inference and annotated imagery generation are not connected.",
        ],
    }
