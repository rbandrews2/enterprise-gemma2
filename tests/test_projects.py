import asyncio
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from contextlib import closing

import httpx
from fastapi.testclient import TestClient

from services.v2.app import create_app
from services.v2.knowledge.store import Store
from services.v2.projects import ProjectStore, ProjectConflict
from services.v2.settings import Settings
from shared.projects import ProjectDraft


DRAFT = {'name':'Example job','intake':{'work_type':'line_striping','location':{'address':'Example address'},'requested_outputs':['work_zone_setup']}}
SPEED = {'id':'posted-1','kind':'speed','source_name':'Example field report','source_reference':'Photo reference only',
         'basis':'customer_report','road_segment':'Example segment','speed_type':'posted','value_mph':35}
TRAFFIC = {'id':'traffic-1','kind':'traffic','source_name':'Example count','source_reference':'Count record',
           'basis':'estimate','road_segment':'Example segment','metric':'aadt','value':1000,'units':'vehicles_per_day','direction':'both'}
IMAGE = {'id':'image-1','kind':'imagery','source_name':'Example owner','source_reference':'file:///do-not-fetch',
         'basis':'customer_report','road_segment':'Example segment','image_type':'generated_illustration',
         'attribution':'Example owner','usage_permission_note':'Unverified claim'}


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.store = ProjectStore(self.path/'projects.sqlite')
        self.knowledge = Store(self.path/'knowledge', {})
        self.app = create_app(Settings(), knowledge_store=self.knowledge, project_store=self.store)
        self.client = TestClient(self.app)

    def create(self, body=None, key='example-create-001'):
        return self.client.post('/v2/projects',json=body or DRAFT,headers={'Idempotency-Key':key})

    def test_create_retry_restart_and_key_conflict(self):
        first=self.create()
        self.assertEqual(first.status_code,201)
        record=first.json()
        self.assertEqual(self.create().json()['project_id'],record['project_id'])
        self.assertEqual(ProjectStore(self.store.path).get(record['project_id'])['draft'],record['draft'])
        self.assertEqual(self.create(DRAFT | {'name':'Different'}).status_code,409)
        self.assertEqual(self.client.get('/v2/projects').json()['total'],1)

    def test_append_only_history_and_stale_edits(self):
        record=self.create().json();pid=record['project_id']
        update=DRAFT | {'name':'Changed job','expected_version':1,'evidence':[SPEED]}
        response=self.client.put('/v2/projects/'+pid,json=update)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['version'],2)
        self.assertEqual(self.client.get('/v2/projects/'+pid+'?version=1').json()['draft']['name'],'Example job')
        self.assertEqual(self.client.put('/v2/projects/'+pid,json=update).status_code,409)
        self.assertEqual(self.client.get('/v2/projects/'+pid).json()['version'],2)
        self.assertEqual(self.create().json()['version'],1)

    def test_conflicting_concurrent_updates(self):
        pid=self.create().json()['project_id']
        def update(name):
            try:
                return self.store.update(pid,ProjectDraft.model_validate(DRAFT | {'name':name}),1)['version']
            except ProjectConflict:
                return 'conflict'
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(update,['First editor','Second editor']))
        self.assertEqual(sorted(map(str,results)),['2','conflict'])

    def test_evidence_remains_unverified_and_no_image_fetched(self):
        response=self.create(DRAFT | {'evidence':[SPEED,TRAFFIC,IMAGE]})
        self.assertEqual(response.status_code,201)
        review=response.json()['evidence_review']
        self.assertEqual(review['verification_status'],'not_verified')
        self.assertFalse(review['approved_for_field_use'])
        self.assertTrue(any('generated illustration' in issue for issue in review['issues']))
        self.assertTrue(any('Actual-site imagery reference is missing' in issue for issue in review['issues']))
        self.assertTrue(any('date is unknown' in issue for issue in review['issues']))

    def test_invalid_units_duration_and_duplicate_evidence(self):
        variants=[[TRAFFIC | {'units':'vehicles_per_hour'}],
                  [TRAFFIC | {'metric':'observed_count','units':'vehicles'}],
                  [TRAFFIC | {'duration_minutes':60}], [SPEED,SPEED],
                  [SPEED | {'verified':True}], [SPEED | {'value_mph':True}]]
        for evidence in variants:
            with self.subTest(evidence=evidence):
                self.assertEqual(self.create(DRAFT | {'evidence':evidence}).status_code,422)
        count=TRAFFIC | {'metric':'observed_count','units':'vehicles','duration_minutes':15}
        self.assertEqual(self.create(DRAFT | {'evidence':[count]}).status_code,201)

    def test_speed_mismatch_and_future_evidence(self):
        intake=DRAFT['intake'] | {'site':{'speed_limit_mph':45},'project_date':'2020-01-01'}
        response=self.create(DRAFT | {'intake':intake,'evidence':[SPEED | {'observed_on':'2099-01-01'}]})
        issues=response.json()['evidence_review']['issues']
        self.assertTrue(any('differs from' in issue for issue in issues))
        self.assertTrue(any('future' in issue for issue in issues))
        self.assertTrue(any('postdates' in issue for issue in issues))

    def test_source_notes_cannot_invent_revision_or_approval(self):
        note={'source_id':'unknown','revision':'a'*64,'section':'6A','question':'Does this apply?'}
        self.assertEqual(self.create(DRAFT | {'applicability_notes':[note]}).status_code,422)
        self.assertEqual(self.create(DRAFT | {'applicability_notes':[note | {'status':'approved'}]}).status_code,422)

    def test_preserved_revision_note_is_saved_as_pending(self):
        note={'source_id':'known-source','revision':'a'*64,'section':'6A','question':'Does this apply?'}
        self.knowledge.catalog['known-source']=object()
        with patch.object(self.knowledge,'revisions',return_value=[{'revision':'a'*64}]):
            result=self.create(DRAFT | {'applicability_notes':[note]})
        self.assertEqual(result.status_code,201)
        self.assertEqual(result.json()['draft']['applicability_notes'][0]['status'],'pending_review')
        self.assertFalse(result.json()['evidence_review']['approved_for_field_use'])

    def test_pagination_missing_and_input_errors(self):
        self.assertEqual(self.client.get('/v2/projects').json()['total'],0)
        self.assertEqual(self.client.get('/v2/projects/'+str(uuid4())).status_code,404)
        self.assertEqual(self.client.get('/v2/projects/not-a-uuid').status_code,422)
        self.assertEqual(self.client.post('/v2/projects',json=DRAFT).status_code,422)
        self.assertEqual(self.client.get('/v2/projects?limit=51').status_code,422)
        self.create();self.create(DRAFT | {'name':'Second'},key='example-create-002')
        page=self.client.get('/v2/projects?limit=1&offset=1').json()
        self.assertEqual(page['total'],2);self.assertEqual(len(page['results']),1)

    def test_saved_project_references_uses_saved_intake(self):
        pid=self.create().json()['project_id']
        result=self.client.get('/v2/projects/'+pid+'/references')
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['version'],1)
        self.assertEqual(result.json()['references']['library_status'],'unavailable')
        self.assertEqual(result.json()['references']['assessment']['form_recommendations'][0]['form_id'],'jsa')

    def test_corrupt_payload_fails_closed(self):
        pid=self.create().json()['project_id']
        with closing(sqlite3.connect(self.store.path)) as db, db:
            db.execute('UPDATE revisions SET payload=? WHERE project_id=?',('{}',pid))
        response=self.client.get('/v2/projects/'+pid)
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json()['error'],'local_storage_unavailable')

    def test_remote_client_cannot_create_project(self):
        async def run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app,client=('203.0.113.1',42)),base_url='http://localhost') as client:
                return await client.post('/v2/projects',json=DRAFT,headers={'Idempotency-Key':'remote-create-001'})
        self.assertEqual(asyncio.run(run()).status_code,403)
        self.assertFalse(self.store.path.exists())


if __name__ == '__main__':
    unittest.main()
