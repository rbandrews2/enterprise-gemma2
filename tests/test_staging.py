import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.v2.knowledge.store import Store

class StagingTests(unittest.TestCase):
    def test_dedicated_service_guard(self):
        with patch.dict(os.environ,{'K_SERVICE':'other','WZOS_PRIVATE_STAGING':'1'}):
            with self.assertRaises(RuntimeError): create_app(private_staging=True)
    def test_fixed_fixture_identity_and_origin_boundary(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,{'K_SERVICE':'wzos-v2-staging','WZOS_PRIVATE_STAGING':'1'}):
            app=create_app(Path(directory)/'db.sqlite', Store(Path(directory)/'sources',{}),private_staging=True)
            with TestClient(app,base_url='https://stage.run.app') as client:
                self.assertEqual(client.get('/api/identities').json()['mode'],'restricted_staging')
                self.assertEqual(len(client.get('/api/identities').json()['identities']),1)
                session=client.get('/api/session',headers={'X-Preview-Actor':'core-admin'}).json()
                self.assertEqual(session['id'],'enterprise-admin')
                self.assertTrue(session['restricted_staging'])
                self.assertFalse(session['production_authenticated'])
                self.assertEqual(client.get('/api/session',headers={'Origin':'https://evil.example'}).status_code,403)
                self.assertEqual(client.get('/api/session',headers={'Origin':'https://stage.run.app'}).status_code,200)
                self.assertEqual(client.get('/api/orders/core-sample').status_code,404)
                navigation={'Sec-Fetch-Site':'cross-site','Sec-Fetch-Mode':'navigate'}
                self.assertEqual(client.get('/',headers=navigation).status_code,200)
                self.assertEqual(client.get('/api/session',headers=navigation).status_code,403)
                with patch.dict(os.environ,{'WZOS_STAGING_ORIGINS':'https://specific.cloudshell.dev'}):
                    self.assertEqual(client.get('/api/session',headers={'Origin':'https://specific.cloudshell.dev'}).status_code,200)
                    self.assertEqual(client.get('/api/session',headers={'Origin':'https://another.cloudshell.dev'}).status_code,403)
