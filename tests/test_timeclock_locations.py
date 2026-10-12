import os
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.workspace_preview.storage import SQLiteStorage
from services.v2.knowledge.store import Store


class TimeLocationTests(unittest.TestCase):
    def make_storage(self):
        return SQLiteStorage(Path(self.temp.name) / 'clock.sqlite')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'WZOS_WORKSPACE_PREVIEW':'1', 'K_SERVICE':'', 'GAE_ENV':'', 'NETLIFY':''})
        self.env.start()
        self.now = patch('services.workspace_preview.timeclock.utc_now', return_value='2026-10-11T18:00:00+00:00')
        self.now.start()
        self.storage = self.make_storage()
        self.client = TestClient(create_app(storage=self.storage, knowledge_store=Store(Path(self.temp.name)/'sources', {})))
        self.client.__enter__()
        self.member = {'X-Preview-Actor':'core-general'}

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.now.stop(); self.env.stop(); self.temp.cleanup()

    def event(self, **extra):
        return {'request_id':str(uuid4()), 'event':'clock_in', 'task':'setup',
                'captured_at':'2026-10-11T17:59:55Z', 'latitude':37.2, 'longitude':-79.3, 'accuracy':12, **extra}

    def save(self, item, headers=None):
        return self.client.post('/api/time/locations', json={'items':[item]}, headers=headers or self.member)

    def test_idempotency_and_command_link(self):
        command_id = str(uuid4())
        shift = self.client.post('/api/time/commands', headers=self.member,
                                 json={'request_id':command_id, 'action':'clock_in', 'task':'setup'}).json()['entry']
        item = self.event(command_id=command_id)
        self.assertEqual(self.save(item).status_code, 200)
        self.assertEqual(self.save(item).status_code, 200)
        self.assertEqual(self.save({**item, 'accuracy':99}).status_code, 409)
        rows = self.client.get('/api/time/locations', headers=self.member).json()['items']
        self.assertEqual(len(rows), 1); self.assertEqual(rows[0]['shift_id'], shift['id'])
        self.assertEqual(rows[0]['record_basis'], 'device_reported_unverified')

    def test_access_scope_and_write_targets(self):
        shift = self.client.post('/api/time/commands', headers=self.member,
                                 json={'request_id':str(uuid4()), 'action':'clock_in'}).json()['entry']
        self.assertEqual(self.save(self.event(shift_id=shift['id'])).status_code, 200)
        self.assertEqual(self.client.get('/api/time/locations').status_code, 401)
        self.assertEqual(self.client.get('/api/time/locations?team=true', headers=self.member).status_code, 403)
        self.assertEqual(self.client.get('/api/time/locations?employee_id=core-admin', headers=self.member).status_code, 403)
        self.assertEqual(len(self.client.get('/api/time/locations?team=true', headers={'X-Preview-Actor':'core-admin'}).json()['items']), 1)
        self.assertEqual(self.client.get('/api/time/locations?team=true', headers={'X-Preview-Actor':'enterprise-admin'}).json()['items'], [])
        self.assertEqual(self.save(self.event(shift_id=shift['id']), {'X-Preview-Actor':'enterprise-general'}).status_code, 404)
        self.assertEqual(self.save(self.event(employee_id='core-admin')).status_code, 422)

    def test_missing_fix_and_invalid_coordinates(self):
        item = self.event(latitude=None, longitude=None, accuracy=None, unavailable='offline')
        self.assertEqual(self.save(item).status_code, 200)
        for bad in [self.event(latitude=91), self.event(accuracy=-1), self.event(longitude=None),
                    self.event(unavailable='offline'), self.event(captured_at='2030-01-01T00:00:00Z')]:
            self.assertEqual(self.save(bad).status_code, 422, bad)


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'), 'PostgreSQL test database not configured')
class PostgreSQLTimeLocationTests(TimeLocationTests):
    def make_storage(self):
        from psycopg.conninfo import make_conninfo
        from services.workspace_preview.postgres import PostgreSQLStorage
        dsn, schema = os.environ['WZOS_TEST_DATABASE_URL'], 'test_' + uuid4().hex
        bootstrap = PostgreSQLStorage(dsn)
        self.addCleanup(bootstrap.close)
        with bootstrap.connect() as conn:
            conn.execute('CREATE SCHEMA ' + schema)
        def drop():
            with bootstrap.connect() as conn:
                conn.execute('DROP SCHEMA ' + schema + ' CASCADE')
        self.addCleanup(drop)
        storage = PostgreSQLStorage(make_conninfo(dsn, options='-c search_path=' + schema))
        self.addCleanup(storage.close)
        storage.initialize()
        return storage
