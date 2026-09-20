"""Reported job geometry; bounds validate inputs, not engineering suitability."""
from typing import Literal
from pydantic import Field, model_validator
from shared.contracts import StrictModel


class RoadPoint(StrictModel):
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False, strict=True)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False, strict=True)


class JobGeometry(StrictModel):
    closure_type: Literal["shoulder", "lane", "full_road", "mobile", "sidewalk", "none", "unknown"] = "unknown"
    duration_hours: float | None = Field(default=None, gt=0, le=87600, allow_inf_nan=False, strict=True)
    lane_width_ft: float | None = Field(default=None, gt=0, le=100, allow_inf_nan=False, strict=True)
    available_sight_distance_ft: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False, strict=True)
    travel_direction: str | None = Field(default=None, min_length=1, max_length=200)
    work_limits: list[RoadPoint] = Field(default_factory=list, max_length=200)
    geometry_source: str | None = Field(default=None, min_length=1, max_length=1000)
    verification_status: Literal["customer_reported"] = "customer_reported"

    @model_validator(mode="after")
    def line_has_extent(self):
        if self.work_limits:
            if len(self.work_limits) < 2 or len({(p.latitude,p.longitude) for p in self.work_limits}) < 2:
                raise ValueError("Work limits require at least two distinct points")
            if not self.geometry_source:
                raise ValueError("Identify the source of the reported geometry")
        return self
