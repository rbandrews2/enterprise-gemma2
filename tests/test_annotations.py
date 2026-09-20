import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from pydantic import ValidationError
from services.v2.app import create_app
from services.v2.projects import ProjectStore, canonical
from shared.projects import ProjectDraft

DRAFT = {"name": "Annotation test", "intake": {"work_type": "line_striping",
    "location": {"address": "Example address"}, "requested_outputs": ["annotated_image"]}}
MARKER = {"id": "sign-1", "kind": "sign", "label": "Proposed warning sign",
    "latitude": 37.54, "longitude": -77.43, "rationale": "Operator proposal pending review"}


class AnnotationTests(unittest.TestCase):
    def test_history_coordinates_and_restart(self):
        with TemporaryDirectory() as folder:
            store = ProjectStore(Path(folder) / "projects.sqlite")
            with TestClient(create_app(project_store=store)) as client:
                first = client.post("/v2/projects", json=DRAFT | {"annotations": [MARKER]},
                                    headers={"Idempotency-Key": "annotation-test"}).json()
                path = f'/v2/projects/{first["project_id"]}'
                geo = client.get(path + "/annotations").json()
                self.assertEqual(geo["features"][0]["geometry"]["coordinates"], [-77.43, 37.54])
                self.assertFalse(geo["approved_for_field_use"])
                changed = client.put(path, json=DRAFT | {"annotations": [], "expected_version": 1})
                self.assertEqual(changed.status_code, 200)
                self.assertEqual(client.get(path + "/annotations").json()["features"], [])
                self.assertEqual(len(client.get(path + "/annotations?version=1").json()["features"]), 1)
                self.assertEqual(client.get(path + "/annotations?version=0").status_code, 422)
            saved = ProjectStore(store.path).get(first["project_id"], 1)
            self.assertEqual(saved["draft"]["annotations"][0]["id"], "sign-1")

    def test_validation_and_no_approval(self):
        for changes in ({"latitude": 91}, {"longitude": -181}, {"latitude": float("nan")},
                        {"status": "approved"}, {"evidence_ids": ["missing"]},
                        {"kind": "traffic_observation"}, {"evidence_ids": ["x", "x"]}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                ProjectDraft.model_validate(DRAFT | {"annotations": [MARKER | changes]})
        with self.assertRaises(ValidationError):
            ProjectDraft.model_validate(DRAFT | {"annotations": [MARKER, MARKER]})

    def test_traffic_reference_and_removal(self):
        traffic = {"id": "count", "kind": "traffic", "source_name": "Crew",
                   "source_reference": "Count sheet", "basis": "customer_report", "road_segment": "A",
                   "metric": "observed_count", "value": 50, "units": "vehicles",
                   "duration_minutes": 10, "direction": "north"}
        body = DRAFT | {"evidence": [traffic], "annotations": [MARKER | {
            "kind": "traffic_observation", "evidence_ids": ["count"]}]}
        self.assertEqual(ProjectDraft.model_validate(body).annotations[0].status, "proposed")
        with self.assertRaises(ValidationError):
            ProjectDraft.model_validate(body | {"evidence": []})

    def test_legacy_create_hash_unchanged(self):
        draft = ProjectDraft.model_validate(DRAFT)
        legacy = draft.model_dump(mode="json", exclude={"annotations", "review_responses"})
        encoded = json.dumps(legacy, sort_keys=True, separators=(",", ":"))
        self.assertEqual(canonical(draft), encoded)
        self.assertEqual(ProjectDraft.model_validate_json(encoded).annotations, [])
