"""Discovery results are explicitly separate from applicable project requirements."""
from datetime import date, datetime
from typing import Literal

from pydantic import Field
from shared.contracts import StrictModel
from shared.intake import IntakeAssessment


class ReferenceCandidate(StrictModel):
    source_id: str
    agency: Literal["VDOT", "FHWA", "OSHA", "VOSH"]
    title: str
    edition: str | None
    revision: str = Field(pattern=r"^[a-f0-9]{64}$")
    text: str
    url: str
    page: int | None = None
    section: str | None = None
    retrieved_at: datetime
    effective_from: date | None = None
    effective_to: date | None = None
    review_status: str
    publication_status: str
    extraction_checked: bool
    warnings: list[str]
    applicability_status: Literal["unresolved"] = "unresolved"
    match_basis: Literal["keyword_match_only"] = "keyword_match_only"


class ReferenceTopic(StrictModel):
    id: str
    query: str
    reason: str
    status: Literal["candidates_found", "no_candidates", "library_unavailable"]
    candidates: list[ReferenceCandidate]


class SourceAvailability(StrictModel):
    source_id: str
    agency: Literal["VDOT", "FHWA", "OSHA", "VOSH"]
    status: Literal["searchable", "not_downloaded", "extraction_unavailable", "superseded", "index_stale", "index_unavailable"]
    last_attempt_status: str
    note: str


class PlanningReferences(StrictModel):
    schema_version: Literal["2.0"] = "2.0"
    assessment: IntakeAssessment
    library_status: Literal["available", "unavailable"]
    project_date: date | None
    topics: list[ReferenceTopic]
    source_availability: list[SourceAvailability]
    coverage_gaps: list[str]
    requirements_determined: Literal[False] = False
    approved_for_field_use: Literal[False] = False
