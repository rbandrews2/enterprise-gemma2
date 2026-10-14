import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app, ACTORS
from services.workspace_preview.organization_hub import register
from services.workspace_preview.storage import SQLiteStorage
from services.v2.knowledge.store import Store


class OrganizationHubTests(unittest.TestCase):
    def make_storage(self, root):
        return SQLiteStorage(root / 'db')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        env = patch.dict(os.environ, {'WZOS_WORKSPACE_PREVIEW': '1'}); env.start(); self.addCleanup(env.stop)
        self.storage = self.make_storage(root)
        self.app = create_app(storage=self.storage, knowledge_store=Store(root / 'sources', {}))
        self.client = TestClient(self.app); self.addCleanup(self.client.close)

    def h(self, who='enterprise-admin'):
        return {'X-Preview-Actor': who}

    def credential(self, who='enterprise-admin', **changes):
        response = self.client.post('/api/admin/integrations', headers=self.h(who), json={'name': 'Synthetic connector', 'scopes': ['orders:read'], **changes})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_admin_boundary_and_edition(self):
        self.assertEqual(self.client.get('/api/admin/dashboard').status_code, 401)
        self.assertEqual(self.client.get('/api/admin/dashboard', headers=self.h('enterprise-general')).status_code, 403)
        data = self.client.get('/api/admin/dashboard', headers=self.h()).json()
        self.assertEqual(data['status'], 'amber')
        self.assertIn('report', [m['id'] for m in data['modules']])
        core = self.client.get('/api/admin/dashboard', headers=self.h('core-admin')).json()
        self.assertNotIn('report', [m['id'] for m in core['modules']])

    def test_notes_retry_isolation_and_delete(self):
        body = {'request_id': str(uuid4()), 'text': '<script>not executable</script>'}
        url = '/api/admin/dashboard/notes'
        self.assertEqual(self.client.post(url, headers=self.h(), json=body).status_code, 200)
        self.assertEqual(self.client.post(url, headers=self.h(), json=body).status_code, 200)
        self.assertEqual(self.client.post(url, headers=self.h(), json={**body, 'text': 'Changed'}).status_code, 409)
        self.assertEqual(self.client.post(url, headers=self.h('enterprise-general'), json=body).status_code, 403)
        self.assertEqual(self.client.get('/api/admin/dashboard', headers=self.h('core-admin')).json()['notes'], [])
        self.assertEqual(len(self.client.get('/api/admin/dashboard', headers=self.h()).json()['notes']), 1)
        self.client.delete(url + '/' + body['request_id'], headers=self.h('core-admin'))
        self.assertEqual(len(self.client.get('/api/admin/dashboard', headers=self.h()).json()['notes']), 1)
        self.client.delete(url + '/' + body['request_id'], headers=self.h())
        self.assertEqual(self.client.get('/api/admin/dashboard', headers=self.h()).json()['notes'], [])

    def test_preferences_concurrency_and_validation(self):
        url = '/api/admin/dashboard/preferences'
        body = {'expected_version': 0, 'hidden_modules': ['clock']}
        self.assertEqual(self.client.put(url, headers=self.h(), json=body).status_code, 200)
        self.assertEqual(self.client.put(url, headers=self.h(), json=body).status_code, 409)
        self.assertEqual(self.client.put(url, headers=self.h(), json={**body, 'hidden_modules': ['unknown']}).status_code, 422)
        data = self.client.get('/api/admin/dashboard', headers=self.h()).json()
        self.assertFalse(next(m['visible'] for m in data['modules'] if m['id'] == 'clock'))

    def test_status_requires_current_evidence(self):
        now = datetime.now(timezone.utc)
        with self.storage.connect() as db:
            for kind in ('account', 'service', 'security'):
                db.execute('INSERT INTO hub_status_checks VALUES (?,?,?,?,?,?,?)', ('enterprise-demo', kind, 'ok', 'Synthetic verified check', 'test-fixture', (now-timedelta(minutes=1)).isoformat(), (now+timedelta(minutes=5)).isoformat()))
        self.assertEqual(self.client.get('/api/admin/dashboard', headers=self.h()).json()['status'], 'green')
        with self.storage.connect() as db:
            db.execute("UPDATE hub_status_checks SET status='problem',explanation='Synthetic invoice overdue' WHERE kind='account'")
        self.assertEqual(self.client.get('/api/admin/dashboard', headers=self.h()).json()['status'], 'red')
        with self.storage.connect() as db:
            db.execute('UPDATE hub_status_checks SET expires_at=?', ((now-timedelta(minutes=2)).isoformat(),))
        self.assertEqual(self.client.get('/api/admin/dashboard', headers=self.h()).json()['status'], 'amber')

    def test_credential_secret_scopes_and_revoke(self):
        item = self.credential()
        listed = self.client.get('/api/admin/integrations', headers=self.h()).text
        self.assertNotIn(item['token'], listed); self.assertNotIn('token_hash', listed)
        headers = {'X-WZOS-API-Key': item['token']}
        self.assertEqual(self.client.get('/api/integrations/v1/orders', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/api/integrations/v1/schedule', headers=headers).status_code, 403)
        self.assertEqual(self.client.get('/api/orders', headers=headers).status_code, 401)
        self.assertEqual(self.client.delete('/api/admin/integrations/'+item['id'], headers=self.h('core-admin')).status_code, 404)
        self.client.delete('/api/admin/integrations/'+item['id'], headers=self.h())
        self.assertEqual(self.client.get('/api/integrations/v1/orders', headers=headers).status_code, 401)

    def test_export_projection_and_organization_isolation(self):
        with self.storage.connect() as db:
            db.execute('DELETE FROM preview_orders')
        body = {'request_id': str(uuid4()), 'title': 'Synthetic job', 'work_type': 'line_striping', 'address': 'Synthetic public road', 'locality': 'Norfolk', 'notes': 'Private notes excluded'}
        self.assertEqual(self.client.post('/api/orders', headers=self.h(), json=body).status_code, 201)
        own, other = self.credential(), self.credential('core-admin')
        url = '/api/integrations/v1/orders'
        result = self.client.get(url, headers={'X-WZOS-API-Key': own['token']}).json()
        self.assertEqual(len(result['items']), 1); self.assertNotIn('notes', result['items'][0])
        self.assertEqual(self.client.get(url, headers={'X-WZOS-API-Key': other['token']}).json()['items'], [])
        self.assertEqual(self.client.get(url+'?offset=1', headers={'X-WZOS-API-Key': own['token']}).json()['items'], [])
        self.assertEqual(self.client.get(url+'?limit=51', headers={'X-WZOS-API-Key': own['token']}).status_code, 422)

    def test_expiry_and_rate_limit(self):
        item = self.credential(); headers = {'X-WZOS-API-Key': item['token']}; url = '/api/integrations/v1/orders'
        with self.storage.connect() as db:
            db.execute('INSERT INTO integration_usage VALUES (?,?,?)', ('enterprise-demo', datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M'), 60))
        response = self.client.get(url, headers=headers)
        self.assertEqual(response.status_code, 429); self.assertEqual(response.headers['retry-after'], '60')
        with self.storage.connect() as db:
            db.execute("UPDATE integration_credentials SET expires_at='2000-01-01T00:00:00+00:00'")
        self.assertEqual(self.client.get(url, headers=headers).status_code, 401)

    def test_integration_observes_admin_and_organization_revocation(self):
        item = self.credential()
        with self.storage.connect() as db:
            db.execute('CREATE TABLE organizations (id TEXT PRIMARY KEY,active INTEGER NOT NULL)')
            db.execute('CREATE TABLE memberships (organization_id TEXT,user_id TEXT,role TEXT,active INTEGER)')
            db.execute('INSERT INTO organizations VALUES (?,1)', ('enterprise-demo',))
            db.execute("INSERT INTO memberships VALUES (?,?,'admin',1)", ('enterprise-demo', 'enterprise-admin'))
        guarded = FastAPI(); register(guarded, self.storage.connect, lambda request: ACTORS['enterprise-admin'], accounts=True)
        with TestClient(guarded) as client:
            # No export tables are read after authentication fails.
            with self.storage.connect() as db:
                db.execute("UPDATE memberships SET role='member'")
            self.assertEqual(client.get('/api/integrations/v1/orders', headers={'X-WZOS-API-Key': item['token']}).status_code, 401)
            with self.storage.connect() as db:
                db.execute("UPDATE memberships SET role='admin'"); db.execute('UPDATE organizations SET active=0')
            self.assertEqual(client.get('/api/integrations/v1/orders', headers={'X-WZOS-API-Key': item['token']}).status_code, 401)

    def test_request_boundaries_and_security_headers(self):
        response = self.client.post('/api/admin/dashboard/notes', headers=self.h(), content=iter([b'x'*9000, b'x'*9000]))
        self.assertEqual(response.status_code, 413)
        self.assertEqual(self.client.post('/api/admin/integrations', headers={**self.h(), 'Origin': 'https://untrusted.example'}, json={}).status_code, 403)
        self.assertEqual(self.client.get('/api/integrations/v1/orders?api_key=ignored').status_code, 401)
        self.assertEqual(self.client.get('/').headers['referrer-policy'], 'no-referrer')
        self.assertEqual(self.client.get('/').headers['x-frame-options'], 'DENY')


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'), 'Dedicated PostgreSQL database not configured')
class PostgreSQLOrganizationHubTests(OrganizationHubTests):
    def make_storage(self, root):
        from psycopg.conninfo import make_conninfo
        from services.workspace_preview.postgres import PostgreSQLStorage
        dsn = os.environ['WZOS_TEST_DATABASE_URL']; schema = 'test_'+uuid4().hex
        base = PostgreSQLStorage(dsn); self.addCleanup(base.close)
        with base.connect() as db:
            db.execute('CREATE SCHEMA '+schema)
        def cleanup():
            with base.connect() as db:
                db.execute('DROP SCHEMA '+schema+' CASCADE')
        self.addCleanup(cleanup)
        storage = PostgreSQLStorage(make_conninfo(dsn, options='-c search_path='+schema)); self.addCleanup(storage.close)
        storage.initialize(); return storage
