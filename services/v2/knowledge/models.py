"""Catalog metadata is curated; downloading never establishes applicability."""
import json
import re
from datetime import date
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from shared.contracts import StrictModel

Agency = Literal["VDOT", "FHWA", "OSHA", "VOSH", "NIOSH"]
Review = Literal["unreviewed", "extraction_checked", "applicability_reviewed"]
ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / "knowledge" / "sources.json"
DATA = ROOT / ".local-data" / "knowledge"
OFFICIAL_HOSTS = {
    "www.vdot.virginia.gov", "mutcd.fhwa.dot.gov", "www.osha.gov",
    "www.govinfo.gov", "www.cdc.gov", "doli.virginia.gov", "www.doli.virginia.gov", "law.lis.virginia.gov",
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
    kind: Literal["pdf", "html", "docx"]
    origin: Literal["official", "user_import"] = "official"
    pinned_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    document_role: Literal["standard", "specification", "correction", "guidance", "training", "unknown"] = "unknown"
    regions: list[str] = Field(default_factory=list, max_length=60)
    # Exact correction revisions required alongside this manual's context.
    required_companions: dict[str, str] = Field(default_factory=dict, max_length=8)
    archive_member: str | None = None
    archive_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    effective_from: date | None = None
    effective_to: date | None = None
    applicability_note: str
    publication_status: Literal["unknown", "current_at_verification", "superseded"] = "unknown"
    links_verified_on: date
    usage_note: str = "Official reference; redistribution and operational applicability require review."

    @model_validator(mode="after")
    def validate_source(self):
        if self.kind == "docx" and not self.archive_member:
            raise ValueError("DOCX requires a pinned archive member")
        if bool(self.archive_member) != bool(self.archive_sha256):
            raise ValueError("Archive member and hash are both required")
        if self.archive_member and (self.kind != "docx" or not self.archive_member.endswith(".docx")
                                    or any(x in self.archive_member for x in ("/", "\\", ":", ".."))):
            raise ValueError("Only approved top-level DOCX archive members are supported")
        if self.origin == "user_import":
            # Catalog-only, pinned operator imports. Never a downloader allowlist.
            if (self.kind != "pdf" or not self.pinned_sha256 or self.allowed_redirects
                    or not re.fullmatch(r"https://drive\.google\.com/file/d/[A-Za-z0-9_-]+/view", self.url)):
                raise ValueError("User imports require a pinned PDF and canonical Drive file URL")
        else:
            approved_url(self.url)
        for url in [self.publication_page, *self.allowed_redirects]:
            approved_url(url)
        if any(not re.fullmatch(r"[A-Z]{2}", region) for region in self.regions):
            raise ValueError("Regions must be two-letter state codes or US")
        if any(not re.fullmatch(r'[a-z][a-z0-9-]{1,79}', sid) or not re.fullmatch(r'[a-f0-9]{64}', sha)
               or sid == self.id for sid, sha in self.required_companions.items()):
            raise ValueError('Invalid pinned context companion')
        if self.effective_from and self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("Effective date range is reversed")
        return self


def load_catalog(path: Path = CATALOG) -> dict[str, Source]:
    entries = [Source.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]
    result = {entry.id: entry for entry in entries}
    if len(result) != len(entries):
        raise ValueError("Duplicate source IDs")
    return result
