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

    def make_client(self, files=True, raise_errors=True):
        store = LocalFiles(Path(self.temp.name) / 'files') if files else None
        client = TestClient(create_app(self.db, Store(Path(self.temp.name) / 'sources', {}), storage=self.storage, file_store=store),
                            raise_server_exceptions=raise_errors)
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
        self.assertEqual(self.delete(item_id, 4).json(), {'deleted': True, 'cleanup_pending': False})
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

    # ---- Review finding 1: deletion and replacement must never leave a published form pointing at a missing object.

    def file_rows(self, item_id):
        with self.raw() as db:
            return db.execute("SELECT COUNT(*) FROM workspace_files WHERE entity_id=?", (item_id,)).fetchone()[0]

    def unreachable(self, *file_ids):
        for file_id in file_ids:
            for headers in (ADMIN, MEMBER):
                self.assertEqual(self.client.get(f'/api/files/{file_id}', headers=headers).status_code, 404)

    def cleanup(self, client=None):
        return (client or self.client).post('/api/forms/library/cleanup', headers=ADMIN).json()['cleanup_pending']

    def test_second_object_failure_keeps_form_deleted_and_recovers_after_restart(self):
        item_id, item = self.published()
        extra = self.upload(item_id, filename='unattached.pdf').json()
        real, calls = LocalFiles.delete, []
        def flaky(store, key):  # the first object is really erased, the second fails
            calls.append(key)
            if len(calls) == 2:
                raise OSError('storage down')
            real(store, key)
        with patch.object(LocalFiles, 'delete', autospec=True, side_effect=flaky):
            response = self.delete(item_id, 2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'deleted': True, 'cleanup_pending': True})  # never claims nothing was deleted
        self.assertEqual(len(self.stored_objects()), 1)
        self.assertEqual((self.library(MEMBER)['items'], self.library(ADMIN)['items']), ([], []))  # no longer published
        self.unreachable(item['file']['id'], extra['id'])  # 404, not a broken 503 download
        self.assertEqual(self.upload(item_id).status_code, 404)
        self.assertEqual(self.item(item_id, version=3).status_code, 404)
        self.assertGreater(self.library(ADMIN)['cleanup_pending'], 0)
        restarted = self.make_client()  # recovery state is durable across a restart
        try:
            self.assertEqual(self.cleanup(restarted), 0)
        finally:
            restarted.__exit__(None, None, None)
        self.assertEqual((self.stored_objects(), self.file_rows(item_id)), ([], 0))
        self.assertEqual(self.delete(item_id, 2).status_code, 404)
        self.assertEqual(self.library(ADMIN)['cleanup_pending'], 0)

    def test_metadata_failure_after_object_erased_is_retried(self):
        item_id, item = self.published()
        with patch.object(forms_hub, 'forget_file', side_effect=OSError('database unavailable')):
            response = self.delete(item_id, 2)
        self.assertEqual(response.json(), {'deleted': True, 'cleanup_pending': True})
        self.assertEqual((self.stored_objects(), self.file_rows(item_id)), ([], 1))  # object gone, row still queued
        self.assertEqual(self.library(MEMBER)['items'], [])
        self.unreachable(item['file']['id'])
        self.assertEqual(self.delete(item_id, 2).json(), {'deleted': True, 'cleanup_pending': False})  # repeating finishes it
        self.assertEqual(self.file_rows(item_id), 0)

    def test_failure_before_commit_changes_nothing(self):
        item_id, item = self.published()
        self.client.__exit__(None, None, None)
        self.client = self.make_client(raise_errors=False)
        with patch.object(forms_hub, 'queue_files', side_effect=RuntimeError('database unavailable')):
            self.assertEqual(self.delete(item_id, 2).status_code, 500)
            replacement = self.upload(item_id, data=PDF + b'new').json()
            self.assertEqual(self.item(item_id, version=2, file_id=replacement['id']).status_code, 500)
        # Nothing was hidden, queued or erased: the published form still downloads.
        self.assertEqual(self.library(MEMBER)['items'][0]['file']['id'], item['file']['id'])
        self.assertEqual(self.client.get(f"/api/files/{item['file']['id']}", headers=MEMBER).content, PDF)
        self.assertEqual(len(self.stored_objects()), 2)
        self.assertEqual(self.library(ADMIN)['cleanup_pending'], 0)

    def test_replacement_stays_published_when_old_file_cannot_be_erased(self):
        item_id, item = self.published()
        replacement = self.upload(item_id, data=PDF + b'2026 edition', filename='new.pdf').json()
        with patch.object(LocalFiles, 'delete', side_effect=OSError('storage down')):
            updated = self.item(item_id, version=2, file_id=replacement['id'])
        self.assertEqual(updated.status_code, 200)
        self.assertEqual((updated.json()['file']['id'], updated.json()['cleanup_pending']), (replacement['id'], True))
        self.assertEqual(self.client.get(f"/api/files/{replacement['id']}", headers=MEMBER).content, PDF + b'2026 edition')
        self.unreachable(item['file']['id'])  # the old file is queued, so nobody can reach it
        listed = self.client.get(f'/api/files?entity_kind=form_library&entity_id={item_id}', headers=ADMIN).json()['items']
        self.assertEqual([f['id'] for f in listed], [replacement['id']])
        self.assertEqual(len(self.stored_objects()), 2)
        self.assertEqual(self.cleanup(), 0)
        self.assertEqual(self.stored_objects(), [replacement['id']])
        self.assertEqual(self.client.get(f"/api/files/{replacement['id']}", headers=MEMBER).status_code, 200)

    def test_overlapping_cleanups_cannot_erase_a_reused_file_id(self):
        # Codex repair review (51ed59e): a stale cleanup erased a file re-uploaded under the same ID.
        item_id, item = self.published()
        file_a = item['file']['id']
        replacement = self.upload(item_id, data=PDF + b'B', filename='b.pdf').json()
        with patch.object(LocalFiles, 'delete', side_effect=OSError('storage down')):
            self.assertEqual(self.item(item_id, version=2, file_id=replacement['id']).json()['cleanup_pending'], True)  # A queued, B published
        real, other, seen = LocalFiles.delete, self.make_client(), {}
        def interleave(store, key):
            if not seen:  # cleanup 1 is paused just before erasing A; everything below happens meanwhile
                seen['paused'] = True
                self.assertEqual(self.cleanup(other), 0)  # cleanup 2 erases and forgets A
                retry = self.upload(item_id, file_id=file_a)  # an upload retry with A's original ID
                seen['retry'] = retry.status_code
                seen['republish'] = self.item(item_id, version=3, file_id=file_a).status_code
            real(store, key)
        try:
            with patch.object(LocalFiles, 'delete', autospec=True, side_effect=interleave):
                self.assertEqual(self.cleanup(), 0)  # cleanup 1 resumes with its stale queue entry
        finally:
            other.__exit__(None, None, None)
        self.assertEqual((seen['retry'], seen['republish']), (409, 422))  # the retired ID is refused, not recreated
        current = self.library(MEMBER)['items']
        self.assertEqual([(i['version'], i['file']['id'], i['complete']) for i in current], [(3, replacement['id'], True)])
        self.assertEqual(self.client.get(f"/api/files/{replacement['id']}", headers=MEMBER).content, PDF + b'B')
        self.assertEqual(self.stored_objects(), [replacement['id']])
        # A fresh ID for the same content works normally.
        fresh = self.upload(item_id).json()
        self.assertEqual(self.item(item_id, version=3, file_id=fresh['id']).status_code, 200)
        self.assertEqual(self.client.get(f"/api/files/{fresh['id']}", headers=MEMBER).content, PDF)

    def test_retired_ids_are_per_organization_and_survive_deletion(self):
        item_id, item = self.published()
        self.assertEqual(self.delete(item_id, 2).json(), {'deleted': True, 'cleanup_pending': False})
        recreated = str(uuid4())
        self.item(recreated)
        self.assertEqual(self.upload(recreated, file_id=item['file']['id']).status_code, 409)  # retired in this organization

    # ---- Review finding 2: members reach only the published file.

    def test_members_only_reach_the_published_file(self):
        unfinished = str(uuid4())
        self.item(unfinished, title='Unfinished')
        hidden = self.upload(unfinished).json()  # uploaded, never attached
        files = f'/api/files?entity_kind=form_library&entity_id={unfinished}'
        self.assertEqual(self.client.get(files, headers=MEMBER).status_code, 404)
        self.assertEqual(self.client.get(f"/api/files/{hidden['id']}", headers=MEMBER).status_code, 404)
        self.assertEqual([f['id'] for f in self.client.get(files, headers=ADMIN).json()['items']], [hidden['id']])  # admins finish it
        self.assertEqual(self.client.get(f"/api/files/{hidden['id']}", headers=ADMIN).status_code, 200)
        item_id, item = self.published()
        abandoned = self.upload(item_id, data=PDF + b'draft replacement', filename='draft.pdf').json()  # never attached
        files = f'/api/files?entity_kind=form_library&entity_id={item_id}'
        self.assertEqual([f['id'] for f in self.client.get(files, headers=MEMBER).json()['items']], [item['file']['id']])
        self.assertEqual(self.client.get(f"/api/files/{abandoned['id']}", headers=MEMBER).status_code, 404)
        self.assertEqual(self.client.get(f"/api/files/{item['file']['id']}", headers=MEMBER).content, PDF)
        self.assertEqual(self.client.get(f"/api/files/{abandoned['id']}", headers=ADMIN).status_code, 200)
        self.assertEqual(len(self.client.get(files, headers=ADMIN).json()['items']), 2)
        for headers in (OTHER_ADMIN, OTHER_MEMBER):
            for file_id in (item['file']['id'], abandoned['id'], hidden['id']):
                self.assertEqual(self.client.get(f'/api/files/{file_id}', headers=headers).status_code, 404)
            self.assertEqual(self.client.get(files, headers=headers).status_code, 404)

    def test_link_only_forms_expose_no_files(self):
        item_id = str(uuid4())
        self.item(item_id, link=DOC_LINK)
        self.assertEqual(self.client.get(f'/api/files?entity_kind=form_library&entity_id={item_id}', headers=MEMBER).status_code, 404)

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
        self.assertEqual(self.delete(linked['id'], 1).json(), {'deleted': True, 'cleanup_pending': False})

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
