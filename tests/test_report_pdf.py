import hashlib
import json
import os
import unittest
from io import BytesIO
from unittest.mock import patch
from uuid import uuid4

from pypdf import PdfReader
from tests import test_form_submissions as fixtures


class ReportPdfTests(unittest.TestCase):
    setUp = fixtures.FormSubmissionTests.setUp
    make_storage = fixtures.FormSubmissionTests.make_storage
    h = fixtures.FormSubmissionTests.h

    def save(self, packet=None):
        sid = str(uuid4())
        body = {'request_id': sid, 'expected_order_version': 1}
        if packet:
            with patch('services.workspace_preview.report_history.prepare_order', return_value=packet):
                result = self.client.post('/api/orders/enterprise-sample/reports', headers=self.h(), json=body)
        else:
            result = self.client.post('/api/orders/enterprise-sample/reports', headers=self.h(), json=body)
        self.assertEqual(result.status_code, 200, result.text)
        return '/api/orders/enterprise-sample/reports/' + sid, result.json()

    def test_private_snapshot_download_and_immutable_bytes(self):
        path, saved = self.save()
        self.assertEqual(self.client.get(path + '/pdf').status_code, 401)
        self.assertEqual(self.client.get(path + '/pdf', headers=self.h('core-admin')).status_code, 403)
        self.assertEqual(self.client.get(path + '/pdf', headers=self.h('enterprise-admin')).status_code, 404)
        self.assertEqual(self.client.get(path.replace('enterprise-sample', 'core-sample') + '/pdf', headers=self.h()).status_code, 404)
        first = self.client.get(path + '/pdf', headers=self.h())
        self.assertEqual(first.status_code, 200, first.text[:100] if first.status_code != 200 else '')
        self.assertEqual(first.headers['content-type'], 'application/pdf')
        self.assertIn('no-store', first.headers['cache-control'])
        self.assertEqual(first.headers['x-wzos-snapshot-sha256'], saved['sha256'])
        self.assertEqual(first.headers['x-wzos-basis-changed'], 'false')
        pdf = PdfReader(BytesIO(first.content))
        text = '\n'.join(p.extract_text() for p in pdf.pages)
        self.assertIn('NOT APPROVED FOR FIELD USE', text)
        self.assertIn(saved['sha256'], text)
        order = self.client.get('/api/orders/enterprise-sample', headers=self.h()).json()
        payload = {k: order[k] for k in ('title', 'work_type', 'address', 'locality', 'work_date', 'notes')}
        payload.update(expected_version=1, notes='Later content must not change this PDF')
        self.assertEqual(self.client.put('/api/orders/enterprise-sample', headers=self.h(), json=payload).status_code, 200)
        second = self.client.get(path + '/pdf', headers=self.h())
        self.assertEqual(second.headers['x-wzos-basis-changed'], 'true')
        self.assertEqual(first.content, second.content)

    def test_citations_and_literal_content_survive_multipage_render(self):
        packet = {'note': 'Synthetic reference preparation', 'references': {'topics': [{
            'id': 'traffic_control', 'candidates': [{
                'title': 'Synthetic official manual', 'agency': 'VDOT', 'edition': 'Synthetic edition',
                'page': 17, 'section': 'Warning signs', 'revision': 'a' * 64,
                'review_status': 'unreviewed', 'publication_status': 'superseded', 'is_latest': False,
                'url': 'https://www.virginiadot.org/manual#page=17',
                'text': ('<img src="https://example.test/image"> Café & crew: review this source. ' * 130),
            }]}], 'coverage_gaps': ['Locality rules are not reviewed']}}
        path, _ = self.save(packet)
        result = self.client.get(path + '/pdf', headers=self.h())
        self.assertEqual(result.status_code, 200)
        pdf = PdfReader(BytesIO(result.content))
        self.assertGreater(len(pdf.pages), 2)
        text = '\n'.join(p.extract_text() for p in pdf.pages)
        for item in ('VDOT', 'Synthetic edition', 'page: 17', 'unreviewed', 'superseded',
                     'a' * 64, '<img src=', 'Café', 'Locality rules are not reviewed'):
            self.assertIn(item, text)
        links = [a.get_object()['/A']['/URI'] for p in pdf.pages for a in p.get('/Annots', [])
                 if a.get_object().get('/A', {}).get('/S') == '/URI']
        self.assertEqual(links, ['https://www.virginiadot.org/manual#page=17'])
        self.assertIn('Page ' + str(len(pdf.pages)), pdf.pages[-1].extract_text())

    def test_tampered_and_oversize_snapshots_refuse_export(self):
        path, saved = self.save()
        with self.storage.connect() as db:
            db.execute("UPDATE report_snapshots SET payload=payload || ' ' WHERE id=?", (saved['id'],))
        self.assertEqual(self.client.get(path + '/pdf', headers=self.h()).status_code, 409)
        path, saved = self.save()
        with self.storage.connect() as db:
            row = db.execute('SELECT payload FROM report_snapshots WHERE id=?', (saved['id'],)).fetchone()
            payload = json.loads(row['payload'])
            payload['order']['notes'] = 'x' * (2 * 1024 * 1024)
            packed = json.dumps(payload)
            db.execute('UPDATE report_snapshots SET payload=?,sha256=? WHERE id=?',
                       (packed, hashlib.sha256(packed.encode()).hexdigest(), saved['id']))
        self.assertEqual(self.client.get(path + '/pdf', headers=self.h()).status_code, 413)


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'), 'Dedicated PostgreSQL database not configured')
class PostgreSQLReportPdfTests(ReportPdfTests):
    make_storage = fixtures.PostgreSQLFormSubmissionTests.make_storage
