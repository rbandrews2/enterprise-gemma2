import unittest
import asyncio

import httpx
from fastapi.testclient import TestClient

from services.v2.app import create_app
from services.v2.imagery import StreetViewMetadata
from shared.intake import JobLocation


class ImageryTests(unittest.TestCase):
    def lookup(self, data, status=200):
        return StreetViewMetadata("test-secret", httpx.MockTransport(
            lambda request: httpx.Response(status, json=data))).lookup(JobLocation(address="Richmond, VA"))

    def test_success_preserves_partial_date_and_location(self):
        for capture in (None, "2024", "2024-02"):
            result = self.lookup(dict(status="OK", pano_id="panorama", date=capture,
                                      location={"lat": 37.54, "lng": -77.43}, copyright="Google"))
            self.assertEqual(result.status, "available")
            self.assertEqual(result.capture_date, capture)
            self.assertFalse(result.approved_for_field_use)

    def test_empty_and_provider_errors(self):
        for status in ("ZERO_RESULTS", "NOT_FOUND"):
            self.assertEqual(self.lookup({"status": status}).status, "empty")
        for status in ("REQUEST_DENIED", "OVER_QUERY_LIMIT", "UNKNOWN_ERROR", "INVALID_REQUEST"):
            result = self.lookup({"status": status, "error_message": "test-secret"})
            self.assertEqual(result.status, "unavailable")
            self.assertNotIn("test-secret", result.model_dump_json())

    def test_bad_payloads(self):
        for payload in ([], {}, {"status": "OK"}, {"status": "OK", "pano_id": "x",
                        "location": {"lat": 100, "lng": 0}}, {"status": "OK", "pano_id": "x",
                        "location": {"lat": 0, "lng": 0}, "date": "2024-13"}):
            self.assertEqual(self.lookup(payload).status, "unavailable")
        self.assertEqual(self.lookup({"data": "x" * 70000}).reason, "provider_response_too_large")

    def test_redirect_not_followed_and_coordinates_used(self):
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(302, headers={"location": "https://example.com"})
        result = StreetViewMetadata("secret", httpx.MockTransport(handler)).lookup(
            JobLocation(latitude=37.0, longitude=-77.0))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].url.params["location"], "37.0,-77.0")
        self.assertEqual(result.status, "unavailable")

    def test_timeout_is_sanitized(self):
        def handler(request):
            raise httpx.ReadTimeout("secret", request=request)
        result = StreetViewMetadata("secret", httpx.MockTransport(handler)).lookup(JobLocation(address="VA"))
        self.assertEqual(result.reason, "provider_response_failed")

    def test_default_api_and_access_boundary(self):
        with TestClient(create_app()) as client:
            path = "/v2/imagery/streetview/availability"
            self.assertEqual(client.post(path, json={"address": "Richmond"}).json()["status"], "not_configured")
            self.assertEqual(client.post(path, json={"latitude": 37.0}).status_code, 422)
        async def remote():
            transport = httpx.ASGITransport(app=create_app(), client=("203.0.113.1", 123))
            async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
                return await client.post(path, json={"address": "Richmond"})
        self.assertEqual(asyncio.run(remote()).status_code, 403)
