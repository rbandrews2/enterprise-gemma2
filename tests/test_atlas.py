import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from services.v2.app import create_app
from services.v2.knowledge.store import Store
from services.v2.projects import ProjectStore


class AtlasTests(unittest.TestCase):
    def test_preparation_missing_library_no_invented_placements(self):
        with tempfile.TemporaryDirectory() as directory:
            store=ProjectStore(Path(directory)/'projects.sqlite')
            with TestClient(create_app(project_store=store, knowledge_store=Store(Path(directory)/'sources',{}))) as client:
                draft={'name':'Norfolk example','intake':{'work_type':'line_striping','location':{'address':'Example address','locality':'Norfolk'},'requested_outputs':['annotated_image']}}
                record=client.post('/v2/projects',json=draft,headers={'Idempotency-Key':'atlas-test'}).json()
                path=f'/v2/projects/{record["project_id"]}/atlas/prepare'
                response=client.post(path+'?expected_version=1')
                self.assertEqual(response.status_code,200)
                result=response.json()
                self.assertEqual(result['project_sha256'],record['sha256'])
                self.assertEqual(result['placements'],[])
                self.assertIn('operations', {a['category'] for a in result['project_advice']})
                self.assertTrue(all(a['next_action'] for a in result['project_advice']))
                self.assertFalse(result['model_called'])
                self.assertFalse(result['approved_for_field_use'])
                self.assertEqual(result['form_recommendations'][0]['form_id'],'jsa')
                self.assertIn('road_authority',[q['id'] for q in result['questions']])
                self.assertEqual(result['references']['library_status'],'unavailable')
                self.assertEqual(client.post(path).status_code,422)
                self.assertEqual(client.post(path+'?expected_version=2').status_code,409)
                self.assertEqual(store.get(record['project_id'])['version'],1)

    def test_supplied_context_still_cannot_approve(self):
        from services.v2.atlas import prepare
        from shared.projects import ProjectDraft
        with tempfile.TemporaryDirectory() as directory:
            store=ProjectStore(Path(directory)/'projects.sqlite')
            draft=ProjectDraft.model_validate({'name':'Complete claims','intake':{'work_type':'line_striping','location':{'address':'Example','locality':'Norfolk','road_authority':'Claimed authority'},'project_date':'2026-10-01','site':{'speed_limit_mph':35,'lane_count':2,'pedestrians_present':False,'intersections_present':False,'work_period':'day'},'requested_outputs':['annotated_image']}})
            result=prepare(store.create(draft,'test-key'),Store(Path(directory)/'sources',{}))
            self.assertEqual(result['status'],'needs_verified_rules')
            self.assertEqual(len(result['questions']),3)
            self.assertEqual(result['placements'],[])
