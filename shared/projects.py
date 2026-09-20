"""Local project records retain evidence claims without granting verification."""
from datetime import date
from typing import Annotated, Literal

from pydantic import Field, model_validator

from shared.contracts import StrictModel
from shared.intake import IntakeRequest
from shared.annotations import GeographicAnnotation


class EvidenceBase(StrictModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    source_name: str = Field(min_length=1, max_length=300)
    source_reference: str = Field(min_length=1, max_length=2000)
    basis: Literal["official_record", "field_observation", "estimate", "customer_report"]
    observed_on: date | None = None
    road_segment: str = Field(min_length=1, max_length=500)
    notes: str = Field(default="", max_length=2000)


class SpeedEvidence(EvidenceBase):
    kind: Literal["speed"]
    speed_type: Literal["posted", "temporary_authorized", "design", "observed"]
    value_mph: float = Field(gt=0, le=150, allow_inf_nan=False, strict=True)


class TrafficEvidence(EvidenceBase):
    kind: Literal["traffic"]
    metric: Literal["aadt", "hourly_volume", "observed_count"]
    value: float = Field(ge=0, allow_inf_nan=False, strict=True)
    units: Literal["vehicles_per_day", "vehicles_per_hour", "vehicles"]
    duration_minutes: int | None = Field(default=None, gt=0, le=10080, strict=True)
    direction: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def match_units(self):
        expected = {"aadt": "vehicles_per_day", "hourly_volume": "vehicles_per_hour", "observed_count": "vehicles"}
        if self.units != expected[self.metric]:
            raise ValueError("Traffic units do not match the metric")
        if self.metric == "observed_count" and self.duration_minutes is None:
            raise ValueError("Observed counts need the measurement duration")
        if self.metric != "observed_count" and self.duration_minutes is not None:
            raise ValueError("Duration applies only to observed counts")
        return self


class ImageryEvidence(EvidenceBase):
    kind: Literal["imagery"]
    image_type: Literal["field_photo", "street_imagery", "aerial_imagery", "generated_illustration"]
    attribution: str = Field(min_length=1, max_length=500)
    usage_permission_note: str = Field(min_length=1, max_length=1000)
    declared_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


Evidence = Annotated[SpeedEvidence | TrafficEvidence | ImageryEvidence, Field(discriminator="kind")]


class ApplicabilityNote(StrictModel):
    source_id: str = Field(pattern=r"^[a-z][a-z0-9-]{1,79}$")
    revision: str = Field(pattern=r"^[a-f0-9]{64}$")
    section: str = Field(min_length=1, max_length=200)
    question: str = Field(min_length=1, max_length=2000)
    status: Literal["pending_review"] = "pending_review"


class ProjectDraft(StrictModel):
    name: str = Field(min_length=1, max_length=200)
    intake: IntakeRequest
    evidence: list[Evidence] = Field(default_factory=list, max_length=100)
    applicability_notes: list[ApplicabilityNote] = Field(default_factory=list, max_length=100)
    annotations: list[GeographicAnnotation] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def unique_evidence(self):
        if len({e.id for e in self.evidence}) != len(self.evidence):
            raise ValueError("Evidence IDs must be unique within a revision")
        if len({a.id for a in self.annotations}) != len(self.annotations):
            raise ValueError("Annotation IDs must be unique within a revision")
        evidence = {e.id: e for e in self.evidence}
        for annotation in self.annotations:
            if any(ref not in evidence for ref in annotation.evidence_ids):
                raise ValueError("Annotation references missing evidence in this revision")
            if annotation.kind == "traffic_observation" and not any(
                evidence[ref].kind == "traffic" for ref in annotation.evidence_ids
            ):
                raise ValueError("Traffic markers require traffic evidence")
        return self


class ProjectUpdate(ProjectDraft):
    expected_version: int = Field(ge=1, strict=True)
