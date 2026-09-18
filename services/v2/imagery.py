"""Street View metadata boundary. No image downloads, persistence or placement."""
import json
from typing import Literal

import httpx
from pydantic import Field, ValidationError

from shared.contracts import StrictModel
from shared.intake import JobLocation


class PanoramaLocation(StrictModel):
    lat: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lng: float = Field(ge=-180, le=180, allow_inf_nan=False)


class ImageryAvailability(StrictModel):
    provider: Literal["google_street_view"] = "google_street_view"
    status: Literal["not_configured", "available", "empty", "unavailable"]
    reason: str
    panorama_id: str | None = None
    capture_date: str | None = None
    location: PanoramaLocation | None = None
    attribution: str | None = None
    approved_for_field_use: Literal[False] = False


class StreetViewMetadata:
    """Explicitly injected credentials only; default app never reads cloud secrets."""
    URL = "https://maps.googleapis.com/maps/api/streetview/metadata"

    def __init__(self, api_key: str | None = None, transport=None):
        self._api_key = api_key
        self._transport = transport

    def lookup(self, location: JobLocation) -> ImageryAvailability:
        if not self._api_key:
            return ImageryAvailability(status="not_configured", reason="google_access_disabled")
        query = (f"{location.latitude},{location.longitude}"
                 if location.latitude is not None else location.address)
        try:
            # Never follow redirects carrying a key. Never expose provider URLs/errors.
            with httpx.Client(transport=self._transport, timeout=10, follow_redirects=False,
                              trust_env=False) as client:
                with client.stream("GET", self.URL, params={"location": query, "key": self._api_key}) as response:
                    if response.status_code != 200:
                        return ImageryAvailability(status="unavailable", reason="provider_http_error")
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) > 65536:
                            return ImageryAvailability(status="unavailable", reason="provider_response_too_large")
            data = json.loads(body)
            if not isinstance(data, dict):
                raise ValueError("Invalid response")
            status = data.get("status")
            if status in {"ZERO_RESULTS", "NOT_FOUND"}:
                return ImageryAvailability(status="empty", reason="no_panorama_found")
            if status != "OK":
                return ImageryAvailability(status="unavailable", reason="provider_rejected_or_failed")
            panorama = data.get("pano_id")
            if not isinstance(panorama, str) or not panorama or len(panorama) > 512:
                raise ValueError("Missing panorama")
            capture_date = data.get("date")
            if capture_date is not None:
                import re
                if not isinstance(capture_date, str) or not re.fullmatch(r"[0-9]{4}(-(0[1-9]|1[0-2]))?", capture_date):
                    raise ValueError("Invalid capture date")
            return ImageryAvailability(
                status="available", reason="site_match_and_current_conditions_require_review",
                panorama_id=panorama, capture_date=capture_date,
                location=PanoramaLocation.model_validate(data["location"]),
                attribution=data.get("copyright"))
        except (httpx.HTTPError, ValueError, KeyError, TypeError, ValidationError):
            return ImageryAvailability(status="unavailable", reason="provider_response_failed")
