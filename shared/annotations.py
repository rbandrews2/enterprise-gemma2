"""User-proposed geographic markers, independent of any imagery provider."""
from typing import Literal
from pydantic import Field, model_validator
from shared.contracts import StrictModel


class GeographicAnnotation(StrictModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    kind: Literal["sign", "flagger", "work_area", "traffic_observation"]
    label: str = Field(min_length=1, max_length=200)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False, strict=True)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False, strict=True)
    evidence_ids: list[str] = Field(default_factory=list, max_length=100)
    rationale: str = Field(min_length=1, max_length=2000)
    status: Literal["proposed"] = "proposed"

    @model_validator(mode="after")
    def unique_references(self):
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("Annotation evidence references must be unique")
        return self
