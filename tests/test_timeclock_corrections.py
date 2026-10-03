import csv
import io
import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from services.v2.knowledge.store import Store
from services.workspace_preview.app import create_app

MEMBER, ADMIN = {'X-Preview-Actor': 'core-general'}, {'X-Preview-Actor': 'core-admin'}
OTHER_ADMIN, OTHER_MEMBER = {'X-Preview-Actor': 'enterprise-admin'}, {'X-Preview-Actor': 'enterprise-general'}
NOW = '2026-09-22T18:00:00+00:00'


def times(clock_in='2026-09-22T08:00:00Z', clock_out='2026-09-22T12:00:00Z', breaks=(), segments=None, **extra):
    segments = [{'task': 'job_site', 'start': clock_in, 'end': clock_out}] if segments is None else segments
    return {'request_id': str(uuid4()), 'reason': 'Crew lead confirmed start time', 'clock_in': clock_in,
            'clock_out': clock_out, 'breaks': list(breaks), 'segments': segments, **extra}


class TimeClockCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'WZOS_WORKSPACE_PREVIEW': '1', 'K_SERVICE': '', 'GAE_ENV': '', 'NETLIFY': ''})
        self.env.start()
        self.db = Path(self.temp.name) / 'db.sqlite'
        self.client = self.make_client()
        self.now = patch('services.workspace_preview.timeclock.utc_now', return_value=NOW)
        self.now.start()

    def make_client(self):
        client = TestClient(create_app(self.db, Store(Path(self.temp.name) / 'sources', {})))
        client.__enter__()
        return client

    def tearDown(self):
        self.now.stop()
        self.client.__exit__(None, None, None)
        self.env.stop()
        self.temp.cleanup()

    def at(self, moment):
        self.now.stop()
        self.now = patch('services.workspace_preview.timeclock.utc_now', return_value=moment)
        self.now.start()

    def clock(self, action, state=None, headers=MEMBER, at=None, **extra):
        if at:
            self.at(at)
        body = {'request_id': str(uuid4()), 'action': action, **extra}
        if state:
            body.update(shift_id=state['id'], expected_version=state['version'])
        response = self.client.post('/api/time/commands', headers=headers, json=body)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['entry']

    def closed_shift(self):
        state = self.clock('clock_in', at='2026-09-22T08:05:00+00:00')
        state = self.clock('clock_out', state, at='2026-09-22T12:00:00+00:00')
        self.at(NOW)
        return state

    def correct(self, state, body=None, headers=ADMIN, **extra):
        body = body or times(**extra)
        body.setdefault('expected_version', state['version'])
        return self.client.post(f"/api/time/entries/{state['id']}/corrections", headers=headers, json=body)

    def test_admin_correction_is_audited_and_visible_to_member(self):
        state = self.closed_shift()
        body = times(clock_in='2026-09-22T07:30:00-04:00', clock_out='2026-09-22T12:00:00Z',
                     breaks=[{'start': '2026-09-22T10:00:00Z', 'end': '2026-09-22T10:30:00Z'}],
                     segments=[{'task': 'setup', 'start': '2026-09-22T11:30:00Z', 'end': '2026-09-22T10:00:00+00:00'}])
        self.assertEqual(self.correct(state, body).status_code, 422)  # segment ends before it starts
        body = times(clock_in='2026-09-22T07:30:00Z', clock_out='2026-09-22T12:00:00Z',
                     breaks=[{'start': '2026-09-22T10:00:00Z', 'end': '2026-09-22T10:30:00Z'}],
                     segments=[{'task': 'setup', 'start': '2026-09-22T07:30:00Z', 'end': '2026-09-22T10:00:00Z'},
                               {'task': 'travel', 'start': '2026-09-22T10:30:00Z', 'end': '2026-09-22T12:00:00Z'}])
        response = self.correct(state, body)
        self.assertEqual(response.status_code, 200, response.text)
        entry = response.json()['entry']
        self.assertEqual((entry['version'], entry['record_basis'], entry['correction_count']), (3, 'admin_corrected', 1))
        self.assertEqual((entry['work_seconds'], entry['break_seconds'], entry['task']), (14400, 1800, 'travel'))
        self.assertFalse(entry['payroll_calculated'])
        detail = self.client.get(f"/api/time/entries/{state['id']}", headers=MEMBER).json()
        [audit] = detail['corrections']
        self.assertEqual((audit['admin_id'], audit['admin_name'], audit['reason']), ('core-admin', 'Jordan Lee', body['reason']))
        self.assertEqual(audit['before']['clock_in'], '2026-09-22T08:05:00+00:00')
        self.assertEqual(audit['after']['clock_in'], '2026-09-22T07:30:00+00:00')
        self.assertEqual([r['action'] for r in detail['receipts']], ['clock_in', 'clock_out'])
        self.assertTrue(all(r['basis'] == 'server_receipt' for r in detail['receipts']))
        # Replay is idempotent; reusing the ID for different times is refused.
        self.assertEqual(self.correct(state, dict(body)).json(), response.json())
        self.assertEqual(self.correct(state, {**body, 'reason': 'Different correction reason'}).status_code, 409)
        self.assertEqual(len(self.client.get(f"/api/time/entries/{state['id']}", headers=ADMIN).json()['corrections']), 1)
        # A stale version is refused.
        self.assertEqual(self.correct(state, times()).status_code, 409)

    def test_correction_validation(self):
        state = self.closed_shift()
        cases = [
            times(clock_in='2026-09-22T12:00:00Z', clock_out='2026-09-22T08:00:00Z'),
            times(clock_out='2026-09-22T19:00:00Z'),  # future relative to NOW
            times(clock_in='2026-09-20T08:00:00Z'),  # longer than 48 hours
            times(clock_in='2026-09-22T08:00:00', clock_out='2026-09-22T12:00:00'),  # no timezone
            times(breaks=[{'start': '2026-09-22T09:00:00Z', 'end': '2026-09-22T09:30:00Z'},
                          {'start': '2026-09-22T09:15:00Z', 'end': '2026-09-22T09:45:00Z'}]),
            times(segments=[{'task': 'setup', 'start': '2026-09-22T07:00:00Z', 'end': '2026-09-22T09:00:00Z'}]),
            times(breaks=[{'start': '2026-09-22T09:00:00Z', 'end': '2026-09-22T09:30:00Z'}]),  # segment covers break
            times(segments=[]),
            times(segments=[{'task': 'lunch', 'start': '2026-09-22T08:00:00Z', 'end': '2026-09-22T12:00:00Z'}]),
            {**times(), 'employee_id': 'core-admin'},
            {**times(), 'reason': ''},
        ]
        for body in cases:
            with self.subTest(body=body):
                self.assertEqual(self.correct(state, body).status_code, 422)
        self.assertEqual(self.client.get(f"/api/time/entries/{state['id']}", headers=ADMIN).json()['corrections'], [])

    def test_member_permissions_and_organization_isolation(self):
        state = self.closed_shift()
        self.assertEqual(self.correct(state, headers=MEMBER).status_code, 403)
        self.assertEqual(self.client.post('/api/time/entries', headers=MEMBER, json={**times(), 'employee_id': 'core-general'}).status_code, 403)
        self.assertEqual(self.client.get('/api/time/entries?employee_id=core-admin', headers=MEMBER).status_code, 403)
        self.assertEqual(self.client.get('/api/time/export?employee_id=core-admin', headers=MEMBER).status_code, 403)
        self.assertEqual(self.client.get('/api/time/offline-submissions?team=true', headers=MEMBER).status_code, 403)
        self.assertEqual([m['id'] for m in self.client.get('/api/time/members', headers=MEMBER).json()['items']], ['core-general'])
        admin_shift = self.clock('clock_in', headers=ADMIN)
        self.assertEqual(self.client.get(f"/api/time/entries/{admin_shift['id']}", headers=MEMBER).status_code, 404)
        # Another organization's admin cannot see, correct or create records here.
        self.assertEqual(self.client.get(f"/api/time/entries/{state['id']}", headers=OTHER_ADMIN).status_code, 404)
        self.assertEqual(self.correct(state, headers=OTHER_ADMIN).status_code, 404)
        self.assertEqual(self.client.post('/api/time/entries', headers=OTHER_ADMIN, json={**times(), 'employee_id': 'core-general'}).status_code, 404)
        self.assertEqual(self.client.get('/api/time/entries?team=true&employee_id=core-general', headers=OTHER_ADMIN).json()['total'], 0)
        self.assertEqual({m['id'] for m in self.client.get('/api/time/members', headers=OTHER_ADMIN).json()['items']},
                         {'enterprise-admin', 'enterprise-general'})
        self.assertNotIn('core-general', self.client.get('/api/time/export?team=true', headers=OTHER_ADMIN).text)
        self.assertEqual(self.client.get(f"/api/time/entries/{state['id']}", headers=OTHER_MEMBER).status_code, 404)

    def test_correcting_active_shift_closes_it_and_member_must_refresh(self):
        state = self.clock('clock_in', at='2026-09-22T08:00:00+00:00')
        self.at(NOW)
        response = self.correct(state, clock_in='2026-09-22T08:00:00Z', clock_out='2026-09-22T16:00:00Z')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['entry']['status'], 'closed')
        self.assertIsNone(self.client.get('/api/time/status', headers=MEMBER).json()['active'])
        stale = self.client.post('/api/time/commands', headers=MEMBER, json={'request_id': str(uuid4()), 'action': 'clock_out', 'shift_id': state['id'], 'expected_version': 1})
        self.assertEqual(stale.status_code, 409)
        self.clock('clock_in', at='2026-09-22T18:00:00+00:00')
        # Corrections and manual entries cannot overlap another shift, including the active one.
        self.assertEqual(self.correct(response.json()['entry'], clock_in='2026-09-22T08:00:00Z', clock_out='2026-09-22T18:00:30Z').status_code, 409)

    def test_manual_entry_and_overlap_protection(self):
        self.closed_shift()
        overlapping = {**times(clock_in='2026-09-22T11:00:00Z', clock_out='2026-09-22T13:00:00Z'), 'employee_id': 'core-general'}
        self.assertEqual(self.client.post('/api/time/entries', headers=ADMIN, json=overlapping).status_code, 409)
        body = {**times(clock_in='2026-09-21T08:00:00Z', clock_out='2026-09-21T16:00:00Z'), 'employee_id': 'core-general', 'order_id': 'core-sample'}
        response = self.client.post('/api/time/entries', headers=ADMIN, json=body)
        self.assertEqual(response.status_code, 200, response.text)
        entry = response.json()['entry']
        self.assertEqual((entry['record_basis'], entry['version'], entry['status']), ('admin_entered', 1, 'closed'))
        self.assertIsNotNone(entry['order_title'])
        self.assertEqual(self.client.post('/api/time/entries', headers=ADMIN, json=body).json(), response.json())
        detail = self.client.get(f"/api/time/entries/{entry['id']}", headers=MEMBER).json()
        self.assertEqual((detail['corrections'][0]['kind'], detail['corrections'][0]['before']), ('manual_entry', None))
        self.assertEqual(detail['receipts'], [])
        unknown = {**times(clock_in='2026-09-20T08:00:00Z', clock_out='2026-09-20T09:00:00Z'), 'employee_id': 'nobody'}
        self.assertEqual(self.client.post('/api/time/entries', headers=ADMIN, json=unknown).status_code, 404)
        other_order = {**times(clock_in='2026-09-20T08:00:00Z', clock_out='2026-09-20T09:00:00Z'), 'employee_id': 'core-general', 'order_id': 'enterprise-sample'}
        self.assertEqual(self.client.post('/api/time/entries', headers=ADMIN, json=other_order).status_code, 404)
        self.assertEqual(self.client.get('/api/time/entries', headers=MEMBER).json()['total'], 2)

    def test_concurrent_corrections_apply_once(self):
        state = self.closed_shift()
        bodies = [times(clock_in='2026-09-22T07:00:00Z'), times(clock_in='2026-09-22T07:15:00Z')]
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = sorted(pool.map(lambda b: self.correct(state, b).status_code, bodies))
        self.assertEqual(statuses, [200, 409])
        self.assertEqual(len(self.client.get(f"/api/time/entries/{state['id']}", headers=ADMIN).json()['corrections']), 1)

    def drafts(self, *items, submitted='2026-09-22T17:50:00Z'):
        return {'device_submitted_at': submitted, 'drafts': [
            {'request_id': str(uuid4()), 'captured_at': '2026-09-22T17:40:00Z', **item} for item in items]}

    def test_offline_submissions_never_change_attendance(self):
        state = self.clock('clock_in', at='2026-09-22T08:00:00+00:00')
        self.at(NOW)
        batch = self.drafts({'action': 'clock_out', 'stated_at': '2026-09-22T16:30:00Z', 'note': 'Signal lost at site',
                             'known_shift_id': state['id'], 'known_version': 1},
                            submitted='2026-09-22T17:50:00Z')  # device clock 10 minutes behind the server
        response = self.client.post('/api/time/offline-submissions', headers=MEMBER, json=batch)
        self.assertEqual(response.status_code, 200, response.text)
        [item] = response.json()['items']
        self.assertFalse(response.json()['attendance_changed'])
        self.assertEqual((item['status'], item['time_basis'], item['device_offset_seconds']), ('pending', 'device_estimate_unverified', 600))
        self.assertEqual(item['estimated_at'], '2026-09-22T16:40:00+00:00')
        self.assertEqual(self.client.get('/api/time/status', headers=MEMBER).json()['active']['version'], 1)
        # Replaying the same batch returns the original receipt; changing the content under the same ID is refused.
        self.assertEqual(self.client.post('/api/time/offline-submissions', headers=MEMBER, json={**batch, 'device_submitted_at': '2026-09-22T17:55:00Z'}).json()['items'][0]['id'], item['id'])
        changed = {**batch, 'drafts': [{**batch['drafts'][0], 'note': 'changed'}]}
        self.assertEqual(self.client.post('/api/time/offline-submissions', headers=MEMBER, json=changed).status_code, 409)
        self.assertEqual(self.client.post('/api/time/offline-submissions', headers=MEMBER, json=self.drafts({'action': 'clock_in', 'captured_at': '2026-09-22T17:59:00Z'}, submitted='2026-09-22T17:50:00Z')).status_code, 422)
        self.assertEqual(self.client.post('/api/time/offline-submissions', headers=MEMBER, json=self.drafts({'action': 'clock_in', 'captured_at': '2026-09-01T08:00:00Z'})).status_code, 422)
        self.assertEqual(self.client.post('/api/time/offline-submissions', headers=MEMBER, json=self.drafts({'action': 'clock_in', 'stated_at': '2026-09-22T17:45:00Z'})).status_code, 422)
        self.assertEqual(self.client.post('/api/time/offline-submissions', headers=MEMBER, json=self.drafts({'action': 'clock_in', 'order_id': 'enterprise-sample'})).status_code, 404)
        self.assertEqual(self.client.post('/api/time/offline-submissions', headers=MEMBER, json=self.drafts({'action': 'clock_in', 'captured_at': '2026-09-22T17:40:00'})).status_code, 422)
        self.assertEqual(len(self.client.get('/api/time/offline-submissions', headers=MEMBER).json()['items']), 1)
        self.assertEqual(self.client.get('/api/time/offline-submissions?team=true', headers=OTHER_ADMIN).json()['items'], [])
        # Admin applies the reviewed time by closing the active shift and linking the submission.
        queue = self.client.get('/api/time/offline-submissions?team=true', headers=ADMIN).json()['items']
        self.assertEqual([q['id'] for q in queue], [item['id']])
        reviewed = times(clock_in='2026-09-22T08:00:00Z', clock_out='2026-09-22T16:40:00Z', resolves=[item['id']])
        self.assertEqual(self.correct(state, reviewed, headers=OTHER_ADMIN).status_code, 404)
        applied = self.correct(state, reviewed)
        self.assertEqual(applied.status_code, 200, applied.text)
        self.assertEqual(applied.json()['resolved'], [item['id']])
        mine = self.client.get('/api/time/offline-submissions?status=all', headers=MEMBER).json()['items']
        self.assertEqual((mine[0]['status'], mine[0]['resolved_shift_id']), ('applied', state['id']))
        detail = self.client.get(f"/api/time/entries/{state['id']}", headers=MEMBER).json()
        self.assertEqual(detail['entry']['record_basis'], 'admin_corrected')
        self.assertEqual(detail['offline_submissions'][0]['id'], item['id'])
        # An applied submission cannot be applied or rejected again.
        again = times(clock_in='2026-09-21T08:00:00Z', clock_out='2026-09-21T09:00:00Z', employee_id='core-general', resolves=[item['id']])
        self.assertEqual(self.client.post('/api/time/entries', headers=ADMIN, json=again).status_code, 409)
        self.assertEqual(self.client.post(f"/api/time/offline-submissions/{item['id']}/resolve", headers=ADMIN, json={'decision': 'rejected', 'reason': 'Not valid'}).status_code, 409)

    def test_duplicate_hint_and_resolution(self):
        self.clock('clock_in', at='2026-09-22T17:30:00+00:00')
        self.at(NOW)
        batch = self.drafts({'action': 'clock_in', 'captured_at': '2026-09-22T17:35:00Z'}, submitted='2026-09-22T17:59:00Z')
        item = self.client.post('/api/time/offline-submissions', headers=MEMBER, json=batch).json()['items'][0]
        queue = self.client.get('/api/time/offline-submissions?team=true', headers=ADMIN).json()['items']
        self.assertEqual(queue[0]['possible_duplicates'][0]['kind'], 'server_receipt')
        path = f"/api/time/offline-submissions/{item['id']}/resolve"
        self.assertEqual(self.client.post(path, headers=MEMBER, json={'decision': 'duplicate', 'reason': 'Already recorded'}).status_code, 403)
        self.assertEqual(self.client.post(path, headers=OTHER_ADMIN, json={'decision': 'duplicate', 'reason': 'Already recorded'}).status_code, 404)
        self.assertEqual(self.client.post(path, headers=ADMIN, json={'decision': 'approved', 'reason': 'Already recorded'}).status_code, 422)
        first = self.client.post(path, headers=ADMIN, json={'decision': 'duplicate', 'reason': 'Already recorded'})
        self.assertEqual(first.json()['item']['status'], 'duplicate')
        self.assertEqual(self.client.post(path, headers=ADMIN, json={'decision': 'duplicate', 'reason': 'Already recorded'}).json()['item'], first.json()['item'])
        self.assertEqual(self.client.post(path, headers=ADMIN, json={'decision': 'rejected', 'reason': 'Changed mind'}).status_code, 409)
        self.assertEqual(self.client.get('/api/time/offline-submissions?team=true', headers=ADMIN).json()['items'], [])
        self.assertEqual(self.client.get('/api/time/entries', headers=MEMBER).json()['total'], 1)

    def test_export_filters_basis_and_intervals(self):
        state = self.closed_shift()
        self.correct(state, clock_in='2026-09-22T07:00:00Z')
        self.client.post('/api/time/entries', headers=ADMIN, json={**times(clock_in='2026-09-20T08:00:00Z', clock_out='2026-09-20T09:00:00Z'), 'employee_id': 'core-admin'})
        rows = list(csv.reader(io.StringIO(self.client.get('/api/time/export?team=true', headers=ADMIN).text)))
        self.assertEqual(rows[0][:2] + rows[0][-3:], ['Employee ID', 'Employee', 'Record basis', 'Corrections', 'Payroll calculated'])
        self.assertEqual([(r[0], r[1], r[8], r[9]) for r in rows[1:]],
                         [('core-admin', 'Jordan Lee', 'admin_entered', '0'), ('core-general', 'Casey Morgan', 'admin_corrected', '1')])
        filtered = self.client.get('/api/time/export?team=true&start_date=2026-09-21&end_date=2026-09-22&employee_id=core-general', headers=ADMIN)
        self.assertIn('2026-09-21-to-2026-09-22', filtered.headers['content-disposition'])
        self.assertEqual(len(list(csv.reader(io.StringIO(filtered.text)))), 2)
        intervals = list(csv.reader(io.StringIO(self.client.get('/api/time/export?detail=intervals', headers=MEMBER).text)))
        self.assertEqual(intervals[1][4:9], ['Task', 'Job Site', '2026-09-22T07:00:00+00:00', '2026-09-22T12:00:00+00:00', '18000'])
        self.assertEqual(self.client.get('/api/time/export?start_date=2026-09-23&end_date=2026-09-22', headers=MEMBER).status_code, 422)

    def test_export_limit_and_formula_safety(self):
        with closing(sqlite3.connect(self.db)) as conn, conn:
            for n in range(1001):
                payload = {'clock_in': f'2026-01-01T00:00:{n % 60:02d}+00:00', 'clock_out': None, 'task': 'other', 'order_id': None,
                           'order_title': '=HYPERLINK("x")', 'note': '', 'breaks': [], 'segments': []}
                conn.execute('INSERT INTO preview_shifts VALUES (?,?,?,?,?,?)', (str(uuid4()), 'core-demo', 'core-general', 1, 0, json.dumps(payload)))
        self.assertEqual(self.client.get('/api/time/export', headers=MEMBER).status_code, 422)
        safe = self.client.get('/api/time/export?employee_id=core-general&team=true&start_date=2026-01-01&end_date=2026-01-01', headers=ADMIN)
        self.assertEqual(safe.status_code, 422)
        with closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute("DELETE FROM preview_shifts WHERE rowid IN (SELECT rowid FROM preview_shifts LIMIT 1000)")
        text = self.client.get('/api/time/export', headers=MEMBER).text
        self.assertIn("'=HYPERLINK", text)

    def test_audit_and_submissions_persist_across_restart(self):
        state = self.closed_shift()
        self.correct(state, clock_in='2026-09-22T07:00:00Z')
        self.client.post('/api/time/offline-submissions', headers=MEMBER, json=self.drafts({'action': 'break_start'}))
        second = self.make_client()
        try:
            self.assertEqual(len(second.get(f"/api/time/entries/{state['id']}", headers=MEMBER).json()['corrections']), 1)
            self.assertEqual(len(second.get('/api/time/offline-submissions?team=true', headers=ADMIN).json()['items']), 1)
        finally:
            second.__exit__(None, None, None)


if __name__ == '__main__':
    unittest.main()
