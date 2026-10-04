import unittest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import httpx
from scripts.validate_atlas_reliability_staging import valid_concurrent_outcome, run


class ConcurrentAcceptanceTests(unittest.TestCase):
    def test_concurrency_only_sends_exactly_two_distinct_requests(self):
        calls = []
        def handle(request):
            if request.url.path == '/api/identities':
                return httpx.Response(200, json={'auth_header': 'X-WZOS-Authorization'})
            self.assertEqual(request.url.path, '/api/assistant/chat')
            calls.append(json.loads(request.content))
            if len(calls) == 2:
                return httpx.Response(503, json={'code': 'busy'})
            return httpx.Response(200, json={'model_called': True, 'approved_for_field_use': False,
                                            'actions_performed': []})
        client = httpx.AsyncClient
        def factory(**kwargs):
            return client(transport=httpx.MockTransport(handle), **kwargs)
        prefix = 'scripts.validate_atlas_reliability_staging.'
        with tempfile.TemporaryDirectory() as directory, patch(prefix+'gc', side_effect=lambda *a:
                'https://synthetic.run.app' if a[0] == 'run' else 'private-token'), \
                patch(prefix+'require_token_lifetime'), patch(prefix+'httpx.AsyncClient', side_effect=factory):
            output = Path(directory)/'result.jsonl'
            asyncio.run(run({'users': {'member': {'idToken': 'private-token'}}, 'orgs': {'main': 'synthetic'}},
                {'synthetic': True, 'job_id': 'synthetic', 'response': {'order_version': 1},
                 'question': 'Private synthetic question'}, output, concurrency_only=True))
            evidence = output.read_text()
            self.assertNotIn('private-token', evidence)
            self.assertNotIn('Private synthetic question', evidence)
            rows = [json.loads(line) for line in evidence.splitlines()]
            self.assertEqual([row['request_id'] for row in rows[:2]],
                             [call['request_id'] for call in calls])
            self.assertTrue(all(row['started_at'].endswith('+00:00') for row in rows[:2]))
        self.assertEqual(len(calls), 2)
        self.assertNotEqual(calls[0]['request_id'], calls[1]['request_id'])

    def test_failed_request_preserves_peer_outcome_without_retry_or_private_errors(self):
        for failure in ('transport', 'list_body', 'invalid_success'):
            with self.subTest(failure=failure):
                calls, completed = [], []
                async def handle(request):
                    if request.url.path == '/api/identities':
                        return httpx.Response(200,json={'auth_header':'X-WZOS-Authorization'})
                    calls.append(json.loads(request.content))
                    if len(calls) == 1:
                        if failure == 'transport':
                            raise httpx.ReadTimeout('private error secret',request=request)
                        return httpx.Response(200,json=[] if failure == 'list_body' else
                                              {'model_called':True,'approved_for_field_use':True})
                    await asyncio.sleep(0.02)
                    completed.append(True)
                    return httpx.Response(200,json={'model_called':True,
                        'approved_for_field_use':False,'actions_performed':[]})
                client = httpx.AsyncClient
                prefix = 'scripts.validate_atlas_reliability_staging.'
                with tempfile.TemporaryDirectory() as directory, \
                        patch(prefix+'gc',side_effect=lambda *a:
                              'https://synthetic.run.app' if a[0]=='run' else 'private-token'), \
                        patch(prefix+'require_token_lifetime'), \
                        patch(prefix+'httpx.AsyncClient',side_effect=lambda **kw:
                              client(transport=httpx.MockTransport(handle),**kw)):
                    output = Path(directory)/'result.jsonl'
                    with self.assertRaisesRegex(RuntimeError,'Concurrent request failed'):
                        asyncio.run(run({'users':{'member':{'idToken':'private-token'}},
                            'orgs':{'main':'synthetic'}}, {'synthetic':True,'job_id':'synthetic',
                            'response':{'order_version':1},'question':'Private question'},
                            output,concurrency_only=True))
                    raw = output.read_text()
                    rows = [json.loads(line) for line in raw.splitlines()]
                    self.assertEqual(len(rows),2)
                    self.assertEqual(rows[1]['http_status'],200)
                    self.assertIn('error_type',rows[0])
                    self.assertEqual({r['request_id'] for r in rows},
                                     {r['request_id'] for r in calls})
                    for private in ('private-token','Private question','private error secret'):
                        self.assertNotIn(private,raw)
                self.assertEqual(len(calls),2)
                self.assertEqual(completed,[True])

    def test_only_success_and_explicit_busy_are_accepted(self):
        success = {'http_status': 200, 'model_called': True, 'error_code': None}
        busy = {'http_status': 503, 'model_called': False, 'error_code': 'busy'}
        self.assertTrue(valid_concurrent_outcome([success, busy]))
        self.assertTrue(valid_concurrent_outcome([success, success]))
        self.assertFalse(valid_concurrent_outcome([busy, busy]))
        self.assertFalse(valid_concurrent_outcome([success]))
        for code in ('timeout', 'provider_error', 'disabled', 'unavailable', None):
            with self.subTest(code=code):
                self.assertFalse(valid_concurrent_outcome([success, {**busy, 'error_code': code}]))
        self.assertFalse(valid_concurrent_outcome([success, {**success, 'model_called': False}]))
