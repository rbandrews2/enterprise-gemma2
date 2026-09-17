"""Initial local draft contract. No compliance or approval claims."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DraftRequest(StrictModel):
    project_name: str = Field(min_length=1, max_length=200)
    address: str = Field(min_length=1, max_length=500)
    state: Literal["VA"]
    locality: str = Field(min_length=1, max_length=200)
    road_authority: str = Field(min_length=1, max_length=200)
    work_description: str = Field(min_length=1, max_length=2000)


class DraftResponse(StrictModel):
    schema_version: Literal["2.0"] = "2.0"
    status: Literal["local_preview"] = "local_preview"
    provider: Literal["deterministic_local"] = "deterministic_local"
    project_name: str
    summary: str
    missing_capabilities: list[str]
    approved_for_field_use: Literal[False] = False
