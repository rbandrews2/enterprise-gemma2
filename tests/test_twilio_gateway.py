import unittest
from unittest.mock import Mock
from urllib.parse import urlencode

import httpx
from fastapi.testclient import TestClient
from services.workspace_preview.sms_provider import signature
from services.workspace_preview.twilio_gateway import create_app, origin


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.base = 'https://callback.test'
        self.upstream = 'https://private-workspace.run.app'
        self.token = 'synthetic-twilio-token'
        self.sid = 'AC' + '1' * 32
        self.forwarded = []
        self.tokens = Mock(return_value='synthetic-iam-token')
        self.status = 204

        def transport(request):
            self.forwarded.append(request)
            return httpx.Response(self.status, text='must not be exposed',
                                  headers={'Set-Cookie': 'must-not-relay=1'})
        self.client = TestClient(create_app(public_origin=self.base,
            upstream=self.upstream, auth_token=self.token, account_sid=self.sid,
            token_provider=self.tokens, transport=httpx.MockTransport(transport)))
        self.addCleanup(self.client.close)
        self.params = [('AccountSid', self.sid), ('MessageSid', 'SM' + '2' * 32),
                       ('MessageStatus', 'delivered'), ('NewProviderField', 'future value')]
        self.path = '/api/messaging/twilio/status?outbox=synthetic-id'

    def post(self, *, path=None, params=None, body=None, headers=None):
        path = path or self.path
        params = params if params is not None else self.params
        h = {'Content-Type': 'application/x-www-form-urlencoded',
             'X-Twilio-Signature': signature(self.token, self.base + path, params)}
        h.update(headers or {})
        return self.client.post(path, content=body if body is not None else urlencode(params), headers=h)

    def test_signed_status_preserves_body_query_and_separate_iam(self):
        r = self.post()
        self.assertEqual(r.status_code, 204)
        forwarded = self.forwarded[0]
        self.assertEqual(str(forwarded.url), self.upstream + self.path)
        self.assertEqual(forwarded.content, urlencode(self.params).encode())
        self.assertEqual(forwarded.headers['X-Serverless-Authorization'], 'Bearer synthetic-iam-token')
        self.assertNotIn('cookie', forwarded.headers)
        self.assertNotIn('set-cookie', r.headers)
        self.assertEqual(r.headers['cache-control'], 'no-store')
        self.tokens.assert_called_once_with(self.upstream)

    def test_signed_inbound_returns_only_empty_twiml(self):
        self.status = 200
        r = self.post(path='/api/messaging/twilio/inbound')
        self.assertEqual(r.status_code, 200)
        self.assertIn('<Response></Response>', r.text)
        self.assertNotIn('must not', r.text)

    def test_missing_and_invalid_signatures_do_not_get_iam(self):
        for supplied in ('', 'wrong'):
            self.assertEqual(self.post(headers={'X-Twilio-Signature': supplied}).status_code, 403)
        self.tokens.assert_not_called()
        self.assertEqual(self.forwarded, [])

    def test_changed_body_or_query_rejected(self):
        h = {'X-Twilio-Signature': signature(self.token, self.base + self.path, self.params)}
        self.assertEqual(self.post(body=urlencode(self.params) + '&Extra=changed').status_code, 403)
        self.assertEqual(self.post(path=self.path + '&changed=1', headers=h).status_code, 403)

    def test_duplicate_or_wrong_account_rejected_even_if_signed(self):
        for p in (self.params + [('AccountSid', self.sid)], [('AccountSid', 'other-account')]):
            self.assertEqual(self.post(params=p).status_code, 403)
        self.tokens.assert_not_called()

    def test_only_fixed_routes_and_post_allowed(self):
        for p in ('/api/orders', '/api/account', '/docs', '/openapi.json', '/',
                  '/api/messaging/twilio/status/'):
            self.assertEqual(self.client.get(p).status_code, 404)
            self.assertEqual(self.post(path=p).status_code, 404)
        self.assertEqual(self.client.get(self.path).status_code, 405)
        self.assertEqual(self.client.get('/healthz').json(), {'status': 'ok'})
        self.tokens.assert_not_called()

    def test_oversized_and_invalid_input_rejected(self):
        self.assertEqual(self.post(body=b'x' * 16385).status_code, 413)
        self.assertEqual(self.post(body=b'\xff').status_code, 400)
        self.assertEqual(self.post(body='&'.join(['k=v'] * 257)).status_code, 400)
        self.assertEqual(self.post(headers={'Content-Type': 'application/json'}).status_code, 415)
        self.tokens.assert_not_called()

    def test_proxy_headers_cannot_change_signature_origin_or_target(self):
        self.assertEqual(self.post(headers={'X-Forwarded-Host': 'attacker.test',
            'X-Forwarded-Proto': 'http', 'X-Upstream': 'http://169.254.169.254'}).status_code, 204)
        self.assertEqual(self.forwarded[0].url.host, 'private-workspace.run.app')
        self.assertNotIn('x-upstream', self.forwarded[0].headers)

    def test_upstream_errors_and_redirects_not_relayed_or_retried(self):
        for code in (302, 403, 500):
            self.status = code
            r = self.post()
            self.assertEqual(r.status_code, 502)
            self.assertEqual(r.content, b'')
        self.assertEqual(len(self.forwarded), 3)

    def test_iam_failure_is_redacted_without_forwarding(self):
        self.tokens.side_effect = RuntimeError('sensitive token')
        r = self.post()
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.content, b'')
        self.assertEqual(self.forwarded, [])

    def test_origin_configuration_rejects_dynamic_or_insecure_destinations(self):
        for value in ('http://private.run.app', 'https://private.run.app/path',
                      'https://u:p@private.run.app', 'https://private.run.app?target=a',
                      'https://private.run.app:443', 'https://attacker.test'):
            with self.assertRaises(ValueError):
                origin(value, private=True)
        self.assertEqual(origin(self.upstream, private=True), self.upstream)


if __name__ == '__main__':
    unittest.main()
