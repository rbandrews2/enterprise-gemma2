import os, re, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from uuid import uuid4
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.workspace_preview.storage import SQLiteStorage
from services.workspace_preview import sms_provider
from services.workspace_preview.sms_provider import SendResult, TwilioProvider, signature
from services.v2.knowledge.store import Store
from tests import test_form_submissions as fixtures

TOKEN = 'synthetic-auth-token'
BASE = 'https://wzos.test'
MEMBER_PHONE = '+15550100001'
ADMIN_PHONE = '+15550100002'
OTHER_PHONE = '+15550100009'


class FakeProvider:
    """Records sends; outcomes are consumed in order, then every send is accepted."""
    def __init__(self):
        self.sent, self.outcomes = [], []

    def send(self, outbox_id, to, body):
        self.sent.append({'id': outbox_id, 'to': to, 'body': body})
        if self.outcomes:
            return self.outcomes.pop(0)
        return SendResult('accepted', sid='SM' + uuid4().hex, provider_status='queued')


class MessagingTests(unittest.TestCase):
    def setUp(self, mode='test'):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); root = Path(self.temp.name)
        env = patch.dict(os.environ, {'WZOS_WORKSPACE_PREVIEW': '1', 'WZOS_SMS_MODE': mode, 'WZOS_TWILIO_AUTH_TOKEN': TOKEN,
                                      'WZOS_PUBLIC_BASE_URL': BASE, 'WZOS_SMS_TEST_RECIPIENTS': f'{MEMBER_PHONE},{ADMIN_PHONE}'})
        env.start(); self.addCleanup(env.stop)
        self.storage = self.make_storage(root)
        self.app = create_app(storage=self.storage, knowledge_store=Store(root / 'sources', {}))
        self.provider = FakeProvider(); self.app.state.sms_provider = self.provider
        self.client = TestClient(self.app); self.addCleanup(self.client.close)

    def make_storage(self, root):
        return SQLiteStorage(root / 'db')

    def h(self, who='enterprise-general'):
        return {'X-Preview-Actor': who}

    def contact(self, who='enterprise-general'):
        return self.client.get('/api/messaging/sms/contact', headers=self.h(who)).json()

    def enroll(self, who='enterprise-general', phone=MEMBER_PHONE, **change):
        current = self.contact(who)
        body = {'request_id': str(uuid4()), 'expected_version': current['version'], 'phone': phone, 'consent': True,
                'consent_version': current['current_consent_version'], **change}
        return self.client.put('/api/messaging/sms/contact', headers=self.h(who), json=body)

    def verified(self, who='enterprise-general', phone=MEMBER_PHONE):
        response = self.enroll(who, phone); self.assertEqual(response.status_code, 200, response.text)
        code = re.search(r'code: (\d{6})', self.provider.sent[-1]['body']).group(1)
        response = self.client.post('/api/messaging/sms/contact/verify', headers=self.h(who), json={'code': code})
        self.assertEqual(response.json()['status'], 'verified', response.text)
        return response.json()

    def message(self, who='enterprise-admin', to='enterprise-general', **change):
        body = {'request_id': str(uuid4()), 'recipient_id': to, 'text': 'Report to the Granby Street site at 7:00.', **change}
        return self.client.post('/api/messages', headers=self.h(who), json=body), body

    def sid(self, outbox_id):
        with self.app.state.messaging.connect() as db:
            return db.execute('SELECT provider_sid FROM sms_outbox WHERE id=?', (outbox_id,)).fetchone()[0]

    def outbox(self, who='enterprise-admin'):
        return self.client.get('/api/messaging/sms/outbox', headers=self.h(who)).json()['items']

    def callback(self, outbox_id, status, sid='SMx', error=None, token=TOKEN):
        params = [('MessageSid', sid), ('MessageStatus', status), ('AccountSid', 'ACx')] + ([('ErrorCode', error)] if error else [])
        url = f'{BASE}/api/messaging/twilio/status?outbox={outbox_id}'
        return self.client.post(f'/api/messaging/twilio/status?outbox={outbox_id}', content=urlencode(params),
                                headers={'Content-Type': 'application/x-www-form-urlencoded', 'X-Twilio-Signature': signature(token, url, params)})

    def inbound(self, phone, body):
        params = [('From', phone), ('To', '+15550109999'), ('Body', body), ('MessageSid', 'SMin')]
        return self.client.post('/api/messaging/twilio/inbound', content=urlencode(params),
                                headers={'Content-Type': 'application/x-www-form-urlencoded', 'X-Twilio-Signature': signature(TOKEN, BASE + '/api/messaging/twilio/inbound', params)})

    def test_readiness_is_admin_only_and_names_missing_settings_without_values(self):
        self.assertEqual(self.client.get('/api/messaging/sms/readiness', headers=self.h()).status_code, 403)
        self.app.state.sms_provider = None
        with patch.dict(os.environ, {'WZOS_TWILIO_ACCOUNT_SID': 'ACsecretvalue'}):
            data = self.client.get('/api/messaging/sms/readiness', headers=self.h('enterprise-admin')).json()
        self.assertFalse(data['ready']); self.assertEqual(data['mode'], 'test')
        self.assertIn('WZOS_TWILIO_MESSAGING_SERVICE_SID or WZOS_TWILIO_FROM_NUMBER', data['missing'])
        self.assertNotIn('WZOS_TWILIO_AUTH_TOKEN', data['missing'])
        self.assertNotIn('ACsecretvalue', str(data)); self.assertNotIn(TOKEN, str(data))
        self.assertEqual(data['status_callback_url'], BASE + '/api/messaging/twilio/status')
        with patch.dict(os.environ, {'WZOS_SMS_MODE': 'live'}):
            self.assertEqual(self.client.get('/api/messaging/sms/readiness', headers=self.h('enterprise-admin')).json()['mode'], 'disabled')

    def test_member_consents_and_verifies_own_number(self):
        self.assertEqual(self.enroll(consent=False).status_code, 422)
        self.assertEqual(self.enroll(consent_version='old').status_code, 409)
        response = self.enroll(); self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['status'], 'pending_verification')
        self.assertEqual(response.json()['verification_delivery']['status'], 'queued')
        sent = self.provider.sent[-1]; self.assertEqual(sent['to'], MEMBER_PHONE)
        code = re.search(r'code: (\d{6})', sent['body']).group(1)
        wrong = '000000' if code != '000000' else '111111'
        self.assertEqual(self.client.post('/api/messaging/sms/contact/verify', headers=self.h(), json={'code': wrong}).status_code, 422)
        ok = self.client.post('/api/messaging/sms/contact/verify', headers=self.h(), json={'code': code}).json()
        self.assertEqual(ok['status'], 'verified'); self.assertEqual(ok['consent_version'], self.contact()['current_consent_version'])
        verification = [r for r in self.outbox() if r['purpose'] == 'verification'][0]
        self.assertEqual(verification['status'], 'accepted'); self.assertNotIn(code, verification['body'])
        self.assertEqual(verification['phone'], '•••• 0001')
        # Admins see consent state and masked numbers but cannot enroll or verify a member.
        listed = {i['id']: i for i in self.client.get('/api/messaging/sms/contacts', headers=self.h('enterprise-admin')).json()['items']}
        self.assertEqual(listed['enterprise-general']['status'], 'verified'); self.assertEqual(listed['enterprise-general']['phone'], '•••• 0001')
        self.assertNotIn('enterprise-general', {i['id'] for i in self.client.get('/api/messaging/sms/contacts', headers=self.h('core-admin')).json()['items']})
        self.assertEqual(self.client.get('/api/messaging/sms/contacts', headers=self.h()).status_code, 403)

    def test_verification_attempts_expiry_and_daily_limit(self):
        self.enroll()
        self.assertEqual(self.client.post('/api/messaging/sms/contact/verify', headers=self.h(), json={'code': 'abc123'}).status_code, 422)
        code = re.search(r'code: (\d{6})', self.provider.sent[-1]['body']).group(1)
        attempts = 0
        for _ in range(5):
            wrong = f'{(int(code) + 1) % 1000000:06d}'
            attempts += self.client.post('/api/messaging/sms/contact/verify', headers=self.h(), json={'code': wrong}).status_code == 422
        self.assertEqual(attempts, 5)
        self.assertEqual(self.client.post('/api/messaging/sms/contact/verify', headers=self.h(), json={'code': code}).status_code, 409)
        for _ in range(4):
            self.assertEqual(self.enroll().status_code, 200)
        self.assertEqual(self.enroll().status_code, 429)

    def test_admin_text_copy_is_sent_once_and_tracked_separately_from_acknowledgement(self):
        self.verified()
        response, body = self.message(request_acknowledgement=True, sms_copy=True)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json(); self.assertTrue(data['external_delivery']); self.assertEqual(data['sms']['status'], 'queued')
        self.assertEqual(self.provider.sent[-1]['to'], MEMBER_PHONE)
        self.assertIn('Report to the Granby Street site', self.provider.sent[-1]['body']); self.assertIn('Reply STOP', self.provider.sent[-1]['body'])
        sends = len(self.provider.sent)
        self.assertEqual(self.client.post('/api/messages', headers=self.h('enterprise-admin'), json=body).json()['id'], data['id'])
        self.assertEqual(len(self.provider.sent), sends)
        self.assertEqual(self.client.post('/api/messages', headers=self.h('enterprise-admin'), json={**body, 'sms_copy': False}).status_code, 409)
        sent = self.client.get('/api/messages', headers=self.h('enterprise-admin')).json()['items'][0]
        self.assertEqual(sent['sms']['status'], 'accepted'); self.assertIsNone(sent['acknowledged_at']); self.assertTrue(sent['acknowledgement_requested'])
        received = self.client.get('/api/messages', headers=self.h()).json()['items'][0]
        self.assertIsNone(received['sms'])
        url = f"/api/messages/{data['id']}/acknowledge"
        self.assertEqual(self.client.post(url, headers=self.h('enterprise-admin')).status_code, 404)
        self.assertEqual(self.client.post(url, headers=self.h('core-general')).status_code, 404)
        first = self.client.post(url, headers=self.h()).json(); self.assertEqual(self.client.post(url, headers=self.h()).json(), first)
        sent = self.client.get('/api/messages', headers=self.h('enterprise-admin')).json()['items'][0]
        self.assertEqual(sent['acknowledged_at'], first['acknowledged_at']); self.assertEqual(sent['sms']['status'], 'accepted')

    def test_members_cannot_request_texts_and_ineligible_recipients_are_blocked(self):
        self.assertEqual(self.message('enterprise-general', 'enterprise-admin', sms_copy=True)[0].status_code, 403)
        response = self.message(sms_copy=True)[0].json()
        self.assertEqual(response['sms']['status'], 'blocked'); self.assertEqual(response['sms']['reason'], 'no_contact')
        self.assertFalse(response['external_delivery']); self.assertEqual(self.provider.sent, [])
        self.assertEqual(self.message('enterprise-admin', 'core-general', sms_copy=True)[0].status_code, 404)
        # Test mode refuses numbers outside the approved test list, including verification codes.
        self.assertEqual(self.enroll(phone=OTHER_PHONE).json()['verification_delivery']['reason'], 'not_test_recipient')
        self.assertEqual(self.provider.sent, [])

    def test_disabled_mode_blocks_every_text(self):
        self.verified()
        with patch.dict(os.environ, {'WZOS_SMS_MODE': 'disabled'}):
            sms = self.message(sms_copy=True)[0].json()['sms']
        self.assertEqual((sms['status'], sms['reason']), ('blocked', 'sms_disabled'))

    def test_signed_callbacks_advance_delivery_in_order_and_once(self):
        self.verified(); sms = self.message(sms_copy=True)[0].json()['sms']
        self.assertEqual(self.callback(sms['id'], 'delivered', token='wrong').status_code, 403)
        unsigned = self.client.post(f"/api/messaging/twilio/status?outbox={sms['id']}", content='MessageStatus=delivered', headers={'Content-Type': 'application/x-www-form-urlencoded'})
        self.assertEqual(unsigned.status_code, 403)
        sid = self.sid(sms['id'])
        self.assertEqual(self.callback(sms['id'], 'sent', sid).status_code, 204)
        self.assertEqual(self.callback(sms['id'], 'delivered', sid).status_code, 204)
        self.assertEqual(self.callback(sms['id'], 'delivered', sid).status_code, 204)
        self.assertEqual(self.callback(sms['id'], 'sent', sid).status_code, 204)
        self.assertEqual(self.callback(sms['id'], 'failed', 'SMother').status_code, 204)
        row = [r for r in self.outbox() if r['id'] == sms['id']][0]; self.assertEqual(row['status'], 'delivered')
        events = self.client.get(f"/api/messaging/sms/outbox/{sms['id']}/events", headers=self.h('enterprise-admin')).json()['items']
        self.assertEqual([e['event'] for e in events if e['source'] == 'callback'], ['sent', 'delivered'])
        self.assertEqual(self.client.get(f"/api/messaging/sms/outbox/{sms['id']}/events", headers=self.h('core-admin')).status_code, 404)
        self.assertEqual(self.client.get('/api/messaging/sms/outbox', headers=self.h('core-admin')).json()['items'], [])
        self.assertEqual(self.client.get('/api/messaging/sms/outbox', headers=self.h()).status_code, 403)

    def test_undelivered_callback_records_failure_code(self):
        self.verified(); sms = self.message(sms_copy=True)[0].json()['sms']
        self.callback(sms['id'], 'undelivered', self.sid(sms['id']), error='30003')
        row = [r for r in self.outbox() if r['id'] == sms['id']][0]
        self.assertEqual((row['status'], row['error_code']), ('undelivered', '30003'))

    def test_retryable_failures_back_off_then_fail(self):
        self.verified(); messaging = self.app.state.messaging
        self.provider.outcomes = [SendResult('retryable', detail='busy')] * 4
        sms = self.message(sms_copy=True)[0].json()['sms']
        row = [r for r in self.outbox() if r['id'] == sms['id']][0]; self.assertEqual((row['status'], row['attempts']), ('queued', 1))
        for _ in range(3):
            with messaging.connect() as db:
                db.execute("UPDATE sms_outbox SET next_attempt_at='2000-01-01T00:00:00+00:00' WHERE id=?", (sms['id'],))
            messaging.process('enterprise-demo')
        row = [r for r in self.outbox() if r['id'] == sms['id']][0]
        self.assertEqual((row['status'], row['reason'], row['attempts']), ('failed', 'retries_exhausted', 4))

    def test_ambiguous_send_needs_admin_confirmation_and_callback_can_resolve_it(self):
        self.verified(); messaging = self.app.state.messaging
        self.provider.outcomes = [SendResult('ambiguous', detail='timeout')]
        sms = self.message(sms_copy=True)[0].json()['sms']; sends = len(self.provider.sent)
        messaging.process('enterprise-demo'); self.assertEqual(len(self.provider.sent), sends)
        url = f"/api/messaging/sms/outbox/{sms['id']}/resolve"
        self.assertEqual(self.client.post(url, headers=self.h('enterprise-admin'), json={'action': 'retry'}).status_code, 409)
        self.assertEqual(self.client.post(url, headers=self.h(), json={'action': 'mark_failed'}).status_code, 403)
        self.assertEqual(self.client.post(url, headers=self.h('core-admin'), json={'action': 'mark_failed'}).status_code, 404)
        self.callback(sms['id'], 'delivered', 'SMlate')
        self.assertEqual([r for r in self.outbox() if r['id'] == sms['id']][0]['status'], 'delivered')
        self.provider.outcomes = [SendResult('ambiguous', detail='timeout')]
        second = self.message(sms_copy=True)[0].json()['sms']
        resent = self.client.post(f"/api/messaging/sms/outbox/{second['id']}/resolve", headers=self.h('enterprise-admin'),
                                  json={'action': 'retry', 'confirm_possible_duplicate': True, 'note': 'Provider console shows no message'})
        self.assertEqual(resent.status_code, 200, resent.text)
        self.assertEqual([r for r in self.outbox() if r['id'] == second['id']][0]['status'], 'accepted')

    def test_admin_marked_failure_yields_to_provider_evidence(self):
        self.verified(); self.provider.outcomes = [SendResult('ambiguous')]
        sms = self.message(sms_copy=True)[0].json()['sms']
        self.client.post(f"/api/messaging/sms/outbox/{sms['id']}/resolve", headers=self.h('enterprise-admin'), json={'action': 'mark_failed'})
        self.callback(sms['id'], 'delivered', 'SMlate')
        self.assertEqual([r for r in self.outbox() if r['id'] == sms['id']][0]['status'], 'delivered')

    def test_expired_send_lease_becomes_ambiguous_not_resent(self):
        self.verified(); messaging = self.app.state.messaging
        response, _ = self.message(sms_copy=True); outbox_id = response.json()['sms']['id']
        with messaging.connect() as db:
            db.execute("UPDATE sms_outbox SET status='sending',provider_sid=NULL,lease_until='2000-01-01T00:00:00+00:00' WHERE id=?", (outbox_id,))
        sends = len(self.provider.sent); messaging.process('enterprise-demo')
        row = [r for r in self.outbox() if r['id'] == outbox_id][0]
        self.assertEqual((row['status'], row['reason']), ('ambiguous', 'lease_expired')); self.assertEqual(len(self.provider.sent), sends)

    def test_stop_and_start_keywords_and_provider_opt_out(self):
        self.verified(); self.verified('enterprise-admin', ADMIN_PHONE)
        self.assertEqual(self.inbound(MEMBER_PHONE, 'stop ').status_code, 200)
        self.assertEqual(self.contact()['status'], 'opted_out')
        sms = self.message(sms_copy=True)[0].json()['sms']; self.assertEqual((sms['status'], sms['reason']), ('blocked', 'opted_out'))
        self.assertEqual(self.inbound(MEMBER_PHONE, 'START').status_code, 200); self.assertEqual(self.contact()['status'], 'verified')
        self.provider.outcomes = [SendResult('rejected', error_code='21610')]
        sms = self.message(sms_copy=True)[0].json()['sms']
        row = [r for r in self.outbox() if r['id'] == sms['id']][0]; self.assertEqual((row['status'], row['reason']), ('blocked', 'opted_out'))
        self.assertEqual(self.contact()['status'], 'opted_out'); self.assertEqual(self.contact('enterprise-admin')['status'], 'verified')
        params = [('From', MEMBER_PHONE), ('Body', 'START')]
        forged = self.client.post('/api/messaging/twilio/inbound', content=urlencode(params), headers={'Content-Type': 'application/x-www-form-urlencoded', 'X-Twilio-Signature': 'forged'})
        self.assertEqual(forged.status_code, 403); self.assertEqual(self.contact()['status'], 'opted_out')

    def test_member_opt_out_blocks_queued_texts(self):
        contact = self.verified(); messaging = self.app.state.messaging
        self.provider.outcomes = [SendResult('retryable')]
        sms = self.message(sms_copy=True)[0].json()['sms']
        stale = self.client.post('/api/messaging/sms/contact/opt-out', headers=self.h(), json={'expected_version': contact['version'] - 1})
        self.assertEqual(stale.status_code, 409)
        out = self.client.post('/api/messaging/sms/contact/opt-out', headers=self.h(), json={'expected_version': contact['version']})
        self.assertEqual(out.json()['status'], 'opted_out')
        self.assertEqual(self.client.post('/api/messaging/sms/contact/opt-out', headers=self.h(), json={'expected_version': contact['version']}).json(), out.json())
        row = [r for r in self.outbox() if r['id'] == sms['id']][0]; self.assertEqual((row['status'], row['reason']), ('blocked', 'opted_out'))
        # Re-enrolling the same number requires fresh consent and verification.
        self.assertEqual(self.enroll().json()['status'], 'pending_verification')

    def test_number_change_blocks_texts_queued_for_the_old_number(self):
        self.verified(); messaging = self.app.state.messaging
        self.provider.outcomes = [SendResult('retryable')]
        sms = self.message(sms_copy=True)[0].json()['sms']
        self.enroll(phone=ADMIN_PHONE)
        with messaging.connect() as db:
            db.execute("UPDATE sms_outbox SET next_attempt_at='2000-01-01T00:00:00+00:00' WHERE id=?", (sms['id'],))
        messaging.process('enterprise-demo')
        row = [r for r in self.outbox() if r['id'] == sms['id']][0]; self.assertEqual((row['status'], row['reason']), ('blocked', 'contact_changed'))

    def test_queued_and_blocked_texts_can_be_cancelled_and_blocked_retried(self):
        self.verified()
        with patch.dict(os.environ, {'WZOS_SMS_MODE': 'disabled'}):
            sms = self.message(sms_copy=True)[0].json()['sms']
        url = f"/api/messaging/sms/outbox/{sms['id']}/resolve"
        retried = self.client.post(url, headers=self.h('enterprise-admin'), json={'action': 'retry'}).json()
        self.assertEqual(retried['status'], 'queued')
        self.assertEqual([r for r in self.outbox() if r['id'] == sms['id']][0]['status'], 'accepted')
        self.assertEqual(self.client.post(url, headers=self.h('enterprise-admin'), json={'action': 'cancel'}).status_code, 409)


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'), 'Dedicated PostgreSQL database not configured')
class PostgreSQLMessagingTests(MessagingTests):
    make_storage = fixtures.PostgreSQLFormSubmissionTests.make_storage


