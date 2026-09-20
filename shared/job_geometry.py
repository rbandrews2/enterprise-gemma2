"""Reported job geometry; bounds validate inputs, not engineering suitability."""
from typing import Literal
from datetime import date
from pydantic import Field, model_validator, model_serializer
from shared.contracts import StrictModel


class RoadPoint(StrictModel):
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False, strict=True)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False, strict=True)


class MeasuredApproach(StrictModel):
    id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,64}$')
    travel_direction: str = Field(min_length=1, max_length=200)
    measurement_source: str = Field(min_length=1, max_length=1000)
    measured_on: date
    path: list[RoadPoint] = Field(min_length=2, max_length=200)
    path_order: Literal['upstream_to_work_area'] = 'upstream_to_work_area'
    available_sight_distance_ft: float = Field(ge=0, le=100000, allow_inf_nan=False, strict=True)
    lane_width_ft: float = Field(gt=0, le=100, allow_inf_nan=False, strict=True)
    obstruction_notes: str = Field(min_length=1, max_length=2000)
    verification_status: Literal['customer_reported'] = 'customer_reported'

    @model_validator(mode='after')
    def validate_measurements(self):
        if not all(v.strip() for v in (self.travel_direction, self.measurement_source, self.obstruction_notes)):
            raise ValueError('Approach descriptions must not be blank')
        if self.measured_on > date.today():
            raise ValueError('Measurement date cannot be in the future')
        if any(a == b for a,b in zip(self.path, self.path[1:])):
            raise ValueError('Consecutive approach points must be distinct')
        return self


class JobGeometry(StrictModel):
    placement_scenario: Literal['stationary_shoulder'] | None = None
    road_class: Literal['conventional', 'undivided', 'divided_non_limited', 'limited_access'] | None = None
    approaches: list[MeasuredApproach] = Field(default_factory=list, max_length=8)
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
        if len({a.id for a in self.approaches}) != len(self.approaches):
            raise ValueError('Approach IDs must be unique')
        if self.placement_scenario == 'stationary_shoulder' and self.closure_type != 'shoulder':
            raise ValueError('Stationary shoulder scenario requires shoulder closure type')
        if self.work_limits:
            if len(self.work_limits) < 2 or len({(p.latitude,p.longitude) for p in self.work_limits}) < 2:
                raise ValueError("Work limits require at least two distinct points")
            if not self.geometry_source:
                raise ValueError("Identify the source of the reported geometry")
        return self

    @model_serializer(mode='wrap')
    def preserve_existing_hashes(self, handler):
        payload = handler(self)
        for key in ('placement_scenario', 'road_class', 'approaches'):
            if not payload.get(key):
                payload.pop(key, None)
        return payload
