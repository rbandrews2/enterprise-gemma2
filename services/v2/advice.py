"""Cross-workflow gap review. Product suggestions are not legal determinations."""
import hashlib
import json


def context_hash(draft):
    payload = draft.model_dump(mode="json", exclude={"review_responses"})
    if payload.get("job_geometry") is None:
        payload.pop("job_geometry", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def review_project(draft, assessment, evidence_review):
    advice = []

    def add(id, category, finding, reason, action, priority="review", state="unknown"):
        advice.append(dict(id=id, category=category, state=state, priority=priority,
                           finding=finding, reason=reason, next_action=action,
                           basis="wzos_project_review_policy", legally_required=None))

    for item in assessment.attention_items:
        if item.category == "capability_gap":
            continue
        add("intake_" + item.id, "project_context", item.message,
            "Job conditions determine which guidance and workflow apply.",
            "Confirm this item and record the supporting project information.",
            "needs_input" if item.category == "missing_information" else "review",
            "missing" if item.category == "missing_information" else "unverified")

    for issue in evidence_review["issues"]:
        add("evidence_" + hashlib.sha256(issue.encode()).hexdigest()[:24], "evidence", issue,
            "Planning decisions need relevant, traceable site evidence.",
            "Supply or verify the evidence and resolve discrepancies.", state="unverified")

    for output in assessment.requested_outputs:
        add("delivery_" + output.output, "requested_function", output.reason,
            f"The customer requested {output.output.replace('_', ' ')}.",
            "Confirm the intended deliverable and arrange the missing implementation or review step.",
            priority="capability_gap", state="not_implemented")

    # These records are not modeled yet: ask about them rather than asserting absence.
    add("forms_inventory", "forms", "Project form inventory and applicability have not been evaluated.",
        "Required and useful records depend on the authority, activity, contract and project conditions.",
        "List existing forms; review permits, traffic-control plans, inspections, crew briefings and other applicable records.")
    add("crew_readiness", "operations", "Crew assignments and readiness are unknown.",
        "A usable work plan needs responsible personnel, equipment and relevant training.",
        "Confirm roles, equipment, training records and any applicable qualifications.")
    add("coordination", "operations", "Scheduling, dispatch and communication arrangements are unknown.",
        "Crews need coordinated work windows, access and a way to communicate changes.",
        "Review schedule, dispatch, navigation/access instructions, employee messaging and emergency contacts.")
    add("recordkeeping", "operations", "Project tracking and integration needs have not been assessed.",
        "Some jobs need time records, progress tracking or information exchanged with other systems.",
        "Confirm whether time clock, tracking and app integrations are needed for this project.")
    for form in assessment.form_recommendations:
        add("form_" + form.form_id, "forms", form.title + " is a suggested review item.",
            form.reason, "Check whether an equivalent current record already exists before creating another.",
            priority="recommended")
    digest = context_hash(draft)
    responses = {r.finding_id: r for r in draft.review_responses}
    for item in advice:
        response = responses.get(item["id"])
        item["context_sha256"] = digest
        item["customer_response"] = response.model_dump() if response else None
        item["response_state"] = ("unanswered" if response is None else
                                  "stale" if response.context_sha256 != digest else
                                  "needs_help" if response.disposition == "needs_help" else "reported_handled")
        item["verification_status"] = "not_verified"
    return advice
