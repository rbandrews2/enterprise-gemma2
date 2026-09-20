import os
import unittest
from unittest.mock import patch
from pydantic import ValidationError
from fastapi.testclient import TestClient
from shared.job_geometry import JobGeometry
from shared.projects import ProjectDraft
from services.v2.app import create_app
from services.v2.projects import canonical
from services.v2.advice import context_hash


class GeometryTests(unittest.TestCase):
    def test_work_limits_and_bounds(self):
        for data in ({'duration_hours':0},{'lane_width_ft':-1},
                     {'work_limits':[{'latitude':37.,'longitude':-77.}]},
                     {'work_limits':[{'latitude':37.,'longitude':-77.}]*2,'geometry_source':'test'},
                     {'verification_status':'approved'}, {'available_sight_distance_ft':float('nan')}):
            with self.assertRaises(ValidationError):JobGeometry.model_validate(data)
        valid=JobGeometry.model_validate({'closure_type':'lane','geometry_source':'crew measurement',
             'work_limits':[{'latitude':37.,'longitude':-77.},{'latitude':37.01,'longitude':-77.}]})
        self.assertEqual(valid.verification_status,'customer_reported')

    def test_optional_geometry_compatibility(self):
        draft=ProjectDraft.model_validate({'name':'Test','intake':{'work_type':'line_striping','location':{'address':'Example'},'requested_outputs':['annotated_image']}})
        self.assertNotIn('job_geometry',canonical(draft))
        before=context_hash(draft)
        draft.job_geometry=JobGeometry(closure_type='lane')
        self.assertNotEqual(before,context_hash(draft))

    def test_browser_key_is_explicit_and_never_server_key(self):
        with patch.dict(os.environ,{'GOOGLE_MAPS_API_KEY':'server-secret','WZOS_GOOGLE_MAPS_BROWSER_KEY':''}):
            with TestClient(create_app()) as client:
                response=client.get('/v2/maps/config')
                self.assertEqual(response.json(),{'enabled':False,'browser_key':None})
                self.assertNotIn('server-secret',response.text)
                self.assertEqual(response.headers['cache-control'],'no-store')
                self.assertEqual(client.get('/v2/workspace-job.js').status_code,200)
        with patch.dict(os.environ,{'WZOS_GOOGLE_MAPS_BROWSER_KEY':'synthetic-browser-key'}):
            with TestClient(create_app()) as client:
                self.assertEqual(client.get('/v2/maps/config').json()['browser_key'],'synthetic-browser-key')
