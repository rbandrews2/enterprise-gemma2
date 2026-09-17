"""Catalog metadata is curated; downloading never establishes applicability."""
import json
from datetime import date
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from shared.contracts import StrictModel

Agency = Literal["VDOT", "FHWA", "OSHA", "VOSH"]
Review = Literal["unreviewed", "extraction_checked", "applicability_reviewed"]
ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / "knowledge" / "sources.json"
DATA = ROOT / ".local-data" / "knowledge"
OFFICIAL_HOSTS = {
    "www.vdot.virginia.gov", "mutcd.fhwa.dot.gov", "www.osha.gov",
    "doli.virginia.gov", "www.doli.virginia.gov", "law.lis.virginia.gov",
}


def approved_url(url: str) -> str:
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname not in OFFICIAL_HOSTS
            or parts.username or parts.password or parts.port not in (None, 443) or parts.fragment):
        raise ValueError("URL must be an approved official HTTPS address")
    return url


class Source(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]{1,79}$")
    agency: Agency
    title: str = Field(min_length=1, max_length=300)
    url: str
    allowed_redirects: list[str] = Field(default_factory=list)
    publication_page: str
    edition: str | None = None
    jurisdiction: str
    kind: Literal["pdf", "html"]
    effective_from: date | None = None
    effective_to: date | None = None
    applicability_note: str
    publication_status: Literal["unknown", "current_at_verification", "superseded"] = "unknown"
    links_verified_on: date
    usage_note: str = "Official reference; redistribution and operational applicability require review."

    @model_validator(mode="after")
    def validate_source(self):
        for url in [self.url, self.publication_page, *self.allowed_redirects]:
            approved_url(url)
        if self.effective_from and self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("Effective date range is reversed")
        return self


def load_catalog(path: Path = CATALOG) -> dict[str, Source]:
    entries = [Source.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]
    result = {entry.id: entry for entry in entries}
    if len(result) != len(entries):
        raise ValueError("Duplicate source IDs")
    return result
