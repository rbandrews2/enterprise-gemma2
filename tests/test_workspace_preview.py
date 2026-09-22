import os
import asyncio
import httpx
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app, ACTORS
from services.v2.knowledge.store import Store


class WorkspacePreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "preview.sqlite"
        self.env = patch.dict(os.environ, {"WZOS_WORKSPACE_PREVIEW": "1", "K_SERVICE": "", "GAE_ENV": "", "NETLIFY": ""})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = TestClient(create_app(self.db, Store(Path(self.temp.name) / "sources", {})))
        self.addCleanup(self.client.close)

    def headers(self, actor="enterprise-admin"):
        return {"X-Preview-Actor": actor}

    def payload(self, **changes):
        return {"request_id": str(uuid4()), "title": "Synthetic utility job", "work_type": "underground_utility",
                "address": "Example road segment, Norfolk, VA", "locality": "Norfolk", "notes": "Synthetic", **changes}

    def create(self, actor="enterprise-admin", body=None):
        response = self.client.post("/api/orders", headers=self.headers(actor), json=body or self.payload())
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_explicit_opt_in_and_cloud_refusal(self):
        with patch.dict(os.environ, {"WZOS_WORKSPACE_PREVIEW": "0"}), self.assertRaises(RuntimeError):
            create_app(self.db)
        with patch.dict(os.environ, {"K_SERVICE": "cloud"}), self.assertRaises(RuntimeError):
            create_app(self.db)

    def test_boundary_and_identity(self):
        self.assertEqual(self.client.get("/api/orders").status_code, 401)
        self.assertEqual(self.client.get("/api/orders", headers=self.headers("unknown")).status_code, 401)
        self.assertEqual(self.client.get("/", headers={"Host": "evil.example"}).status_code, 403)
        for origin in ("https://evil.example", "null"):
            self.assertEqual(self.client.post("/api/orders", headers={**self.headers(), "Origin": origin}, json=self.payload()).status_code, 403)
        self.assertEqual(self.client.get("/", headers={"Sec-Fetch-Site": "cross-site"}).status_code, 403)
        async def remote_check():
            transport = httpx.ASGITransport(app=create_app(self.db), client=("203.0.113.9", 8083))
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as remote:
                self.assertEqual((await remote.get("/")).status_code, 403)
        asyncio.run(remote_check())

    def test_four_combinations_and_tenant_isolation(self):
        for actor_id, actor in ACTORS.items():
            with self.subTest(actor=actor_id):
                session = self.client.get("/api/session", headers=self.headers(actor_id)).json()
                self.assertFalse(session["production_authenticated"])
                self.assertEqual(session["can_prepare_atlas"], actor["edition"] == "enterprise")
                self.assertEqual(session["can_manage_team"], actor["role"] == "admin")
                record = self.create(actor_id)
                self.assertEqual(record["owner_id"], actor_id)
                other = "core-admin" if actor["edition"] == "enterprise" else "enterprise-admin"
                path = "/api/orders/" + record["id"]
                self.assertEqual(self.client.get(path, headers=self.headers(other)).status_code, 404)
                update = self.payload(title="Cross-organization edit attempt")
                update.pop("request_id")
                self.assertEqual(self.client.put(path, headers=self.headers(other), json={**update, "expected_version": 1}).status_code, 404)
                other_ids = [r["id"] for r in self.client.get("/api/orders", headers=self.headers(other)).json()["items"]]
                self.assertNotIn(record["id"], other_ids)
                if actor["role"] == "admin":
                    crew = actor["edition"] + "-general"
                    self.assertEqual(self.client.get(path, headers=self.headers(crew)).status_code, 404)
                    self.assertEqual(self.client.put(path, headers=self.headers(crew), json={**update, "expected_version": 1}).status_code, 404)

    def test_idempotent_create_and_conflicting_retry(self):
        body = self.payload()
        one = self.create(body=body)
        two = self.create(body=body)
        self.assertEqual(one["id"], two["id"])
        self.assertEqual(self.client.post("/api/orders", headers=self.headers(), json={**body, "title": "Different"}).status_code, 409)

    def test_edit_persists_and_stale_update_cannot_overwrite(self):
        row = self.create("enterprise-general")
        body = self.payload(title="Updated scope")
        body.pop("request_id")
        body["expected_version"] = 1
        path = "/api/orders/" + row["id"]
        result = self.client.put(path, headers=self.headers(), json=body)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["version"], 2)
        self.assertEqual(self.client.put(path, headers=self.headers("enterprise-general"), json=body).status_code, 409)
        with TestClient(create_app(self.db)) as reloaded:
            self.assertEqual(reloaded.get(path, headers=self.headers("enterprise-general")).json()["title"], "Updated scope")

    def test_client_cannot_spoof_owner_org_or_role(self):
        for name in ("owner_id", "organization_id", "role", "edition"):
            response = self.client.post("/api/orders", headers=self.headers("core-general"), json=self.payload(**{name: "enterprise-admin"}))
            self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.post("/api/orders", headers=self.headers(), json=self.payload(title="   ")).status_code, 422)

    def test_preparation_entitlement_version_and_truthful_output(self):
        core = self.create("core-admin")
        path = f"/api/orders/{core['id']}/preparation?expected_version=1"
        self.assertEqual(self.client.post(path, headers=self.headers("core-admin")).status_code, 403)
        row = self.create("enterprise-general")
        path = f"/api/orders/{row['id']}/preparation"
        self.assertEqual(self.client.post(path + "?expected_version=2", headers=self.headers()).status_code, 409)
        response = self.client.post(path + "?expected_version=1", headers=self.headers())
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["model_called"])
        self.assertFalse(data["approved_for_field_use"])
        self.assertEqual(data["placements"], [])
        self.assertTrue(data["attention_items"])
        self.assertEqual(data["order_id"], row["id"])

    def test_atlas_adapter_uses_saved_context_and_preserves_geometry(self):
        body = self.payload(road_authority="Reported city road", site={"speed_limit_mph": 35.0,
                            "lane_count": 2, "work_period": "night"},
                            job_geometry={"closure_type": "shoulder", "lane_width_ft": 12.0})
        order = self.create(body=body)
        path = f"/api/orders/{order['id']}"
        result = self.client.post(path + "/preparation?expected_version=1", headers=self.headers()).json()
        self.assertEqual(result["mode"], "source_grounded_preparation")
        self.assertEqual(result["references"]["library_status"], "unavailable")
        self.assertEqual(result["project_id"], order["id"])
        self.assertEqual(len(result["project_sha256"]), 64)
        questions = {q["id"] for q in result["questions"]}
        self.assertNotIn("speed_limit", questions)
        self.assertNotIn("road_authority", questions)
        self.assertNotIn("lane_width_ft", questions)
        self.assertIn("verify_geometry", questions)
        self.assertEqual(result["placements"], [])
        self.assertEqual(result["evidence_review"]["verification_status"], "not_verified")
        self.assertEqual(self.client.get(path, headers=self.headers()).json()["job_geometry"], order["job_geometry"])
        self.assertEqual(self.client.get(path, headers=self.headers()).json()["version"], 1)
        body.pop("request_id")
        body["site"]["speed_limit_mph"] = 45.0
        changed = self.client.put(path, headers=self.headers(), json={**body, "expected_version": 1})
        self.assertEqual(changed.status_code, 200)
        new = self.client.post(path + "/preparation?expected_version=2", headers=self.headers()).json()
        self.assertNotEqual(new["project_sha256"], result["project_sha256"])
        body["job_geometry"] = {"work_limits": [{"latitude": 36.8, "longitude": -76.2}]}
        self.assertEqual(self.client.put(path, headers=self.headers(), json={**body, "expected_version": 2}).status_code, 422)

    def test_measured_approach_saved_and_invalid_geometry_rejected(self):
        approach = {"id": "north", "travel_direction": "southbound", "measurement_source": "Synthetic fixture",
                    "measured_on": "2026-09-01", "lane_width_ft": 12.0, "available_sight_distance_ft": 400.0,
                    "obstruction_notes": "Synthetic only", "path": [{"latitude": 36.86, "longitude": -76.28},
                    {"latitude": 36.85, "longitude": -76.28}]}
        body = self.payload(job_geometry={"closure_type": "shoulder", "placement_scenario": "stationary_shoulder",
                                         "approaches": [approach]})
        order = self.create(body=body)
        self.assertEqual(order["job_geometry"]["approaches"][0]["path"], approach["path"])
        body["request_id"] = str(uuid4())
        body["job_geometry"]["approaches"].append(approach)
        self.assertEqual(self.client.post("/api/orders", headers=self.headers(), json=body).status_code, 422)

    def checklist_payload(self, version=0, order_version=1):
        from services.workspace_preview.app import CHECKLIST_ITEMS
        return {"expected_version": version, "expected_order_version": order_version,
                "items": {key: {"status": "not_reviewed", "notes": ""} for key in CHECKLIST_ITEMS}}

    def test_checklist_history_staleness_conflicts_and_restart(self):
        order = self.create("enterprise-general")
        path = f"/api/orders/{order['id']}/checklist"
        self.assertIsNone(self.client.get(path, headers=self.headers()).json()["checklist"])
        body = self.checklist_payload()
        saved = self.client.put(path, headers=self.headers(), json=body)
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertFalse(saved.json()["approved_for_field_use"])
        self.assertEqual(self.client.put(path, headers=self.headers(), json=body).status_code, 409)
        update = self.payload(title="Changed limits")
        update.pop("request_id")
        self.client.put(f"/api/orders/{order['id']}", headers=self.headers(), json={**update, "expected_version": 1})
        self.assertTrue(self.client.get(path, headers=self.headers()).json()["checklist"]["stale"])
        self.assertEqual(self.client.put(path, headers=self.headers(), json=self.checklist_payload(1, 1)).status_code, 409)
        body = self.checklist_payload(1, 2)
        body["items"]["site"] = {"status": "needs_attention", "notes": "Measure changed limits"}
        response = self.client.put(path, headers=self.headers("enterprise-general"), json=body)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["checklist"]["stale"])
        with TestClient(create_app(self.db)) as client:
            latest = client.get(path, headers=self.headers()).json()
            self.assertEqual(latest["latest_version"], 2)
            self.assertEqual(latest["checklist"]["author_id"], "enterprise-general")
            old = client.get(path + "?version=1", headers=self.headers()).json()["checklist"]
            self.assertTrue(old["stale"])
            self.assertEqual(old["items"]["site"]["status"], "not_reviewed")
            self.assertEqual(client.get(path + "?version=3", headers=self.headers()).status_code, 404)

    def test_checklist_access_validation_and_core_support(self):
        for actor_id in ACTORS:
            order = self.create(actor_id)
            path = f"/api/orders/{order['id']}/checklist"
            self.assertEqual(self.client.put(path, headers=self.headers(actor_id), json=self.checklist_payload()).status_code, 200)
            forbidden = "enterprise-admin" if actor_id.startswith("core") else "core-admin"
            for suffix in ("", "?version=1"):
                self.assertEqual(self.client.get(path + suffix, headers=self.headers(forbidden)).status_code, 404)
            self.assertEqual(self.client.put(path, headers=self.headers(forbidden), json=self.checklist_payload()).status_code, 404)
            if actor_id.endswith("admin"):
                general = actor_id.replace("admin", "general")
                self.assertEqual(self.client.get(path, headers=self.headers(general)).status_code, 404)
                self.assertEqual(self.client.put(path, headers=self.headers(general), json=self.checklist_payload()).status_code, 404)
        path = f"/api/orders/{self.create()['id']}/checklist"
        for change in ("missing", "extra", "approval", "reason", "spoof"):
            body = self.checklist_payload()
            if change == "missing": body["items"].pop("site")
            if change == "extra": body["items"]["unknown"] = {"status": "not_reviewed"}
            if change == "approval": body["items"]["site"]["status"] = "approved"
            if change == "reason": body["items"]["site"]["status"] = "not_applicable"
            if change == "spoof": body["author_id"] = "someone-else"
            self.assertEqual(self.client.put(path, headers=self.headers(), json=body).status_code, 422, change)
        self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.get(path + "?version=0", headers=self.headers()).status_code, 422)

    def test_assets_and_missing_routes(self):
        for path in ("/", "/workspace.js", "/workspace.css", "/assistant.js", "/geometry.js", "/atlas-assistant.png"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
        self.assertEqual(self.client.get("/secrets.env").status_code, 404)


if __name__ == "__main__":
    unittest.main()
