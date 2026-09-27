import asyncio
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import httpx
from services.workspace_preview.vllm_intelligence import VLLMIntelligence
from services.workspace_preview.intelligence import ChatInput, ModelUnavailable
from scripts.evaluate_atlas_vllm import evaluate


class VLLMTests(unittest.TestCase):
    def test_private_endpoint_identity_and_full_model(self):
        async def check():
            calls = []
            async def token(audience):
                self.assertEqual(audience, 'https://atlas-example.run.app')
                return 'synthetic.identity.token'
            def handle(request):
                calls.append(request)
                self.assertEqual(str(request.url), 'https://atlas-example.run.app/v1/chat/completions')
                self.assertEqual(request.headers['Authorization'], 'Bearer synthetic.identity.token')
                self.assertEqual(json.loads(request.content)['model'], 'google/gemma-4-31B-it')
                return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': 'Synthetic reply'}}],
                                                'usage': {'prompt_tokens': 10, 'completion_tokens': 2}})
            engine = VLLMIntelligence(httpx.MockTransport(handle), token)
            self.assertFalse(await engine.ready()); self.assertEqual(calls, [])
            await engine.reply(ChatInput(question='Explain'), {})
            self.assertTrue(await engine.ready())
            self.assertEqual(engine.last_usage['prompt_tokens'], 10)
        with patch.dict(os.environ, {'WZOS_ATLAS_VLLM_URL': 'https://atlas-example.run.app', 'WZOS_ATLAS_VLLM_ENABLED': '1'}):
            asyncio.run(check())

    def test_runner_is_bounded_and_stops_on_failure(self):
        class Engine:
            model = 'synthetic'; last_usage = {}; calls = 0
            async def reply(self, payload, context):
                self.calls += 1
                raise ModelUnavailable('synthetic')
        with tempfile.TemporaryDirectory() as directory:
            engine = Engine(); output = Path(directory)/'evidence.jsonl'
            self.assertFalse(asyncio.run(evaluate(engine, output)))
            self.assertEqual(engine.calls, 1)
            self.assertEqual(json.loads(output.read_text())['review_status'], 'needs_human_review')
            with self.assertRaises(FileExistsError): asyncio.run(evaluate(engine, output))

    def test_origin_rejects_external_host(self):
        with patch.dict(os.environ, {'WZOS_ATLAS_VLLM_URL': 'https://example.com'}):
            with self.assertRaises(ValueError): VLLMIntelligence()
