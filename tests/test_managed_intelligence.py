import asyncio
import json
import os
import unittest
from unittest.mock import patch

import httpx

from services.workspace_preview.intelligence import ChatInput, ModelUnavailable, configured_intelligence
from services.workspace_preview.managed_intelligence import ManagedGemmaIntelligence, ENDPOINT, MODEL, access_token


class ManagedIntelligenceTests(unittest.TestCase):
    def test_fixed_full_model_and_no_paid_readiness_probe(self):
        async def check():
            calls = []
            async def token():
                return 'synthetic-token'
            def handle(request):
                calls.append(request)
                self.assertEqual(str(request.url), ENDPOINT)
                self.assertEqual(request.headers['Authorization'], 'Bearer synthetic-token')
                body = json.loads(request.content)
                self.assertEqual(body['model'], MODEL)
                self.assertEqual(body['max_tokens'], 1024)
                self.assertFalse(body['chat_template_kwargs']['enable_thinking'])
                self.assertNotIn('tools', body)
                return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': 'Synthetic answer'}}],
                                                'usage': {'prompt_tokens': 100, 'completion_tokens': 4}})
            engine = ManagedGemmaIntelligence(httpx.MockTransport(handle), token)
            self.assertFalse(await engine.ready())
            self.assertEqual(calls, [])
            self.assertEqual(await engine.reply(ChatInput(question='Explain.'), {'role': 'member'}), 'Synthetic answer')
            self.assertTrue(await engine.ready())
            self.assertEqual(len(calls), 1)
        with patch.dict(os.environ, {'WZOS_ATLAS_MANAGED_ENABLED': '1'}):
            asyncio.run(check())

    def test_disabled_and_oversized_context_never_authenticate(self):
        async def check():
            async def forbidden():
                self.fail('No credentials should be requested')
            engine = ManagedGemmaIntelligence(token_provider=forbidden)
            with patch.dict(os.environ, {'WZOS_ATLAS_MANAGED_ENABLED': ''}):
                self.assertFalse(await engine.ready())
                with self.assertRaises(ModelUnavailable):
                    await engine.reply(ChatInput(question='Explain.'), {})
            with patch.dict(os.environ, {'WZOS_ATLAS_MANAGED_ENABLED': '1'}):
                with self.assertRaises(ModelUnavailable):
                    await engine.reply(ChatInput(question='Explain.'), {'notes': 'x' * 17000})
            self.assertFalse(engine.gate.locked())
        asyncio.run(check())
        with patch.dict(os.environ, {'WZOS_ATLAS_PROVIDER': 'managed_gemma'}):
            self.assertIsInstance(configured_intelligence(), ManagedGemmaIntelligence)

    def test_fail_closed_no_redirect_retry_or_error_disclosure(self):
        async def check():
            async def token(): return 'synthetic-token'
            responses = [httpx.Response(302, headers={'Location': 'https://evil.example'}),
                         httpx.Response(429, text='synthetic-secret'), httpx.Response(200, text='x'*65537),
                         httpx.Response(200, json={'choices': []}),
                         httpx.Response(200, json={'choices': [{'finish_reason': 'length', 'message': {'content': 'partial'}}]}),
                         httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': 'hello', 'tool_calls': [{}]}}]}),
                         httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': 'hello'}}]})]
            for response in responses:
                calls = []
                def handle(request): calls.append(request); return response
                engine = ManagedGemmaIntelligence(httpx.MockTransport(handle), token)
                with self.assertRaises(ModelUnavailable) as caught:
                    await engine.reply(ChatInput(question='Explain.'), {})
                self.assertNotIn('synthetic', str(caught.exception))
                self.assertEqual(len(calls), 1)
                self.assertFalse(engine.gate.locked())
                self.assertFalse(await engine.ready())
        with patch.dict(os.environ, {'WZOS_ATLAS_MANAGED_ENABLED': '1'}): asyncio.run(check())

    def test_metadata_origin_size_and_service_boundary(self):
        async def check():
            calls = []
            def handle(request):
                calls.append(request)
                self.assertEqual(request.url.host, 'metadata.google.internal')
                self.assertEqual(request.headers['Metadata-Flavor'], 'Google')
                return httpx.Response(200, headers={'Metadata-Flavor': 'Google'},
                                      json={'access_token': 'synthetic-token', 'token_type': 'Bearer'})
            transport = httpx.MockTransport(handle)
            with patch.dict(os.environ, {'K_SERVICE': ''}):
                with self.assertRaises(ModelUnavailable): await access_token(transport)
            self.assertEqual(calls, [])
            with patch.dict(os.environ, {'K_SERVICE': 'synthetic'}):
                self.assertEqual(await access_token(transport), 'synthetic-token')
                for response in (httpx.Response(200, json={}), httpx.Response(302),
                                 httpx.Response(200, headers={'Metadata-Flavor': 'Google'}, text='x'*20000)):
                    with self.assertRaises(ModelUnavailable):
                        await access_token(httpx.MockTransport(lambda request: response))
        asyncio.run(check())
