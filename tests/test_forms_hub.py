import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from services.v2.knowledge.store import Store
from services.workspace_preview import forms_hub
from services.workspace_preview.app import create_app
from services.workspace_preview.files import LocalFiles

MEMBER, ADMIN = {'X-Preview-Actor': 'enterprise-general'}, {'X-Preview-Actor': 'enterprise-admin'}
OTHER_ADMIN, OTHER_MEMBER = {'X-Preview-Actor': 'core-admin'}, {'X-Preview-Actor': 'core-general'}
PDF = b'%PDF-1.7\n% synthetic C-85 placeholder for tests\n'


class FormsHubTests(unittest.TestCase):
    storage = None

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'WZOS_WORKSPACE_PREVIEW': '1', 'K_SERVICE': '', 'GAE_ENV': '', 'NETLIFY': ''})
        self.env.start()
        self.db = Path(self.temp.name) / 'db.sqlite'
        self.client = self.make_client()

    def make_client(self, files=True):
        store = LocalFiles(Path(self.temp.name) / 'files') if files else None
        client = TestClient(create_app(self.db, Store(Path(self.temp.name) / 'sources', {}), storage=self.storage, file_store=store))
        client.__enter__()
        return client

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.env.stop()
        self.temp.cleanup()

    def item(self, item_id, headers=ADMIN, version=0, client=None, **extra):
        body = {'expected_version': version, 'title': 'VDOT Form C-85', 'category': 'official_agency_form',
                'description': 'Pavement marking daily log', 'file_id': None, **extra}
        return (client or self.client).put(f'/api/forms/library/{item_id}', headers=headers, json=body)

    def upload(self, item_id, headers=ADMIN, data=PDF, file_id=None, content_type='application/pdf', filename='C-85.pdf'):
        file_id = file_id or str(uuid4())
        return self.client.put(f'/api/files/{file_id}?entity_kind=form_library&entity_id={item_id}&filename={filename}',
                               headers={**headers, 'Content-Type': content_type}, content=data)

    def published(self, title='VDOT Form C-85'):
        item_id = str(uuid4())
        self.assertEqual(self.item(item_id, title=title).status_code, 200)
        stored = self.upload(item_id).json()
        response = self.item(item_id, version=1, title=title, file_id=stored['id'])
        self.assertEqual(response.status_code, 200, response.text)
        return item_id, response.json()

    def library(self, headers=MEMBER, client=None):
        return (client or self.client).get('/api/forms/library', headers=headers).json()

    def test_builtin_printables_are_catalogued_and_never_stored(self):
        self.assertEqual(self.client.get('/api/forms/templates').status_code, 401)
        catalog = self.client.get('/api/forms/templates', headers=MEMBER).json()
        self.assertFalse(catalog['saved_on_server'])
        self.assertEqual({t['id'] for t in catalog['items']}, {'jsa', 'incident', 'dvir'})
        self.assertEqual({t['category'] for t in catalog['items']}, {'wzos_printable'})
        detail = self.client.get('/api/forms/templates/jsa/1', headers=MEMBER).json()
        definition = {k: v for k, v in detail.items() if k not in ('checksum', 'latest_revision')}
        self.assertEqual(detail['checksum'], forms_hub.checksum(definition))
        self.assertFalse(any('required' in f for s in detail['sections'] for f in s['fields']))
        self.assertEqual(self.client.get('/api/forms/templates/c85_prep/1', headers=MEMBER).status_code, 404)
        # There is no endpoint that accepts filled-in form content.
        self.assertIn(self.client.put(f'/api/forms/{uuid4()}', headers=MEMBER, json={'fields': {}}).status_code, (404, 405))

    def test_admin_publishes_and_every_member_downloads(self):
        item_id, item = self.published()
        self.assertEqual((item['category_label'], item['file']['filename'], item['verified_by_wzos']), ('Official agency form', 'C-85.pdf', False))
        listing = self.library(MEMBER)
        self.assertEqual(([i['title'] for i in listing['items']], listing['can_manage'], listing['uploads_enabled']), (['VDOT Form C-85'], False, False))
        download = self.client.get(f"/api/files/{item['file']['id']}", headers=MEMBER)
        self.assertEqual((download.status_code, download.content), (200, PDF))
        self.assertIn('attachment', download.headers['content-disposition'])
        self.assertTrue(self.library(ADMIN)['uploads_enabled'])
        restarted = self.make_client()
        try:
            self.assertEqual(restarted.get(f"/api/files/{item['file']['id']}", headers=MEMBER).content, PDF)
        finally:
            restarted.__exit__(None, None, None)

    def test_only_admins_manage_team_forms(self):
        item_id, item = self.published()
        self.assertEqual(self.item(str(uuid4()), MEMBER).status_code, 403)
        self.assertEqual(self.item(item_id, MEMBER, version=2, file_id=item['file']['id']).status_code, 403)
        self.assertEqual(self.upload(item_id, MEMBER).status_code, 403)
        self.assertEqual(self.client.post(f'/api/forms/library/{item_id}/remove', headers=MEMBER, json={'expected_version': 2}).status_code, 403)
        draft = str(uuid4())
        self.item(draft, title='Company toolbox talk', category='company_form')
        self.assertEqual([i['title'] for i in self.library(MEMBER)['items']], ['VDOT Form C-85'])  # file-less entries stay admin-only
        self.assertIn('Company toolbox talk', [i['title'] for i in self.library(ADMIN)['items']])

    def test_organization_isolation(self):
        item_id, item = self.published()
        for headers in (OTHER_ADMIN, OTHER_MEMBER):
            self.assertEqual(self.library(headers)['items'], [])
            self.assertEqual(self.client.get(f"/api/files/{item['file']['id']}", headers=headers).status_code, 404)
            self.assertEqual(self.client.get(f'/api/files?entity_kind=form_library&entity_id={item_id}', headers=headers).status_code, 404)
        self.assertEqual(self.upload(item_id, OTHER_ADMIN).status_code, 404)
        self.assertEqual(self.client.post(f'/api/forms/library/{item_id}/remove', headers=OTHER_ADMIN, json={'expected_version': 2}).status_code, 404)
        # The same ID in another organization is a separate entry that cannot attach this organization's file.
        self.assertEqual(self.item(item_id, OTHER_ADMIN, file_id=item['file']['id']).status_code, 422)
        self.assertEqual(self.item(item_id, OTHER_ADMIN, title='Their form').status_code, 200)
        self.assertEqual(self.library(ADMIN)['items'][0]['title'], 'VDOT Form C-85')

    def test_validation_versions_and_retries(self):
        item_id = str(uuid4())
        for extra in ({'title': ''}, {'title': 'x' * 121}, {'category': 'verified_form'}, {'description': 'x' * 501}, {'owner': 'me'}):
            with self.subTest(extra=extra):
                self.assertEqual(self.item(item_id, **extra).status_code, 422)
        first = self.item(item_id)
        self.assertEqual(self.item(item_id).json(), first.json())  # identical retry
        self.assertEqual(self.item(item_id, title='Changed').status_code, 409)  # stale version
        other_item = str(uuid4())
        self.item(other_item, title='Other')
        foreign_file = self.upload(other_item).json()['id']
        self.assertEqual(self.item(item_id, version=1, file_id=foreign_file).status_code, 422)  # file belongs to another entry
        self.assertEqual(self.upload(item_id, data=b'not a pdf').status_code, 415)
        self.assertEqual(self.upload(item_id, content_type='text/html', data=b'<script>').status_code, 415)
        self.assertEqual(self.upload(item_id, filename='..%2Fsecret.pdf').status_code, 422)
        file_id = str(uuid4())
        self.assertEqual(self.upload(item_id, file_id=file_id).json(), self.upload(item_id, file_id=file_id).json())  # idempotent upload

    def test_replace_rename_and_remove(self):
        item_id, item = self.published()
        replacement = self.upload(item_id, data=PDF + b'2026 edition', filename='C-85 2026.pdf').json()
        updated = self.item(item_id, version=2, title='VDOT Form C-85 (2026)', file_id=replacement['id']).json()
        self.assertEqual((updated['version'], updated['file']['filename']), (3, 'C-85 2026.pdf'))
        self.assertEqual(self.client.get(f"/api/files/{replacement['id']}", headers=MEMBER).content, PDF + b'2026 edition')
        self.assertEqual(self.client.post(f'/api/forms/library/{item_id}/remove', headers=ADMIN, json={'expected_version': 2}).status_code, 409)
        removed = self.client.post(f'/api/forms/library/{item_id}/remove', headers=ADMIN, json={'expected_version': 3})
        self.assertEqual(removed.json(), {'removed': True, 'version': 4})
        self.assertEqual(self.client.post(f'/api/forms/library/{item_id}/remove', headers=ADMIN, json={'expected_version': 3}).json()['version'], 4)  # retry
        self.assertEqual(self.library(MEMBER)['items'], [])
        self.assertEqual(self.library(ADMIN)['items'], [])
        self.assertEqual(self.client.get(f"/api/files/{replacement['id']}", headers=MEMBER).status_code, 404)
        self.assertEqual(self.upload(item_id).status_code, 404)
        self.assertEqual(self.item(item_id, version=4).status_code, 404)

    def test_library_without_file_storage(self):
        self.client.__exit__(None, None, None)
        self.client = self.make_client(files=False)
        self.assertEqual(self.item(str(uuid4())).status_code, 200)
        listing = self.library(ADMIN)
        self.assertEqual((listing['uploads_enabled'], listing['items'][0]['file']), (False, None))
        self.assertEqual(self.library(MEMBER)['items'], [])

    def test_concurrent_edits_apply_once(self):
        item_id = str(uuid4())
        self.item(item_id)
        bodies = [{'title': 'First'}, {'title': 'Second'}]
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = sorted(pool.map(lambda b: self.item(item_id, version=1, **b).status_code, bodies))
        self.assertEqual(statuses, [200, 409])


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'), 'Dedicated PostgreSQL test database not configured')
class PostgreSQLFormsHubTests(FormsHubTests):
    """Same scenarios on PostgreSQL in a disposable schema (Codex runs these in Cloud Shell)."""
    def setUp(self):
        from psycopg.conninfo import make_conninfo
        from services.workspace_preview.postgres import PostgreSQLStorage
        dsn, schema = os.environ['WZOS_TEST_DATABASE_URL'], 'test_' + uuid4().hex
        bootstrap = PostgreSQLStorage(dsn)
        self.addCleanup(bootstrap.close)
        with bootstrap.connect() as db:
            db.execute('CREATE SCHEMA ' + schema)
        def drop():
            with bootstrap.connect() as db:
                db.execute('DROP SCHEMA ' + schema + ' CASCADE')
        self.addCleanup(drop)
        self.storage = PostgreSQLStorage(make_conninfo(dsn, options='-c search_path=' + schema))
        self.addCleanup(self.storage.close)
        self.storage.initialize()
        super().setUp()


if __name__ == '__main__':
    unittest.main()
