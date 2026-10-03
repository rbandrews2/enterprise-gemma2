import asyncio
import os
import unittest
from unittest.mock import patch

import httpx

from services.workspace_preview.intelligence import ChatInput, ModelUnavailable
from services.workspace_preview.vllm_intelligence import VLLMIntelligence


class BrokenBody(httpx.AsyncByteStream):
    async def __aiter__(self):
        yield b'{'
        raise httpx.ReadTimeout('private-provider-detail')


class TransportDiagnosticsTests(unittest.TestCase):
    def test_failure_phase_no_retry_and_recovery(self):
        async def check(case):
            calls = []

            async def token(audience):
                return 'secret.identity.token'

            def handle(request):
                calls.append(request)
                if len(calls) == 1:
                    if case == 'headers':
                        raise httpx.ReadTimeout('private-provider-detail')
                    if case == 'body':
                        return httpx.Response(200, stream=BrokenBody())
                    return httpx.Response(500, text='private-provider-detail')
                return httpx.Response(200, json={
                    'choices': [{'finish_reason': 'stop', 'message': {'content': 'Recovered'}}],
                    'usage': {'prompt_tokens': 2, 'completion_tokens': 1}})

            engine = VLLMIntelligence(httpx.MockTransport(handle), token)
            with self.assertLogs('services.workspace_preview.managed_intelligence', level='INFO') as logs:
                with self.assertRaises(ModelUnavailable):
                    await engine.reply(ChatInput(question='private-question'), {'private': 'context'})
            output = '\n'.join(logs.output)
            self.assertIn('phase=response_headers' if case == 'headers' else 'phase=response_body', output)
            self.assertIn('upstream_status=' + {'headers': 'None', 'body': '200', 'status': '500'}[case], output)
            self.assertRegex(output, r'attempt_id=[0-9a-f]{32}')
            for secret in ('private-provider-detail', 'private-question', 'secret.identity.token'):
                self.assertNotIn(secret, output)
            self.assertEqual(len(calls), 1)
            self.assertFalse(await engine.ready())
            self.assertFalse(engine.gate.locked())
            self.assertEqual(await engine.reply(ChatInput(question='Retry explicitly'), {}), 'Recovered')
            self.assertEqual(len(calls), 2)

        with patch.dict(os.environ, {'WZOS_ATLAS_VLLM_URL': 'https://atlas-example.run.app',
                                     'WZOS_ATLAS_VLLM_ENABLED': '1'}):
            for case in ('headers', 'body', 'status'):
                with self.subTest(case=case):
                    asyncio.run(check(case))

    def test_cancellation_clears_readiness_and_releases_gate(self):
        async def check():
            entered = asyncio.Event()

            async def token(audience):
                entered.set()
                await asyncio.Event().wait()

            engine = VLLMIntelligence(token_provider=token)
            engine.last_success = 1
            with self.assertLogs('services.workspace_preview.managed_intelligence', level='INFO') as logs:
                task = asyncio.create_task(engine.reply(ChatInput(question='Explain'), {}))
                await entered.wait()
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
            self.assertIn('phase=authentication', '\n'.join(logs.output))
            self.assertIsNone(engine.last_success)
            self.assertFalse(engine.gate.locked())

        with patch.dict(os.environ, {'WZOS_ATLAS_VLLM_URL': 'https://atlas-example.run.app',
                                     'WZOS_ATLAS_VLLM_ENABLED': '1'}):
            asyncio.run(check())
