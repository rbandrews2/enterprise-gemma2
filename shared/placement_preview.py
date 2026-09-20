"""Explicit scenario inputs for a reference-table preview, not plan approval."""
from typing import Literal
from pydantic import Field
from shared.contracts import StrictModel


class PlacementPreviewRequest(StrictModel):
    scenario: Literal['stationary_shoulder']
    road_class: Literal['conventional', 'undivided', 'divided_non_limited', 'limited_access']
    posted_speed_mph: float = Field(gt=0, le=100, allow_inf_nan=False, strict=True)
