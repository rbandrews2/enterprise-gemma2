import base64
import copy
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from scripts import validate_atlas_invocation as check


def fixture():
    status = {'conditions': [{'type': 'Ready', 'status': 'True'}],
              'latestReadyRevisionName': 'rev1', 'latestCreatedRevisionName': 'rev1',
              'traffic': [{'revisionName': 'rev1', 'percent': 100}],
              'url': 'https://synthetic.run.app'}
    model = {'status': status, 'metadata': {}}
    app = {'status': copy.deepcopy(status), 'spec': {'template': {'spec': {
        'serviceAccountName': check.CALLER, 'containers': [{'env': [
            {'name': 'WZOS_ATLAS_VLLM_URL', 'value': status['url']},
            {'name': 'WZOS_ATLAS_VLLM_ENABLED', 'value': '0'}]}]}}}}
    policy = {'bindings': [{'role': 'roles/run.invoker',
                           'members': ['serviceAccount:' + check.CALLER]}]}
    return app, model, policy


def token(**overrides):
    claims = {'aud': 'https://synthetic.run.app', 'email': check.CALLER, 'exp': time.time() + 3600}
    claims.update(overrides)
    encoded = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip('=')
    return 'synthetic.' + encoded + '.signature'


class InvocationPreflightTests(unittest.TestCase):
    def test_control_plane_is_not_invocation_acceptance(self):
        result = check.inspect(*fixture())
        self.assertTrue(result['configuration_passed'])
        self.assertFalse(result['private_invocation_verified'])
        self.assertFalse(result['inference_accepted'])

    def test_mismatched_identity_target_and_revisions_fail(self):
        for case in ('identity', 'target', 'pending', 'traffic', 'ready'):
            app, model, policy = fixture()
            spec = app['spec']['template']['spec']
            if case == 'identity':
                spec['serviceAccountName'] = 'other'
            elif case == 'target':
                spec['containers'][0]['env'][0]['value'] = 'https://other.run.app'
            elif case == 'pending':
                model['status']['latestCreatedRevisionName'] = 'rev2'
            elif case == 'traffic':
                model['status']['traffic'][0]['percent'] = 50
            else:
                model['status']['conditions'] = []
            with self.subTest(case=case):
                self.assertFalse(check.inspect(app, model, policy)['configuration_passed'])

    def test_public_conditional_or_missing_permissions_fail(self):
        for case in ('public', 'conditional', 'missing', 'disabled'):
            app, model, policy = fixture()
            if case == 'public':
                policy['bindings'][0]['members'].append('allUsers')
            elif case == 'conditional':
                policy['bindings'][0]['condition'] = {'expression': 'true'}
            elif case == 'missing':
                policy['bindings'] = []
            else:
                model['metadata']['annotations'] = {'run.googleapis.com/invoker-iam-disabled': 'true'}
            with self.subTest(case=case):
                self.assertFalse(check.inspect(app, model, policy)['configuration_passed'])

    def test_single_probe_no_redirect_retry_generation_or_token_in_evidence(self):
        client = httpx.Client
        for status in (200, 301, 401, 403, 503):
            calls = []
            secret = token()
            def handler(request):
                calls.append(request)
                return httpx.Response(status, headers={'Location': 'https://other.run.app'},
                                      text='private body')
            result = check.inspect(*fixture())
            with patch.object(check, 'gc', return_value=secret) as gc, \
                    patch.object(check.httpx, 'Client', side_effect=lambda **kw:
                        client(transport=httpx.MockTransport(handler), **kw)):
                check.probe(result)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0].method, 'GET')
            self.assertEqual(calls[0].url.path, '/health')
            self.assertIn(check.CALLER, gc.call_args.args)
            self.assertEqual(result['private_invocation_verified'], status == 200)
            self.assertFalse(result['inference_accepted'])
            self.assertNotIn(secret, json.dumps(result))
            self.assertNotIn('private body', json.dumps(result))

    def test_bad_token_claims_and_missing_impersonation_never_send_http(self):
        for value in (token(aud='wrong'), token(email='other'), token(exp=0), 'bad'):
            with patch.object(check, 'gc', return_value=value), patch.object(check.httpx, 'Client') as client:
                with self.assertRaises(ValueError):
                    check.probe(check.inspect(*fixture()))
                client.assert_not_called()
        with patch.object(check, 'gc', side_effect=RuntimeError('private detail')), \
                patch.object(check.httpx, 'Client') as client:
            with self.assertRaises(RuntimeError):
                check.probe(check.inspect(*fixture()))
            client.assert_not_called()

    def test_default_cli_reads_only_and_redacts_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            args = ['check', '--output', str(path)]
            with patch('sys.argv', args), patch.object(check, 'gc', side_effect=[json.dumps(x) for x in fixture()]) as gc, \
                    patch.object(check, 'probe') as probe, patch('builtins.print'):
                self.assertEqual(check.main(), 0)
                probe.assert_not_called()
                self.assertEqual(gc.call_count, 3)
            with patch('sys.argv', args), patch.object(check, 'gc', side_effect=RuntimeError('SECRET')), patch('builtins.print'):
                self.assertEqual(check.main(), 1)
                self.assertNotIn('SECRET', path.read_text())


if __name__ == '__main__':
    unittest.main()
