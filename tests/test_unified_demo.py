import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from scripts.build_unified_demo import build
from services.workspace_preview.app import create_app
from services.v2.knowledge.store import Store


class UnifiedDemoTests(unittest.TestCase):
    def test_saved_journeys_and_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
            'WZOS_WORKSPACE_PREVIEW': '1', 'WZOS_ACCOUNT_WORKSPACE': '',
            'K_SERVICE': '', 'GAE_ENV': '', 'NETLIFY': '', 'WZOS_ATLAS_LOCAL_MODEL': ''}):
            root = Path(tmp)/'demo'
            result = build(root)
            with self.assertRaises(FileExistsError):
                build(root)
            with TestClient(create_app(root/'orders.sqlite', Store(root/'sources', {}))) as client:
                for scenario in result['scenarios']:
                    headers = {'X-Preview-Actor': scenario['member']}
                    order = scenario['order_id']
                    self.assertEqual(client.get('/api/orders/'+order, headers=headers).status_code, 200)
                    forms = client.get('/api/modules/forms', headers=headers).json()['items']
                    self.assertIn(scenario['form_id'], [r['id'] for r in forms])
                    entries = client.get('/api/time/entries', headers=headers).json()['items']
                    self.assertEqual(entries[0]['work_seconds'], 3600)
                    self.assertEqual(entries[0]['status'], 'closed')
                    self.assertEqual(client.get('/api/time/entries?team=true', headers=headers).status_code, 403)
                    other = 'core-admin' if scenario['edition']=='enterprise' else 'enterprise-admin'
                    self.assertEqual(client.get('/api/orders/'+order, headers={'X-Preview-Actor': other}).status_code, 404)
                    if 'report_id' in scenario:
                        self.assertEqual(client.get('/api/orders/'+order+'/reports/'+scenario['report_id'], headers=headers).status_code, 200)

    def test_cloud_refusal_before_creating_files(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'K_SERVICE': 'cloud'}):
            path = Path(tmp)/'demo'
            with self.assertRaises(RuntimeError):
                build(path)
            self.assertFalse(path.exists())
