import hashlib
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from datetime import date, timedelta
from pydantic import ValidationError
from fastapi.testclient import TestClient
from shared.job_geometry import JobGeometry
from shared.projects import ProjectDraft
from services.v2.projects import canonical, ProjectStore
from services.v2.advice import context_hash
from services.v2.app import create_app

APPROACH = {'id':'north','travel_direction':'southbound','measurement_source':'test field measurement',
    'measured_on':'2026-01-01','lane_width_ft':12,'available_sight_distance_ft':250,
    'obstruction_notes':'No obstacles reported; synthetic test',
    'path':[{'latitude':36.852,'longitude':-76.286},{'latitude':36.851,'longitude':-76.286}]}
DRAFT={'name':'Approach test','intake':{'work_type':'line_striping','location':{'address':'Example'},'requested_outputs':['annotated_image']}}


class ApproachTests(unittest.TestCase):
    def test_geometry_validation(self):
        JobGeometry(approaches=[APPROACH])
        for update in ({'path':[APPROACH['path'][0]]}, {'path':[APPROACH['path'][0]]*2},
                       {'measured_on':str(date.today()+timedelta(days=1))}, {'measurement_source':'  '},
                       {'lane_width_ft':0}, {'available_sight_distance_ft':-1}, {'verification_status':'approved'}):
            with self.subTest(update=update), self.assertRaises(ValidationError):
                JobGeometry(approaches=[APPROACH|update])
        with self.assertRaises(ValidationError): JobGeometry(approaches=[APPROACH,APPROACH])
        with self.assertRaises(ValidationError): JobGeometry(placement_scenario='stationary_shoulder',closure_type='lane')

    def test_old_geometry_hashes_unchanged(self):
        draft=ProjectDraft.model_validate(DRAFT|{'job_geometry':{'closure_type':'shoulder'}})
        payload=draft.model_dump(mode='json')
        self.assertNotIn('approaches',payload['job_geometry'])
        self.assertNotIn('placement_scenario',payload['job_geometry'])
        old=deepcopy(payload);old.pop('annotations');old.pop('review_responses')
        self.assertEqual(canonical(draft),json.dumps(old,sort_keys=True,separators=(',',':')))
        old_context=deepcopy(payload);old_context.pop('review_responses')
        self.assertEqual(context_hash(draft),hashlib.sha256(json.dumps(old_context,sort_keys=True,separators=(',',':')).encode()).hexdigest())

    def test_persistence_and_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            with TestClient(create_app(project_store=ProjectStore(Path(directory)/'test.sqlite'))) as client:
                record=client.post('/v2/projects',json=DRAFT,headers={'Idempotency-Key':'approach-test'}).json()
                path='/v2/projects/'+record['project_id']
                update=DRAFT|{'expected_version':1,'job_geometry':{'closure_type':'shoulder','placement_scenario':'stationary_shoulder','road_class':'conventional','approaches':[APPROACH]}}
                saved=client.put(path,json=update)
                self.assertEqual(saved.status_code,200)
                self.assertEqual(saved.json()['draft']['job_geometry']['approaches'][0]['path'],APPROACH['path'])
                self.assertEqual(client.put(path,json=update).status_code,409)
                self.assertNotEqual(context_hash(ProjectDraft.model_validate(DRAFT)),context_hash(ProjectDraft.model_validate(saved.json()['draft'])))
                self.assertIsNone(client.get(path+'?version=1').json()['draft']['job_geometry'])
