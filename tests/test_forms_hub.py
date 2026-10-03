import json
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

MEMBER, ADMIN = {'X-Preview-Actor': 'enterprise-general'}, {'X-Preview-Actor': 'enterprise-admin'}
OTHER_ADMIN, OTHER_MEMBER = {'X-Preview-Actor': 'core-admin'}, {'X-Preview-Actor': 'core-general'}

JSA_COMPLETE = {'work_date': '2026-10-03', 'competent_person': 'Jordan Lee', 'work_description': 'Long-line striping',
                'tasks': 'Stripe centerline', 'controls': '1. Moving traffic - TMA and cones', 'ppe': ['Hard hat', 'High-visibility vest'],
                'emergency_procedures': 'Call 911; nearest facility listed'}


class FormsHubTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'WZOS_WORKSPACE_PREVIEW': '1', 'K_SERVICE': '', 'GAE_ENV': '', 'NETLIFY': ''})
        self.env.start()
        self.db = Path(self.temp.name) / 'db.sqlite'
        self.client = self.make_client()

    storage = None

    def make_client(self):
        client = TestClient(create_app(self.db, Store(Path(self.temp.name) / 'sources', {}), storage=self.storage))
        client.__enter__()
        return client

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.env.stop()
        self.temp.cleanup()

    def template(self, template_id, client=None):
        items = (client or self.client).get('/api/forms/templates', headers=MEMBER).json()['items']
        return next(t for t in items if t['id'] == template_id)

    def body(self, template_id='jsa', version=0, fields=None, client=None, **extra):
        t = self.template(template_id, client)
        return {'expected_version': version, 'template_id': t['id'], 'template_revision': t['revision'],
                'template_checksum': t['checksum'], 'title': 'Granby Street JSA', 'location': 'Norfolk',
                'order_id': None, 'fields': fields if fields is not None else {}, **extra}

    def put(self, record, body, headers=MEMBER, client=None):
        return (client or self.client).put(f'/api/forms/{record}', headers=headers, json=body)

    def status(self, record, version, action, headers=MEMBER, note=''):
        return self.client.post(f'/api/forms/{record}/status', headers=headers, json={'expected_version': version, 'action': action, 'note': note})

    def test_catalog_distinguishes_internal_and_official_references(self):
        self.assertEqual(self.client.get('/api/forms/templates').status_code, 401)
        items = {t['id']: t for t in self.client.get('/api/forms/templates', headers=MEMBER).json()['items']}
        self.assertEqual(set(items), {'jsa', 'incident', 'dvir', 'c85_prep'})
        self.assertEqual({items[k]['category'] for k in ('jsa', 'incident', 'dvir')}, {'internal_worksheet'})
        official = items['c85_prep']
        self.assertEqual(official['category'], 'official_form_reference')
        self.assertFalse(official['official_reference']['official_template_stored'])
        self.assertEqual(official['official_reference']['applicability'], 'not_determined')
        self.assertEqual(official['official_reference']['source']['review_status'], 'unreviewed')
        self.assertIn('not the C-85', official['summary'])
        detail = self.client.get('/api/forms/templates/jsa/1', headers=MEMBER).json()
        definition = {k: v for k, v in detail.items() if k not in ('checksum', 'latest_revision')}
        self.assertEqual(detail['checksum'], forms_hub.checksum(definition))
        self.assertEqual(self.client.get('/api/forms/templates/jsa/9', headers=MEMBER).status_code, 404)

    def test_create_save_reopen_edit_history_and_restart(self):
        record = str(uuid4())
        first = self.put(record, self.body(fields={'work_date': '2026-10-03', 'ppe': ['Gloves', 'Hard hat']}, order_id='enterprise-sample'))
        self.assertEqual(first.status_code, 200, first.text)
        saved = first.json()
        self.assertEqual((saved['version'], saved['status'], saved['template']['category']), (1, 'draft', 'internal_worksheet'))
        self.assertEqual(saved['fields']['ppe'], ['Hard hat', 'Gloves'])  # catalog order
        self.assertIn('competent_person', {m['key'] for m in saved['missing_required']})
        self.assertFalse(saved['permissions']['can_submit'])
        reopened = self.client.get(f'/api/forms/{record}', headers=MEMBER).json()
        self.assertEqual(reopened['fields'], saved['fields'])
        second = self.body(version=1, fields={**JSA_COMPLETE}, order_id='enterprise-sample')
        edited = self.put(record, second).json()
        self.assertEqual((edited['version'], edited['missing_required']), (2, []))
        self.assertEqual(self.put(record, second).json()['version'], 2)  # identical retry
        self.assertEqual(self.put(record, {**second, 'title': 'Changed'}).status_code, 409)  # stale
        history = self.client.get(f'/api/forms/{record}/history', headers=MEMBER).json()['items']
        self.assertEqual([h['version'] for h in history], [2, 1])
        self.assertIn('competent_person', history[0]['changed_fields'])
        restarted = self.make_client()
        try:
            self.assertEqual(restarted.get(f'/api/forms/{record}', headers=MEMBER).json()['version'], 2)
        finally:
            restarted.__exit__(None, None, None)

    def test_invalid_input_is_rejected(self):
        record = str(uuid4())
        cases = [
            {'fields': {'unknown': 'x'}},
            {'fields': {'traffic_volume': 'Extreme'}},
            {'fields': {'ppe': ['Gloves', 'Gloves']}},
            {'fields': {'competent_person': 'x' * 201}},
            {'fields': {'work_date': '10/03/2026'}},
            {'fields': {'start_time': '25:00'}},
            {'fields': {'speed_limit': True}},
            {'fields': {'speed_limit': 120}},
            {'title': ''},
            {'status': 'reviewed'},
        ]
        for extra in cases:
            with self.subTest(extra=extra):
                self.assertEqual(self.put(record, {**self.body(), **extra}).status_code, 422)
        c85 = self.body('c85_prep')
        self.assertEqual(self.put(record, {**c85, 'fields': {'work': [{'work_type': 'x'}] * 11}}).status_code, 422)
        self.assertEqual(self.put(record, {**c85, 'fields': {'work': [{'signature': 'x'}]}}).status_code, 422)
        self.assertEqual(self.put(record, {**self.body(), 'template_checksum': '0' * 64}).status_code, 409)
        self.assertEqual(self.put(record, {**self.body(), 'template_id': 'whistleblower'}).status_code, 422)
        self.assertEqual(self.put(record, {**self.body(), 'order_id': 'core-sample'}).status_code, 404)
        self.assertEqual(self.client.get('/api/forms', headers=MEMBER).json()['total'], 0)
        self.assertEqual(self.put(record, self.body()).status_code, 200)
        self.assertEqual(self.put(record, self.body('incident', version=1)).status_code, 409)  # template fixed

    def test_review_workflow_and_locking(self):
        record = str(uuid4())
        self.put(record, self.body(fields={'work_date': '2026-10-03'}))
        self.assertEqual(self.status(record, 1, 'submit').status_code, 422)
        self.put(record, self.body(version=1, fields=JSA_COMPLETE))
        submitted = self.status(record, 2, 'submit')
        self.assertEqual(submitted.json()['status'], 'ready_for_review')
        self.assertEqual(self.status(record, 2, 'submit').json()['version'], 3)  # identical retry
        self.assertEqual(self.put(record, self.body(version=3, fields=JSA_COMPLETE)).status_code, 409)  # locked
        self.assertEqual(self.status(record, 3, 'mark_reviewed').status_code, 403)
        self.assertEqual(self.status(record, 3, 'return', ADMIN).status_code, 422)  # note required
        returned = self.status(record, 3, 'return', ADMIN, 'Add the medical facility').json()
        self.assertEqual((returned['status'], returned['review']['note']), ('returned', 'Add the medical facility'))
        edited = self.put(record, self.body(version=4, fields={**JSA_COMPLETE, 'medical_facility': 'Sentara Norfolk General'})).json()
        self.assertEqual(edited['status'], 'draft')
        self.status(record, 5, 'submit')
        self.assertEqual(self.status(record, 5, 'mark_reviewed', ADMIN).status_code, 409)  # stale
        reviewed = self.status(record, 6, 'mark_reviewed', ADMIN).json()
        self.assertEqual(reviewed['status'], 'reviewed')
        self.assertEqual(self.status(record, 7, 'cancel').status_code, 409)
        self.assertEqual(self.status(record, 7, 'reopen').status_code, 403)
        self.assertEqual(self.status(record, 7, 'reopen', ADMIN).json()['status'], 'draft')
        self.assertEqual(self.status(record, 8, 'cancel').json()['status'], 'cancelled')
        history = self.client.get(f'/api/forms/{record}/history', headers=MEMBER).json()['items']
        self.assertEqual([h['status'] for h in history][:4], ['cancelled', 'draft', 'reviewed', 'ready_for_review'])
        self.assertEqual(history[2]['author_id'], 'enterprise-admin')

    def test_member_admin_and_organization_isolation(self):
        mine, admins = str(uuid4()), str(uuid4())
        self.put(mine, self.body(fields=JSA_COMPLETE))
        self.put(admins, {**self.body(), 'title': 'Admin JSA'}, ADMIN)
        self.assertEqual(self.client.get('/api/forms', headers=MEMBER).json()['total'], 1)
        self.assertEqual(self.client.get('/api/forms', headers=ADMIN).json()['total'], 2)
        for path in ('', '/history', '/export'):
            self.assertEqual(self.client.get(f'/api/forms/{admins}{path}', headers=MEMBER).status_code, 404)
            self.assertEqual(self.client.get(f'/api/forms/{mine}{path}', headers=OTHER_ADMIN).status_code, 404)
            self.assertEqual(self.client.get(f'/api/forms/{mine}{path}', headers=OTHER_MEMBER).status_code, 404)
        self.assertEqual(self.status(mine, 1, 'submit', OTHER_ADMIN).status_code, 404)
        self.assertEqual(self.put(admins, self.body(version=1), MEMBER).status_code, 404)
        # Records are keyed per organization: another tenant using the same ID never reaches this record.
        self.assertEqual(self.put(mine, self.body(version=1), OTHER_ADMIN).status_code, 409)
        self.assertEqual(self.put(mine, {**self.body(), 'title': 'Other tenant'}, OTHER_ADMIN).json()['version'], 1)
        self.assertEqual(self.client.get(f'/api/forms/{mine}', headers=MEMBER).json()['title'], 'Granby Street JSA')
        self.assertEqual(self.client.get(f'/api/forms/{mine}', headers=OTHER_ADMIN).json()['title'], 'Other tenant')
        self.assertEqual(self.status(admins, 1, 'cancel', MEMBER).status_code, 404)
        self.assertEqual(self.client.get('/api/forms', headers=OTHER_ADMIN).json()['items'][0]['title'], 'Other tenant')
        # Admins may edit organization forms (existing Forms permission); the owner is preserved.
        edited = self.put(mine, {**self.body(version=1, fields=JSA_COMPLETE), 'title': 'Admin fix'}, ADMIN).json()
        self.assertEqual((edited['owner_id'], edited['title']), ('enterprise-general', 'Admin fix'))

    def test_template_revision_traceability(self):
        record = str(uuid4())
        self.put(record, self.body(fields=JSA_COMPLETE))
        catalog = json.loads(forms_hub.CATALOG.read_text(encoding='utf-8'))
        jsa2 = json.loads(json.dumps(next(t for t in catalog['templates'] if t['id'] == 'jsa')))
        jsa2['revision'] = 2
        jsa2['sections'][0]['fields'].append({'key': 'crew_size', 'label': 'Crew size', 'type': 'number', 'min': 1, 'max': 50, 'required': True})
        catalog['templates'].append(jsa2)
        path = Path(self.temp.name) / 'catalog.json'
        path.write_text(json.dumps(catalog), encoding='utf-8')
        with patch.object(forms_hub, 'CATALOG', path):
            client = self.make_client()
        try:
            old = client.get(f'/api/forms/{record}', headers=MEMBER).json()
            self.assertEqual((old['template']['revision'], old['missing_required']), (1, []))
            self.assertEqual(client.get('/api/forms/templates/jsa/1', headers=MEMBER).json()['latest_revision'], 2)
            self.assertEqual(self.template('jsa', client)['revision'], 2)
            rev1 = {**self.body(version=1, fields=JSA_COMPLETE), 'template_revision': 1, 'template_checksum': old['template']['checksum']}
            self.assertEqual(self.put(record, rev1, client=client).json()['version'], 2)  # existing record keeps rev 1
            self.assertEqual(self.put(str(uuid4()), {**rev1, 'expected_version': 0}, client=client).status_code, 409)  # new needs rev 2
            self.assertEqual(self.put(record, {**self.body(version=2, fields=JSA_COMPLETE, client=client)}, client=client).status_code, 409)
            fresh = self.put(str(uuid4()), self.body(fields=JSA_COMPLETE, client=client), client=client).json()
            self.assertEqual((fresh['template']['revision'], [m['key'] for m in fresh['missing_required']]), (2, ['crew_size']))
        finally:
            client.__exit__(None, None, None)

    def test_conditional_rules_and_rows(self):
        dvir = str(uuid4())
        saved = self.put(dvir, {**self.body('dvir'), 'title': 'Truck 12', 'fields': {'vehicle_id': 'T-12', 'trip_type': 'Pre-trip', 'brakes': 'Fail'}}).json()
        messages = [m['message'] for m in saved['missing_required']]
        self.assertIn('Describe each failed item in Defects', messages)
        self.assertEqual(sum('Check every item' in m for m in messages), 5)
        self.assertEqual(saved['fields']['tires'], 'Not checked')
        c85 = str(uuid4())
        prep = self.put(c85, {**self.body('c85_prep'), 'title': 'Marking log', 'fields': {'contractor': 'Acme', 'log_date': '2026-10-03', 'job_number': 'J-1',
                                                                                         'work': [{'work_type': '', 'color': ''}]}}).json()
        self.assertEqual([m['key'] for m in prep['missing_required']], ['work'])  # blank rows are dropped
        self.assertEqual(prep['fields']['work'], [])

    def test_search_filters_and_pagination(self):
        for title, template_id in (('Granby 100% JSA', 'jsa'), ('Truck check', 'dvir'), ('Marking log', 'c85_prep')):
            self.put(str(uuid4()), {**self.body(template_id), 'title': title, 'order_id': 'enterprise-sample' if template_id == 'jsa' else None})
        listing = lambda q: self.client.get('/api/forms?' + q, headers=MEMBER).json()
        self.assertEqual([i['title'] for i in listing('q=granby')['items']], ['Granby 100% JSA'])
        self.assertEqual(listing('q=100%25')['total'], 1)
        self.assertEqual(listing('q=_')['total'], 0)  # wildcard characters are literal
        self.assertEqual([i['title'] for i in listing('category=official_form_reference')['items']], ['Marking log'])
        self.assertEqual(listing('category=internal_worksheet')['total'], 2)
        self.assertEqual(listing('order_id=enterprise-sample')['total'], 1)
        self.assertEqual(listing('status=reviewed')['total'], 0)
        page = listing('limit=2&offset=2')
        self.assertEqual((page['total'], len(page['items'])), (3, 1))
        self.assertEqual(self.client.get('/api/forms?limit=51', headers=MEMBER).status_code, 422)

    def test_export_report_and_legacy_compatibility(self):
        record = str(uuid4())
        self.put(record, {**self.body('c85_prep'), 'title': 'Marking log', 'order_id': 'enterprise-sample', 'fields': {'contractor': '=cmd'}})
        export = self.client.get(f'/api/forms/{record}/export', headers=MEMBER)
        self.assertIn('attachment', export.headers['content-disposition'])
        document = export.json()
        self.assertFalse(document['official_submission'])
        self.assertEqual(document['record']['template']['official_reference']['form_identifier'], 'Form C-85')
        self.assertIn('PREPARATION WORKSHEET ONLY', document['notice'])
        self.assertEqual(document['revision_history'][0]['version'], 1)
        report = self.client.get('/api/orders/enterprise-sample/report', headers=ADMIN).json()
        self.assertEqual([(f['id'], f['title'], f['status']) for f in report['forms']], [(record, 'Marking log', 'draft')])
        legacy_id = str(uuid4())
        legacy = {'request_id': legacy_id, 'expected_version': 0, 'form_type': 'incident', 'title': 'Old draft', 'details': 'Synthetic'}
        self.assertEqual(self.client.put(f'/api/modules/forms/{legacy_id}', headers=MEMBER, json=legacy).status_code, 200)
        view = self.client.get(f'/api/forms/{legacy_id}', headers=MEMBER).json()
        self.assertTrue(view['legacy'])
        self.assertFalse(view['permissions']['can_edit'])
        self.assertEqual(self.client.get('/api/forms?category=legacy', headers=MEMBER).json()['total'], 1)
        self.assertEqual(self.put(legacy_id, self.body('incident', version=1)).status_code, 409)
        self.assertEqual(self.status(legacy_id, 1, 'cancel').status_code, 409)
        modern = {'request_id': record, 'expected_version': 1, 'form_type': 'incident', 'title': 'Overwrite'}
        self.assertEqual(self.client.put(f'/api/modules/forms/{record}', headers=MEMBER, json=modern).status_code, 409)

    def test_concurrent_edits_apply_once(self):
        record = str(uuid4())
        self.put(record, self.body())
        bodies = [{**self.body(version=1), 'title': 'First'}, {**self.body(version=1), 'title': 'Second'}]
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = sorted(pool.map(lambda b: self.put(record, b).status_code, bodies))
        self.assertEqual(statuses, [200, 409])
        self.assertEqual(self.client.get(f'/api/forms/{record}', headers=MEMBER).json()['version'], 2)



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
