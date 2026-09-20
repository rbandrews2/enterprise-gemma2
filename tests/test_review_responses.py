import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from services.v2.app import create_app
from services.v2.knowledge.store import Store
from services.v2.projects import ProjectStore


class ResponseTests(unittest.TestCase):
    def test_save_reassess_stale_history_and_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            store=ProjectStore(Path(directory)/'projects.sqlite')
            with TestClient(create_app(project_store=store,knowledge_store=Store(Path(directory)/'knowledge',{}))) as client:
                draft={'name':'Test','intake':{'work_type':'line_striping','location':{'address':'Example'},'requested_outputs':['annotated_image']}}
                record=client.post('/v2/projects',json=draft,headers={'Idempotency-Key':'response-test'}).json()
                base='/v2/projects/'+record['project_id']
                packet=client.post(base+'/atlas/prepare?expected_version=1').json()
                finding=next(a for a in packet['project_advice'] if a['id']=='coordination')
                body={'finding_id':'coordination','context_sha256':finding['context_sha256'],
                      'disposition':'already_handled','note':'Crew schedule and contact list are recorded externally.','expected_version':1}
                saved=client.post(base+'/atlas/responses',json=body)
                self.assertEqual(saved.status_code,200)
                self.assertEqual(saved.json()['version'],2)
                self.assertEqual(client.post(base+'/atlas/responses',json=body).status_code,409)
                review=client.post(base+'/atlas/prepare?expected_version=2').json()
                self.assertEqual(review['response_summary']['reported_handled'],1)
                self.assertEqual(review['placements'],[])
                self.assertFalse(review['approved_for_field_use'])
                self.assertEqual(store.get(record['project_id'],1)['draft']['review_responses'],[])
                updated=saved.json()['draft']; updated['name']='Changed context'
                self.assertEqual(client.put(base,json=updated|{'expected_version':2}).status_code,200)
                review=client.post(base+'/atlas/prepare?expected_version=3').json()
                self.assertEqual(review['response_summary']['stale'],1)
                self.assertEqual(client.post(base+'/atlas/responses',json=body|{'expected_version':3}).status_code,409)
                current=next(a for a in review['project_advice'] if a['id']=='coordination')
                request=body|{'expected_version':3,'context_sha256':current['context_sha256']}
                self.assertEqual(client.post(base+'/atlas/responses',json=request|{'finding_id':'invented'}).status_code,422)
                self.assertEqual(client.post(base+'/atlas/responses',json=request|{'note':' '}).status_code,422)
                self.assertEqual(client.post(base+'/atlas/responses',json=request|{'disposition':'approved'}).status_code,422)
                self.assertEqual(client.post(base+'/atlas/responses',json=request|{'disposition':'needs_help'}).status_code,200)
                review=client.post(base+'/atlas/prepare?expected_version=4').json()
                self.assertEqual(review['response_summary']['needs_help'],1)
                self.assertEqual(len(ProjectStore(store.path).get(record['project_id'])['draft']['review_responses']),1)
