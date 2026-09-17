"""Customer intake and transparent rule-based needs assessment."""
from datetime import date
from typing import Literal

from pydantic import Field, model_validator

from shared.contracts import StrictModel

Deliverable = Literal["work_zone_setup", "required_forms", "recommended_forms", "annotated_image", "traffic_overlay", "pdf_package", "email_delivery"]


class JobLocation(StrictModel):
    address: str | None = Field(default=None, min_length=1, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False, strict=True)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False, strict=True)
    state: Literal["VA"] = "VA"
    locality: str | None = Field(default=None, min_length=1, max_length=200)
    road_authority: str | None = Field(default=None, min_length=1, max_length=200)

    @model_validator(mode="after")
    def require_location(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitude and longitude must be supplied together")
        if not self.address and self.latitude is None:
            raise ValueError("Provide an address or a latitude/longitude pair")
        return self


class SiteContext(StrictModel):
    speed_limit_mph: float | None = Field(default=None, gt=0, le=100, allow_inf_nan=False, strict=True)
    lane_count: int | None = Field(default=None, ge=1, le=20, strict=True)
    traffic_notes: str | None = Field(default=None, min_length=1, max_length=2000)
    work_period: Literal["day", "night", "mixed", "unknown"] = "unknown"
    pedestrians_present: bool | None = Field(default=None, strict=True)
    intersections_present: bool | None = Field(default=None, strict=True)
    excavation_planned: bool | None = Field(default=None, strict=True)


class IntakeRequest(StrictModel):
    work_type: Literal["line_striping", "underground_utility", "road_maintenance", "other"]
    work_description: str | None = Field(default=None, min_length=1, max_length=2000)
    location: JobLocation
    requested_outputs: list[Deliverable] = Field(min_length=1, max_length=7)
    requested_forms: list[Literal["jsa"]] = Field(default_factory=list, max_length=1)
    project_date: date | None = None
    site: SiteContext = Field(default_factory=SiteContext)

    @model_validator(mode="after")
    def validate_request(self):
        if len(self.requested_outputs) != len(set(self.requested_outputs)):
            raise ValueError("Requested outputs must not contain duplicates")
        if self.work_type == "other" and not self.work_description:
            raise ValueError("Describe other work types")
        return self


class AttentionItem(StrictModel):
    id: str
    category: Literal["missing_information", "context_review", "capability_gap"]
    message: str
    basis: Literal["wzos_intake_policy"] = "wzos_intake_policy"


class FormRecommendation(StrictModel):
    form_id: Literal["jsa"] = "jsa"
    title: str = "Job Safety Analysis"
    priority: Literal["strongly_recommended"] = "strongly_recommended"
    customer_requested: bool
    reason: str
    basis: Literal["wzos_product_policy"] = "wzos_product_policy"
    legally_required: None = None


class OutputAssessment(StrictModel):
    output: Deliverable
    status: Literal["not_implemented"] = "not_implemented"
    reason: str


class IntakeAssessment(StrictModel):
    schema_version: Literal["2.0"] = "2.0"
    assessment_kind: Literal["rule_based_intake"] = "rule_based_intake"
    location_status: Literal["unverified"] = "unverified"
    jurisdiction_note: str = "Virginia is the service default; location and governing authority still require verification."
    regulatory_requirements_status: Literal["not_evaluated"] = "not_evaluated"
    form_recommendations: list[FormRecommendation]
    attention_items: list[AttentionItem]
    requested_outputs: list[OutputAssessment]
    approved_for_field_use: Literal[False] = False
