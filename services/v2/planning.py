"""Deterministic topic discovery using only the local approved-source index."""
from shared.intake import IntakeRequest
from shared.planning import PlanningReferences, ReferenceCandidate, ReferenceTopic, SourceAvailability
from services.v2.intake import assess
from services.v2.knowledge.store import Store, IndexUnavailable


def topics_for(request):
    topics = [
        ("traffic_control", "temporary traffic control", ("VDOT", "FHWA"), "Work-zone context for this job."),
        ("worker_safety", "safety", ("OSHA", "VOSH"), "Worker-safety references to review alongside the JSA recommendation."),
    ]
    if set(request.requested_outputs) & {"work_zone_setup", "annotated_image"}:
        topics += [("advance_warning", "advance warning", ("VDOT", "FHWA"), "The requested setup or image needs warning-sign review."),
                   ("flaggers", "flagger", ("VDOT", "FHWA"), "Determine whether and how flagging applies before positioning icons.")]
    if request.work_type == "line_striping":
        topics.append(("striping", "marking", ("VDOT", "FHWA"), "Customer selected line striping."))
    if "traffic_overlay" in request.requested_outputs:
        topics.append(("traffic_volume", "traffic volume", ("VDOT", "FHWA"), "Customer requested a traffic overlay; reference text is not measured site traffic."))
    if request.work_type == "underground_utility":
        topics.append(("utility", "utility", ("VDOT", "FHWA"), "Customer selected underground utility work."))
    if request.site.excavation_planned is True:
        topics.append(("excavation", "excavation", ("OSHA", "VOSH"), "Customer reported planned excavation."))
    if request.site.work_period in {"night", "mixed"}:
        topics.append(("night_work", "night", ("VDOT", "FHWA"), "Customer reported night or mixed-period work."))
    if request.site.pedestrians_present is True:
        topics.append(("pedestrians", "pedestrian", ("VDOT", "FHWA"), "Customer reported pedestrians."))
    if request.site.intersections_present is True:
        topics.append(("intersections", "intersection", ("VDOT", "FHWA"), "Customer reported intersections."))
    return topics


def discover(request: IntakeRequest, store: Store) -> PlanningReferences:
    availability, revisions = {}, {}
    for source_id, source in store.catalog.items():
        detail = store.detail(source_id)
        current = detail["revisions"][0] if detail["revisions"] else None
        status, note = "searchable", "Downloaded text is available for candidate discovery, not project approval."
        if source.publication_status == "superseded":
            status, note = "superseded", "Excluded from automatic candidate discovery; historical search remains available."
        elif current is None:
            status, note = "not_downloaded", "No downloaded source text is available."
        elif current["extraction_state"] != "extracted":
            status, note = "extraction_unavailable", "The current download lacks a usable extraction."
        if current:
            revisions[source_id] = current["revision"]
        availability[source_id] = SourceAvailability(
            source_id=source_id, agency=source.agency, status=status,
            last_attempt_status=detail["ingestion"]["status"], note=note,
        )

    groups = []
    library_status = "available"
    try:
        indexed = store.indexed_revisions()
        for source_id, item in availability.items():
            if item.status == "searchable" and indexed.get(source_id) != revisions[source_id]:
                item.status = "index_stale"
                item.note = "The latest download is not in the index; rebuild before discovery."
        for topic_id, query, agencies, reason in topics_for(request):
            matches = {agency: [] for agency in agencies}
            for source_id, source in store.catalog.items():
                if source.agency not in agencies or availability[source_id].status != "searchable":
                    continue
                found = store.search(query, source_id=source_id, limit=1, latest_only=True)
                for row in found["results"]:
                    if row["revision"] != revisions[source_id]:
                        availability[source_id].status = "index_stale"
                        availability[source_id].note = "Indexed revision differs from the latest download; rebuild before discovery."
                        continue
                    matches[source.agency].append(row)
            candidates = []
            for agency in agencies:
                # At most two source passages per agency; stable global FTS rank.
                for row in sorted(matches[agency], key=lambda r: (r["rank"], r["source_id"]))[:2]:
                    fields = {key: row[key] for key in ReferenceCandidate.model_fields if key in row}
                    candidates.append(ReferenceCandidate(**fields))
            groups.append(ReferenceTopic(id=topic_id, query=query, reason=reason,
                                        status="candidates_found" if candidates else "no_candidates", candidates=candidates))
    except IndexUnavailable:
        library_status = "unavailable"
        groups = [ReferenceTopic(id=tid, query=query, reason=reason, status="library_unavailable", candidates=[])
                  for tid, query, _, reason in topics_for(request)]
        for item in availability.values():
            if item.status == "searchable":
                item.status = "index_unavailable"
                item.note = "Downloaded text exists, but the search index is unavailable."

    gaps = [
        "Keyword matches are reference candidates, not a determination of governing requirements or sign/flagger placement.",
        "Road ownership, jurisdiction, locality rules, permit/contract conditions, and project dates still require verification.",
        "The project date is recorded but does not automatically establish the applicable edition; effective dates and exceptions require review.",
        "Official required-form selection and complete OSHA/VOSH standards coverage are not implemented; no match does not mean no requirement.",
        "Live traffic, site imagery, verified geometry, and qualified layout review are not connected.",
        "Reference freshness is based on the last local retrieval; no website refresh occurs during this request.",
    ]
    return PlanningReferences(assessment=assess(request), library_status=library_status,
                              project_date=request.project_date, topics=groups,
                              source_availability=list(availability.values()), coverage_gaps=gaps)
