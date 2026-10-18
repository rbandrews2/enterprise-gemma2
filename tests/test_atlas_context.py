import json
import tempfile
import unittest
from pathlib import Path

from services.workspace_preview.atlas_context import operational_context
from services.workspace_preview.storage import SQLiteStorage
from services.workspace_preview.intelligence import module_context, GUIDE


class OperationalContextTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.storage = SQLiteStorage(Path(temp.name) / 'facts.sqlite')
        self.user = dict(id='self', organization_id='org', role='member', edition='enterprise')
        with self.storage.connect() as db:
            db.executescript('''
                CREATE TABLE module_records(id TEXT,organization_id TEXT,owner_id TEXT,
                    kind TEXT,version INTEGER,payload TEXT,updated_at TEXT);
                CREATE TABLE form_submissions(organization_id TEXT,form_id TEXT,form_version INTEGER,status TEXT);
                CREATE TABLE dispatch_plans(id TEXT,organization_id TEXT,status TEXT,payload TEXT);
                CREATE TABLE dispatch_assignments(id TEXT,organization_id TEXT,user_id TEXT,
                    plan_id TEXT,status TEXT,starts_at TEXT,ends_at TEXT);
            ''')

    def form(self, ident, org='org', owner='self', version=2):
        with self.storage.connect() as db:
            db.execute('INSERT INTO module_records VALUES(?,?,?,?,?,?,?)',
                (ident, org, owner, 'forms', version, json.dumps({'title': ident * 150,
                 'form_type': 'incident', 'details': 'PRIVATE INCIDENT', 'order_id': 'job'}), ident))

    def assignment(self, ident, org='org', owner='self', status='sent', plan_status='sent', end='2099-01-01T00:00:00+00:00'):
        with self.storage.connect() as db:
            db.execute('INSERT INTO dispatch_plans VALUES(?,?,?,?)', (ident, org, plan_status,
                json.dumps({'delivery_snapshot': {'order_title': ident * 150, 'notes': 'PRIVATE NOTES'}})))
            db.execute('INSERT INTO dispatch_assignments VALUES(?,?,?,?,?,?,?)',
                (ident, org, owner, ident, status, '2098-01-01T00:00:00+00:00', end))

    def facts(self, page='forms', question='Explain my forms', user=None, accounts=True):
        return operational_context(self.storage.connect, user or self.user, page, question, accounts)

    def test_forms_are_own_scoped_bounded_and_current_revision_only(self):
        for ident in 'abcd': self.form(ident)
        self.form('other', owner='another'); self.form('tenant', org='other')
        with self.storage.connect() as db:
            db.execute('INSERT INTO form_submissions VALUES(?,?,?,?)', ('org', 'd', 1, 'accepted'))
            db.execute('INSERT INTO form_submissions VALUES(?,?,?,?)', ('org', 'c', 2, 'submitted'))
        facts = self.facts()
        data = facts['own_saved_forms']
        self.assertEqual(data['total'], 4)
        self.assertEqual(len(data['items']), 3)
        self.assertTrue(data['truncated'])
        self.assertFalse(data['items'][0]['current_version_submitted'])
        self.assertEqual(data['items'][0]['internal_review_status'], 'not_submitted')
        self.assertTrue(data['items'][1]['current_version_submitted'])
        self.assertTrue(all(len(item['title']) <= 120 for item in data['items']))
        self.assertNotIn('PRIVATE INCIDENT', json.dumps(facts))
        self.assertTrue(data['missing_records_are_not_missing_compliance'])
        self.assertEqual(facts['actions_performed'], [])

    def test_dispatch_excludes_other_accounts_cancelled_declined_and_past(self):
        for ident in 'abcd': self.assignment(ident)
        self.assignment('accepted', status='accepted')
        self.assignment('other', owner='someone')
        self.assignment('tenant', org='other')
        self.assignment('cancelled', plan_status='cancelled')
        self.assignment('declined', status='declined')
        self.assignment('past', end='2000-01-01T00:00:00+00:00')
        data = self.facts('schedule', 'My jobs')['upcoming_assignments']
        self.assertEqual(data['total'], 5)
        self.assertEqual(len(data['items']), 3)
        self.assertTrue(data['truncated'])
        self.assertTrue(all(len(item['title']) <= 120 for item in data['items']))
        self.assertNotIn('PRIVATE NOTES', json.dumps(data))
        self.assertTrue(all(item['receipt_confirmation_needed'] == (item['status'] == 'sent')
                            for item in data['items']))
        self.assertTrue(any(item['status'] == 'accepted' for item in data['items']))

    def test_core_and_synthetic_workspaces_do_not_receive_dispatch(self):
        self.assignment('job')
        core = {**self.user, 'edition': 'core'}
        self.assertNotIn('upcoming_assignments', self.facts('schedule', 'assignments', core))
        self.assertNotIn('upcoming_assignments', self.facts('schedule', 'assignments', accounts=False))

    def test_review_aggregates_require_admin_and_selected_org(self):
        with self.storage.connect() as db:
            db.executemany('INSERT INTO form_submissions VALUES(?,?,?,?)',
                [('org', 'a', 1, 'submitted'), ('org', 'b', 1, 'accepted'),
                 ('other', 'c', 1, 'submitted')])
        self.assertNotIn('organization_form_review_counts', self.facts(question='pending review'))
        admin = {**self.user, 'role': 'admin'}
        self.assertEqual(self.facts(question='pending review', user=admin)['organization_form_review_counts'],
                         {'accepted': 1, 'submitted': 1})
        self.assertNotIn('organization_form_review_counts', self.facts(question='my forms', user=admin))

    def test_empty_and_irrelevant_context_is_explicit(self):
        facts = self.facts()
        self.assertEqual(facts['own_saved_forms']['total'], 0)
        self.assertFalse(facts['records_are_complete'])
        self.assertNotIn('own_saved_forms', self.facts('training', 'Explain study status'))

    def test_guidance_describes_implemented_functions_without_autonomous_claims(self):
        self.assertIn('submit assessments', module_context('training', 'member')['guidance'])
        self.assertIn('not issue a certificate', module_context('training', 'admin')['guidance'])
        self.assertIn('join inside WZOS', module_context('messages', 'member')['guidance'])
        self.assertIn('members cannot compose organization SMS', module_context('messages', 'member')['guidance'])
        self.assertIn('Send text notification', module_context('messages', 'admin')['guidance'])
        self.assertIn('Send to office', module_context('forms', 'member')['guidance'])
        self.assertIn('Start navigation in Google Maps', module_context('navigation', 'member')['guidance'])
        self.assertIn('private PDF', module_context('report', 'admin')['guidance'])
        self.assertIn('Do not infer compliance from record counts', GUIDE)
        self.assertFalse(module_context('training', 'admin')['autonomous_actions_enabled'])

    def test_cross_page_questions_receive_current_time_and_meeting_help(self):
        from services.workspace_preview.intelligence import related_module_context
        time_help = related_module_context('Can you correct my timesheet?', 'forms', 'member', 'core')
        self.assertEqual([item['module'] for item in time_help], ['time_clock'])
        meeting_help = related_module_context('How do I join a video meeting?', 'forms', 'member', 'enterprise')
        self.assertEqual([item['module'] for item in meeting_help], ['messages'])
        self.assertIn('Members cannot create meetings', meeting_help[0]['guidance'])
        self.assertFalse(meeting_help[0]['autonomous_actions_enabled'])