class TwilioProviderTests(unittest.TestCase):
    def provider(self, handler):
        return TwilioProvider('ACtest', TOKEN, BASE, messaging_service_sid='MGtest', transport=httpx.MockTransport(handler))

    def test_request_shape_and_outcomes(self):
        seen = {}
        def accepted(request):
            seen['url'] = str(request.url); seen['auth'] = request.headers['authorization']; seen['form'] = request.content.decode()
            return httpx.Response(201, json={'sid': 'SM123', 'status': 'queued'})
        result = self.provider(accepted).send('out-1', MEMBER_PHONE, 'Hello')
        self.assertEqual((result.outcome, result.sid, result.provider_status), ('accepted', 'SM123', 'queued'))
        self.assertTrue(seen['url'].endswith('/Accounts/ACtest/Messages.json')); self.assertTrue(seen['auth'].startswith('Basic '))
        self.assertIn('MessagingServiceSid=MGtest', seen['form']); self.assertIn('StatusCallback=https%3A%2F%2Fwzos.test%2Fapi%2Fmessaging%2Ftwilio%2Fstatus%3Foutbox%3Dout-1', seen['form'])
        cases = [(httpx.Response(400, json={'code': 21211, 'message': 'Invalid To +15550100001'}), 'rejected'),
                 (httpx.Response(429, json={'code': 20429}), 'retryable'), (httpx.Response(503), 'retryable'),
                 (httpx.Response(500), 'ambiguous'), (httpx.Response(200, json={}), 'rejected')]
        for response, outcome in cases:
            result = self.provider(lambda request, response=response: response).send('o', MEMBER_PHONE, 'x')
            self.assertEqual(result.outcome, outcome); self.assertNotIn(MEMBER_PHONE, result.detail)
        def refused(request): raise httpx.ConnectError('down')
        def timed_out(request): raise httpx.ReadTimeout('slow')
        self.assertEqual(self.provider(refused).send('o', MEMBER_PHONE, 'x').outcome, 'retryable')
        self.assertEqual(self.provider(timed_out).send('o', MEMBER_PHONE, 'x').outcome, 'ambiguous')

    def test_signature_matches_twilio_documented_example(self):
        params = [('CallSid', 'CA1234567890ABCDE'), ('Caller', '+14158675310'), ('Digits', '1234'), ('From', '+14158675310'), ('To', '+18005551212')]
        self.assertEqual(signature('12345', 'https://example.com/myapp.php?foo=1&bar=2', params), 'L/OH5YylLD5NRKLltdqwSvS0BnU=')

    def test_environment_configuration(self):
        with patch.dict(os.environ, {'WZOS_TWILIO_ACCOUNT_SID': '', 'WZOS_TWILIO_AUTH_TOKEN': '', 'WZOS_PUBLIC_BASE_URL': 'http://insecure'}, clear=False):
            missing = sms_provider.settings()['missing']
            self.assertIn('WZOS_PUBLIC_BASE_URL (must use https)', missing); self.assertIsNone(TwilioProvider.from_environment())


if __name__ == '__main__':
    unittest.main()
