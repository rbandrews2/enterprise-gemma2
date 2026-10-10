import os, re, tempfile, unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.workspace_preview.storage import SQLiteStorage
from services.workspace_preview.files import LocalFiles
from services.v2.knowledge.store import Store
from tests.test_messaging import FakeProvider

JOB_DAY = date.today() + timedelta(days=10)
START = datetime(JOB_DAY.year, JOB_DAY.month, JOB_DAY.day, 12, tzinfo=timezone.utc)
END = START + timedelta(hours=8)
PHONE = '+15550100001'


def window(start=START - timedelta(hours=2), end=END + timedelta(hours=2), status='available'):
    return {'starts_at': start.isoformat(), 'ends_at': end.isoformat(), 'status': status}


class DispatchTests(unittest.TestCase):
    def make_storage(self, root):
        return SQLiteStorage(root / 'dispatch.sqlite')

    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup); root = Path(temp.name)
        env = patch.dict(os.environ, {'WZOS_ACCOUNT_WORKSPACE': '1', 'WZOS_SMS_MODE': 'test', 'WZOS_SMS_TEST_RECIPIENTS': PHONE,
                                      'WZOS_TWILIO_AUTH_TOKEN': 'synthetic', 'WZOS_PUBLIC_BASE_URL': 'https://wzos.test'})
        env.start(); self.addCleanup(env.stop)
        users = ['admin', 'member', 'other', 'crew3', 'coreadmin', 'rival']
        self.claims = {u: {'uid': u, 'email': u + '@example.test', 'email_verified': True, 'name': u.title()} for u in users}
        self.app = create_app(root / 'unused', Store(root / 'sources', {}), account_workspace=True, storage=self.make_storage(root),
                              verifier=lambda token: self.claims[token], file_store=LocalFiles(root / 'files'))
        self.provider = FakeProvider(); self.app.state.sms_provider = self.provider
        self.client = TestClient(self.app); self.addCleanup(self.client.close)
        accounts = self.app.state.accounts
        self.org = self.organization('admin', 'enterprise', ['member', 'other', 'crew3'])
        self.core = self.organization('coreadmin', 'core', [])
        self.rival = self.organization('rival', 'enterprise', [])
        self.order = self.client.post('/api/orders', headers=self.h(), json={'request_id': str(uuid4()), 'title': 'Granby Street markings', 'work_type': 'line_striping', 'address': 'Granby Street, Norfolk, VA', 'locality': 'Norfolk'}).json()['id']
        self.profile('member', 'EMP-1', [window()]); self.qualify('member', expires=JOB_DAY + timedelta(days=30))
        self.profile('other', 'EMP-2', [window()]); self.qualify('other', expires=JOB_DAY - timedelta(days=1), issued=date.today() - timedelta(days=400))
        self.profile('crew3', 'EMP-3', []); self.qualify('crew3', expires=JOB_DAY + timedelta(days=30))

    def organization(self, owner, edition, members):
        code = self.app.state.accounts.issue_activation(edition)
        org = self.client.post('/api/account/organizations', headers={'Authorization': 'Bearer ' + owner}, json={'name': owner + ' org', 'activation_code': code}).json()['id']
        for person in members:
            token = self.client.post('/api/account/invitations', headers={'Authorization': 'Bearer ' + owner, 'X-WZOS-Organization': org}, json={'email': person + '@example.test'}).json()['token']
            self.client.post('/api/account/join', headers={'Authorization': 'Bearer ' + person}, json={'token': token})
        return org

    def h(self, user='admin', org=None):
        return {'Authorization': 'Bearer ' + user, 'X-WZOS-Organization': org or self.org}

    def profile(self, user, number, availability, version=0):
        r = self.client.put('/api/account/employees/' + user, headers=self.h(), json={'expected_version': version, 'employee_number': number, 'address': 'Private home address', 'phone': '+15559990000', 'availability': availability})
        self.assertEqual(r.status_code, 200, r.text); return r.json()

    def qualify(self, user, expires, issued=None, status='verified', version=0, qid='flagger'):
        body = {'expected_version': version, 'title': 'Flagger certification', 'issuer': 'Synthetic issuer', 'issued_on': (issued or date.today() - timedelta(days=30)).isoformat(),
                'expires_on': expires.isoformat() if expires else None, 'review_status': status, 'evidence_reference': 'synthetic-card-1' if status == 'verified' else '', 'review_note': 'Checked synthetic card' if status != 'unreviewed' else ''}
        r = self.client.put(f'/api/account/employees/{user}/qualifications/{qid}', headers=self.h(), json=body)
        self.assertEqual(r.status_code, 200, r.text); return r.json()

    def requirements(self, order=None, version=0, count=1, **change):
        body = {'expected_version': version, 'starts_at': START.isoformat(), 'ends_at': END.isoformat(), 'roles': [{'id': 'flagger', 'title': 'Flagger', 'count': count, 'qualification_ids': ['flagger']}], **change}
        return self.client.put(f'/api/dispatch/orders/{order or self.order}/requirements', headers=self.h(), json=body)

    def propose(self, order=None):
        r = self.client.post(f'/api/dispatch/orders/{order or self.order}/proposals', headers=self.h()); self.assertEqual(r.status_code, 200, r.text); return r.json()

    def approve(self, plan, request_id=None):
        return self.client.post(f"/api/dispatch/plans/{plan['id']}/approve", headers=self.h(), json={'request_id': request_id or str(uuid4()), 'expected_version': plan['version']})

    def inbox(self, user):
        return [m['body'] for m in self.client.get('/api/messages', headers=self.h(user)).json()['items']]

    def test_enterprise_admin_only(self):
        self.assertEqual(self.client.get(f'/api/dispatch/orders/{self.order}', headers=self.h('coreadmin', self.core)).status_code, 403)
        self.assertEqual(self.client.get('/api/dispatch/my-assignments', headers=self.h('coreadmin', self.core)).status_code, 403)
        self.assertEqual(self.client.get(f'/api/dispatch/orders/{self.order}', headers=self.h('member')).status_code, 403)
        self.assertEqual(self.requirements().status_code, 200)
        self.assertEqual(self.client.post(f'/api/dispatch/orders/{self.order}/proposals', headers=self.h('member')).status_code, 403)
        self.assertEqual(self.client.get('/api/dispatch/my-assignments', headers=self.h('member')).json()['items'], [])
        self.assertEqual(self.client.get(f'/api/dispatch/orders/{self.order}', headers=self.h('rival', self.rival)).status_code, 404)

    def test_requirements_validation_and_versions(self):
        self.assertEqual(self.requirements(starts_at='2026-12-01T08:00:00').status_code, 422)
        self.assertEqual(self.requirements(ends_at=START.isoformat()).status_code, 422)
        self.assertEqual(self.requirements(roles=[{'id': 'a', 'title': 'A', 'count': 1}, {'id': 'a', 'title': 'B', 'count': 1}]).status_code, 422)
        first = self.requirements(); self.assertEqual(first.json()['version'], 1)
        self.assertEqual(self.requirements().json()['version'], 1)
        self.assertEqual(self.requirements(notes='changed').status_code, 409)
        self.assertEqual(self.requirements(version=1, notes='changed').json()['version'], 2)

    def test_proposal_uses_verified_facts_and_explains_exclusions(self):
        self.requirements(count=2)
        plan = self.propose()
        self.assertEqual([a['user_id'] for a in plan['assignments']], ['member'])
        self.assertEqual(plan['unfilled'], [{'role_id': 'flagger', 'title': 'Flagger', 'missing': 1}])
        reasons = {c['user_id']: c for c in plan['candidates']['flagger']}
        self.assertIn('qualification_expired', reasons['other']['blockers'])
        self.assertIn('qualification_missing', reasons['admin']['blockers'])
        self.assertEqual(reasons['crew3']['blockers'], []); self.assertEqual(reasons['crew3']['warnings'], ['availability_unknown'])
        self.assertFalse(reasons['crew3']['eligible'])
        text = str(plan)
        for private in ('Private home address', '+15559990000', 'synthetic-card-1'):
            self.assertNotIn(private, text)

    def test_unreviewed_and_unknown_expiry_states_are_preserved(self):
        self.qualify('crew3', None, status='unreviewed', version=1)
        self.qualify('member', None, version=1)
        self.requirements(); plan = self.propose()
        reasons = {c['user_id']: c for c in plan['candidates']['flagger']}
        self.assertIn('qualification_unreviewed', reasons['crew3']['blockers'])
        self.assertEqual(reasons['member']['warnings'], ['qualification_expiry_unknown']); self.assertEqual(plan['assignments'], [])

    def test_admin_edits_require_justified_overrides_and_never_bypass_hard_blocks(self):
        self.requirements(count=2); plan = self.propose()
        url = f"/api/dispatch/plans/{plan['id']}"
        edit = lambda picks, version=1: self.client.put(url, headers=self.h(), json={'expected_version': version, 'assignments': picks})
        self.assertEqual(edit([{'role_id': 'flagger', 'user_id': 'other', 'override_reason': 'Card renewed yesterday, trust me'}]).status_code, 422)
        self.assertEqual(edit([{'role_id': 'flagger', 'user_id': 'crew3'}]).status_code, 422)
        self.assertEqual(edit([{'role_id': 'flagger', 'user_id': 'member'}, {'role_id': 'flagger', 'user_id': 'member'}]).status_code, 422)
        self.assertEqual(edit([{'role_id': 'other_role', 'user_id': 'member'}]).status_code, 422)
        ok = edit([{'role_id': 'flagger', 'user_id': 'member'}, {'role_id': 'flagger', 'user_id': 'crew3', 'override_reason': 'Confirmed by phone he is free all day'}])
        self.assertEqual(ok.status_code, 200, ok.text); self.assertEqual(ok.json()['version'], 2); self.assertEqual(ok.json()['unfilled'], [])
        self.assertEqual(edit([{'role_id': 'flagger', 'user_id': 'member'}]).status_code, 409)
        self.assertEqual(edit([{'role_id': 'flagger', 'user_id': 'member'}, {'role_id': 'flagger', 'user_id': 'crew3'}, {'role_id': 'flagger', 'user_id': 'admin'}], 2).status_code, 422)

    def test_approval_sends_once_and_member_responds(self):
        self.requirements(); plan = self.propose(); request_id = str(uuid4())
        sent = self.approve(plan, request_id); self.assertEqual(sent.status_code, 200, sent.text)
        self.assertEqual(sent.json()['status'], 'sent'); self.assertEqual(len(sent.json()['sent_assignments']), 1)
        self.assertEqual(self.approve(plan, request_id).json()['id'], plan['id'])
        self.assertEqual(self.approve(plan).status_code, 409)
        notices = [m for m in self.inbox('member') if m.startswith('New assignment')]
        self.assertEqual(len(notices), 1); self.assertIn('Granby Street, Norfolk, VA', notices[0]); self.assertNotIn('Private home address', notices[0])
        mine = self.client.get('/api/dispatch/my-assignments', headers=self.h('member')).json()['items']
        self.assertEqual((mine[0]['status'], mine[0]['role_title'], mine[0]['order_title']), ('sent', 'Flagger', 'Granby Street markings'))
        url = f"/api/dispatch/assignments/{mine[0]['id']}/respond"
        self.assertEqual(self.client.post(url, headers=self.h('other'), json={'response': 'accepted'}).status_code, 404)
        self.assertEqual(self.client.post(url, headers=self.h('member'), json={'response': 'accepted'}).json()['status'], 'accepted')
        self.assertEqual(self.client.post(url, headers=self.h('member'), json={'response': 'accepted'}).status_code, 200)
        self.assertEqual(self.client.post(url, headers=self.h('member'), json={'response': 'declined'}).status_code, 409)
        received = self.client.get('/api/messages', headers=self.h('member')).json()['items'][0]
        self.assertIsNotNone(received['acknowledged_at'])
        state = self.client.get(f'/api/dispatch/orders/{self.order}', headers=self.h()).json()
        self.assertEqual(state['plans'][0]['sent_assignments'][0]['status'], 'accepted')
        self.assertEqual(self.client.get(f"/api/dispatch/orders/{self.order}/events", headers=self.h()).json()['items'][0]['event'], 'assignment_accepted')

    def test_stale_requirements_or_employee_records_block_approval(self):
        self.requirements(); plan = self.propose()
        self.requirements(version=1, notes='Start moved')
        self.assertEqual(self.approve(plan).status_code, 409)
        plan = self.propose(); self.qualify('member', JOB_DAY + timedelta(days=60), version=1)
        response = self.approve(plan); self.assertEqual(response.status_code, 409); self.assertIn('changed after this proposal', response.json()['detail'])
        self.assertEqual(self.inbox('member'), [])

    def test_overlapping_assignments_and_schedules_conflict(self):
        self.requirements(); self.assertEqual(self.approve(self.propose()).status_code, 200)
        second = self.client.post('/api/orders', headers=self.h(), json={'request_id': str(uuid4()), 'title': 'Second job', 'work_type': 'other', 'address': 'Main Street', 'locality': 'Norfolk'}).json()['id']
        self.requirements(order=second)
        reasons = {c['user_id']: c for c in self.propose(second)['candidates']['flagger']}
        self.assertIn('assignment_conflict', reasons['member']['blockers'])
        schedule = {'request_id': str(uuid4()), 'title': 'Training day', 'assignees': ['crew3'], 'start': START.isoformat(), 'end': END.isoformat()}
        self.assertEqual(self.client.put(f'/api/modules/schedule/{uuid4()}', headers=self.h(), json=schedule).status_code, 200)
        reasons = {c['user_id']: c for c in self.propose(second)['candidates']['flagger']}
        self.assertIn('schedule_conflict', reasons['crew3']['blockers'])

    def test_revision_replaces_previous_assignments_and_notifies_removed_people(self):
        self.requirements(); first = self.approve(self.propose()).json()
        self.assertEqual(first['sent_assignments'][0]['user_id'], 'member')
        self.profile('crew3', 'EMP-3', [window()], version=1)
        revision = self.propose()
        self.assertNotIn('assignment_conflict', {c['user_id']: c for c in revision['candidates']['flagger']}['member']['blockers'])
        edited = self.client.put(f"/api/dispatch/plans/{revision['id']}", headers=self.h(), json={'expected_version': 1, 'assignments': [{'role_id': 'flagger', 'user_id': 'crew3'}]}).json()
        self.assertEqual(self.approve(edited).status_code, 200)
        plans = {p['id']: p for p in self.client.get(f'/api/dispatch/orders/{self.order}', headers=self.h()).json()['plans']}
        self.assertEqual(plans[first['id']]['status'], 'superseded'); self.assertEqual(plans[first['id']]['sent_assignments'][0]['status'], 'replaced')
        self.assertTrue(any(m.startswith('Assignment cancelled') for m in self.inbox('member')))
        self.assertTrue(any(m.startswith('New assignment') for m in self.inbox('crew3')))

    def test_cancelling_a_sent_plan_notifies_and_is_idempotent(self):
        self.requirements(); sent = self.approve(self.propose()).json()
        body = {'expected_version': sent['version'], 'reason': 'Permit withdrawn'}
        url = f"/api/dispatch/plans/{sent['id']}/cancel"
        cancelled = self.client.post(url, headers=self.h(), json=body); self.assertEqual(cancelled.json()['status'], 'cancelled')
        self.assertEqual(self.client.post(url, headers=self.h(), json=body).json()['status'], 'cancelled')
        self.assertEqual(cancelled.json()['sent_assignments'][0]['status'], 'cancelled')
        self.assertEqual(sum(m.startswith('Assignment cancelled') and 'Permit withdrawn' in m for m in self.inbox('member')), 1)
        self.assertEqual(self.client.get('/api/dispatch/my-assignments', headers=self.h('member')).json()['items'][0]['status'], 'cancelled')
        self.assertEqual(self.client.post(f"/api/dispatch/plans/{sent['id']}/approve", headers=self.h(), json={'request_id': str(uuid4()), 'expected_version': 3}).status_code, 409)

    def test_assignment_text_copy_uses_messaging_consent_and_outbox(self):
        contact = self.client.get('/api/messaging/sms/contact', headers=self.h('member')).json()
        self.client.put('/api/messaging/sms/contact', headers=self.h('member'), json={'request_id': str(uuid4()), 'expected_version': 0, 'phone': PHONE, 'consent': True, 'consent_version': contact['current_consent_version']})
        code = re.search(r'code: (\d{6})', self.provider.sent[-1]['body']).group(1)
        self.client.post('/api/messaging/sms/contact/verify', headers=self.h('member'), json={'code': code})
        self.profile('crew3', 'EMP-3', [window()], version=1)
        self.requirements(count=2); sent = self.approve(self.propose()).json()
        texts = {a['user_id']: a['sms'] for a in sent['sent_assignments']}
        self.assertEqual(texts['crew3']['status'], 'blocked'); self.assertEqual(texts['crew3']['reason'], 'no_contact')
        delivered = [s for s in self.provider.sent if s['body'].startswith('WZOS admin org: New assignment')]
        self.assertEqual(len(delivered), 1); self.assertEqual(delivered[0]['to'], PHONE)
        state = self.client.get(f'/api/dispatch/orders/{self.order}', headers=self.h()).json()['plans'][0]['sent_assignments']
        self.assertEqual({a['user_id']: a['sms']['status'] for a in state}['member'], 'accepted')


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'), 'Dedicated PostgreSQL database not configured')
class PostgreSQLDispatchTests(DispatchTests):
    def make_storage(self, root):
        from tests.test_form_submissions import PostgreSQLFormSubmissionTests
        return PostgreSQLFormSubmissionTests.make_storage(self, root)


if __name__ == '__main__':
    unittest.main()
