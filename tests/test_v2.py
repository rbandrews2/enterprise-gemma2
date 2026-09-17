import unittest

from fastapi.testclient import TestClient

from services.v2.app import create_app
from services.v2.settings import Settings


VALID = {
    "project_name": "Example job",
    "address": "Example address",
    "state": "VA",
    "locality": "Example locality",
    "road_authority": "Pending verification",
    "work_description": "Example maintenance",
}


class V2Tests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(Settings()))

    def test_preview_does_not_claim_compliance(self):
        response = self.client.post("/v2/drafts/preview", json=VALID)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["approved_for_field_use"])
        self.assertTrue(response.json()["missing_capabilities"])

    def test_inputs_fail_closed(self):
        for change in ({"state": "NC"}, {"locality": " "}, {"work_description": "x" * 2001}, {"approved": True}):
            with self.subTest(change=change):
                self.assertEqual(self.client.post("/v2/drafts/preview", json=VALID | change).status_code, 422)

    def test_readiness_is_honest(self):
        self.assertEqual(self.client.get("/health/live").status_code, 200)
        self.assertFalse(self.client.get("/health/ready").json()["production_ready"])

    def test_cloud_configuration_rejected(self):
        for kwargs in ({"environment": "production"}, {"backend": "vertex"}):
            with self.assertRaises(ValueError):
                Settings(**kwargs)

    def test_provider_errors_are_redacted(self):
        class BrokenProvider:
            async def preview(self, request):
                raise RuntimeError("sensitive-provider-content")

        response = TestClient(create_app(Settings(), BrokenProvider())).post("/v2/drafts/preview", json=VALID)
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("sensitive-provider-content", response.text)
        self.assertTrue(response.json()["correlation_id"])

    def test_invalid_provider_response_rejected(self):
        class InvalidProvider:
            async def preview(self, request):
                return {"approved_for_field_use": True}

        response = TestClient(create_app(Settings(), InvalidProvider())).post("/v2/drafts/preview", json=VALID)
        self.assertEqual(response.status_code, 502)


if __name__ == "__main__":
    unittest.main()
