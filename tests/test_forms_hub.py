import io
import os
import sqlite3
import tempfile
import unittest
import zipfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from services.v2.knowledge.store import Store
from services.workspace_preview import files, forms_hub
from services.workspace_preview.app import create_app
from services.workspace_preview.files import LocalFiles

MEMBER, ADMIN = {'X-Preview-Actor': 'enterprise-general'}, {'X-Preview-Actor': 'enterprise-admin'}
OTHER_ADMIN, OTHER_MEMBER = {'X-Preview-Actor': 'core-admin'}, {'X-Preview-Actor': 'core-general'}
PDF = b'%PDF-1.7\n% synthetic C-85 placeholder for tests\n'
DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
DOC_LINK = 'https://docs.google.com/document/d/1AbCdEfGhIjKlMnOp/edit?usp=sharing'


def office(main, extra=(), content_types='<Types/>'):
    """A minimal synthetic Office Open XML package."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as package:
        package.writestr('[Content_Types].xml', content_types)
        package.writestr(main, '<synthetic/>')
        for name in extra:
            package.writestr(name, 'x')
    return buffer.getvalue()


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

    def raw(self):
        return self.storage.connect() if self.storage else closing(sqlite3.connect(self.db))

    def stored_objects(self):
        return sorted(p.name for p in (Path(self.temp.name) / 'files').rglob('*') if p.is_file())

    def item(self, item_id, headers=ADMIN, version=0, client=None, **extra):
        body = {'expected_version': version, 'title': 'VDOT Form C-85', 'category': 'official_agency_form',
                'description': 'Pavement marking daily log', 'file_id': None, 'link': None, **extra}
        return (client or self.client).put(f'/api/forms/library/{item_id}', headers=headers, json=body)

    def upload(self, item_id, headers=ADMIN, data=PDF, file_id=None, content_type='application/pdf', filename='C-85.pdf'):
        file_id = file_id or str(uuid4())
        return self.client.put(f'/api/files/{file_id}?entity_kind=form_library&entity_id={item_id}&filename={filename}',
                               headers={**headers, 'Content-Type': content_type}, content=data)

    def delete(self, item_id, version, headers=ADMIN):
        return self.client.post(f'/api/forms/library/{item_id}/delete', headers=headers, json={'expected_version': version})

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
        self.assertEqual((item['category_label'], item['file']['filename'], item['complete'], item['verified_by_wzos']),
                         ('Official agency form', 'C-85.pdf', True, False))
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
        self.assertEqual(self.delete(item_id, 2, MEMBER).status_code, 403)
        self.assertEqual(self.client.get(f"/api/files/{item['file']['id']}", headers=MEMBER).status_code, 200)
        unfinished = str(uuid4())
        self.item(unfinished, title='Company toolbox talk', category='company_form')
        self.assertEqual([i['title'] for i in self.library(MEMBER)['items']], ['VDOT Form C-85'])  # unfinished entries stay admin-only
        admin_view = {i['title']: i['complete'] for i in self.library(ADMIN)['items']}
        self.assertEqual(admin_view, {'VDOT Form C-85': True, 'Company toolbox talk': False})

    def test_organization_isolation(self):
        item_id, item = self.published()
        for headers in (OTHER_ADMIN, OTHER_MEMBER):
            self.assertEqual(self.library(headers)['items'], [])
            self.assertEqual(self.client.get(f"/api/files/{item['file']['id']}", headers=headers).status_code, 404)
            self.assertEqual(self.client.get(f'/api/files?entity_kind=form_library&entity_id={item_id}', headers=headers).status_code, 404)
        self.assertEqual(self.upload(item_id, OTHER_ADMIN).status_code, 404)
        self.assertEqual(self.delete(item_id, 2, OTHER_ADMIN).status_code, 404)
        self.assertEqual(self.client.get(f"/api/files/{item['file']['id']}", headers=MEMBER).status_code, 200)  # untouched
        # The same ID in another organization is a separate entry that cannot attach this organization's file.
        self.assertEqual(self.item(item_id, OTHER_ADMIN, file_id=item['file']['id']).status_code, 422)
        other = self.item(item_id, OTHER_ADMIN, title='Their form')
        self.assertEqual(other.status_code, 200)
        self.assertEqual(self.delete(item_id, 1, OTHER_ADMIN).status_code, 200)  # deleting theirs leaves ours alone
        self.assertEqual(self.library(ADMIN)['items'][0]['title'], 'VDOT Form C-85')
        self.assertEqual(self.client.get(f"/api/files/{item['file']['id']}", headers=MEMBER).content, PDF)

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
        # Interrupted add: the entry exists, the attach is retried with the same body after it already succeeded.
        attached = self.item(item_id, version=1, file_id=file_id)
        self.assertEqual(self.item(item_id, version=1, file_id=file_id).json(), attached.json())

    def test_replace_erases_previous_file_and_delete_is_permanent(self):
        item_id, item = self.published()
        abandoned = self.upload(item_id, filename='never-attached.pdf').json()  # for example, an interrupted earlier attempt
        replacement = self.upload(item_id, data=PDF + b'2026 edition', filename='C-85 2026.pdf').json()
        updated = self.item(item_id, version=2, title='VDOT Form C-85 (2026)', file_id=replacement['id']).json()
        self.assertEqual((updated['version'], updated['file']['filename']), (3, 'C-85 2026.pdf'))
        self.assertEqual(self.client.get(f"/api/files/{replacement['id']}", headers=MEMBER).content, PDF + b'2026 edition')
        for old in (item['file']['id'], abandoned['id']):  # replaced and unattached files are erased, not kept
            self.assertEqual(self.client.get(f'/api/files/{old}', headers=ADMIN).status_code, 404)
        self.assertEqual(self.stored_objects(), [replacement['id']])
        # A details-only edit keeps the current file.
        self.assertEqual(self.item(item_id, version=3, title='Renamed', file_id=replacement['id']).json()['file']['id'], replacement['id'])
        self.assertEqual(self.delete(item_id, 3).status_code, 409)
        self.assertEqual(self.delete(item_id, 4).json(), {'deleted': True})
        self.assertEqual(self.delete(item_id, 4).status_code, 404)  # retry: already gone
        self.assertEqual((self.library(MEMBER)['items'], self.library(ADMIN)['items']), ([], []))
        self.assertEqual(self.client.get(f"/api/files/{replacement['id']}", headers=MEMBER).status_code, 404)
        self.assertEqual(self.stored_objects(), [])  # the stored object itself is gone
        self.assertEqual(self.upload(item_id).status_code, 404)
        with self.raw() as db:
            for table in ('module_records', 'module_revisions'):
                self.assertEqual(db.execute(f"SELECT COUNT(*) FROM {table} WHERE kind='form_library' AND id=?", (item_id,)).fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM workspace_files WHERE entity_id=?", (item_id,)).fetchone()[0], 0)
        self.assertEqual(self.item(item_id).json()['version'], 1)  # the identifier can start over as a new entry

    def test_delete_rolls_back_when_storage_fails(self):
        item_id, item = self.published()
        with patch.object(LocalFiles, 'delete', side_effect=OSError('storage down')):
            response = self.delete(item_id, 2)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.client.get(f"/api/files/{item['file']['id']}", headers=MEMBER).content, PDF)  # nothing was deleted
        self.assertEqual(self.delete(item_id, 2).json(), {'deleted': True})
        self.assertEqual(self.stored_objects(), [])

    def test_word_and_excel_uploads(self):
        docx, xlsx = office('word/document.xml'), office('xl/workbook.xml')
        for data, content_type, name in ((docx, DOCX, 'Toolbox talk.docx'), (xlsx, XLSX, 'Crew roster.xlsx')):
            with self.subTest(name=name):
                item_id = str(uuid4())
                self.item(item_id, title=name, category='company_form')
                stored = self.upload(item_id, data=data, content_type=content_type, filename=name)
                self.assertEqual(stored.status_code, 200, stored.text)
                self.assertEqual(self.item(item_id, version=1, title=name, category='company_form', file_id=stored.json()['id']).status_code, 200)
                download = self.client.get(f"/api/files/{stored.json()['id']}", headers=MEMBER)
                self.assertEqual((download.content, download.headers['content-type'].split(';')[0]), (data, content_type))
        item_id = str(uuid4())
        self.item(item_id)
        refused = {
            'macro project': (office('word/document.xml', ['word/vbaProject.bin']), DOCX),
            'macro content type': (office('xl/workbook.xml', content_types='<Types><Override ContentType="application/vnd.ms-excel.sheet.macroEnabled.main+xml"/></Types>'), XLSX),
            'workbook labelled as Word': (xlsx, DOCX),
            'truncated zip': (b'PK\x03\x04 truncated', DOCX),
            'legacy .doc': (b'\xd0\xcf\x11\xe0' + b'0' * 64, 'application/msword'),
            'macro-enabled type': (docx, 'application/vnd.ms-word.document.macroEnabled.12'),
        }
        for label, (data, content_type) in refused.items():
            with self.subTest(refused=label):
                self.assertEqual(self.upload(item_id, data=data, content_type=content_type, filename='form.docx').status_code, 415)

    def test_office_types_stay_limited_to_team_forms(self):
        self.assertEqual((files.KIND_TYPES['order'], files.KIND_TYPES['form']), (set(files.TYPES), set(files.TYPES)))
        self.assertTrue(set(files.OFFICE) <= files.KIND_TYPES['form_library'])

    def test_google_links(self):
        cases = {
            DOC_LINK: ('Google Docs', ['PDF', 'Word']),
            'https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOp/edit#gid=0': ('Google Sheets', ['PDF', 'Excel']),
            'https://docs.google.com/forms/d/e/1FAIpQLSdSynthetic123/viewform': ('Google Forms', []),
            'https://drive.google.com/file/d/1AbCdEfGhIjKlMnOp/view': ('Google Drive', ['File']),
        }
        for url, (service, downloads) in cases.items():
            with self.subTest(url=url):
                saved = self.item(str(uuid4()), title=service + ' form', category='company_form', link=url)
                self.assertEqual(saved.status_code, 200, saved.text)
                link = saved.json()['link']
                self.assertEqual((link['service'], [d['label'] for d in link['downloads']], saved.json()['complete']), (service, downloads, True))
                self.assertNotIn('#', link['url'])
                self.assertTrue(all(d['url'].startswith('https://') and '1AbCdEfGhIjKlMnOp' in d['url'] for d in link['downloads']))
        self.assertEqual(len(self.library(MEMBER)['items']), 4)  # link forms are complete, so members see them
        for bad in ('http://docs.google.com/document/d/1AbCdEfGhIjKlMnOp/edit', 'https://docs.google.com.evil.example/document/d/1AbCdEfGhIjKlMnOp',
                    'https://evil.example/https://docs.google.com/document/d/1AbCdEfGhIjKlMnOp', 'https://user@docs.google.com/document/d/1AbCdEfGhIjKlMnOp',
                    'https://docs.google.com:8443/document/d/1AbCdEfGhIjKlMnOp', 'javascript:alert(1)', 'https://docs.google.com/presentation/d/1AbCdEfGhIjKlMnOp',
                    'https://docs.google.com/document/d/short', 'https://docs.google.com\\@evil.example/document/d/1AbCdEfGhIjKlMnOp'):
            with self.subTest(bad=bad):
                self.assertEqual(self.item(str(uuid4()), link=bad).status_code, 422)
        self.assertEqual(self.item(str(uuid4()), MEMBER, link=DOC_LINK).status_code, 403)
        # A form is a file or a link, never both; switching a file form to a link erases its file.
        item_id, item = self.published()
        self.assertEqual(self.item(item_id, version=2, file_id=item['file']['id'], link=DOC_LINK).status_code, 422)
        switched = self.item(item_id, version=2, link=DOC_LINK).json()
        self.assertEqual((switched['file'], switched['link']['service']), (None, 'Google Docs'))
        self.assertEqual(self.client.get(f"/api/files/{item['file']['id']}", headers=MEMBER).status_code, 404)

    def test_library_without_file_storage(self):
        self.client.__exit__(None, None, None)
        self.client = self.make_client(files=False)
        self.assertEqual(self.item(str(uuid4())).status_code, 200)
        listing = self.library(ADMIN)
        self.assertEqual((listing['uploads_enabled'], listing['items'][0]['file']), (False, None))
        self.assertEqual(self.library(MEMBER)['items'], [])
        # Google links still work without file storage, and delete still succeeds.
        linked = self.item(str(uuid4()), link=DOC_LINK).json()
        self.assertEqual([i['title'] for i in self.library(MEMBER)['items']], ['VDOT Form C-85'])
        self.assertEqual(self.delete(linked['id'], 1).json(), {'deleted': True})

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
