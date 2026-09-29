"""Deterministic private-adapter lifecycle checks; no model, credentials or network."""
import asyncio
import os
import unittest
from unittest.mock import patch
import httpx
from services.workspace_preview.vllm_intelligence import VLLMIntelligence
from services.workspace_preview.intelligence import ChatInput, ModelUnavailable, ClientDisconnected, reply_until_disconnected


def success():
    return httpx.Response(200, json={'choices':[{'finish_reason':'stop','message':{'content':'Recovered reply'}}],
                                    'usage':{'prompt_tokens':12,'completion_tokens':3}})


class PrivateReliabilityTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'WZOS_ATLAS_VLLM_ENABLED':'1','WZOS_ATLAS_VLLM_URL':'https://atlas-example.run.app'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.payload = ChatInput(question='Explain the saved project')

    def engine(self, handler):
        async def token(audience): return 'synthetic.identity.token'
        return VLLMIntelligence(httpx.MockTransport(handler), token)

    async def test_overlap_rejected_without_second_provider_call_and_recovery(self):
        entered, release = asyncio.Event(), asyncio.Event()
        calls = []
        async def handler(request):
            calls.append(request)
            entered.set()
            await release.wait()
            return success()
        engine = self.engine(handler)
        first = asyncio.create_task(engine.reply(self.payload, {}))
        try:
            await asyncio.wait_for(entered.wait(), 1)
            with self.assertRaisesRegex(ModelUnavailable, 'another request'):
                await engine.reply(self.payload, {})
            self.assertEqual(len(calls), 1)
        finally:
            release.set()
            await first
        self.assertEqual(await engine.reply(self.payload, {}), 'Recovered reply')
        self.assertEqual(len(calls), 2)
        self.assertFalse(engine.gate.locked())

    async def test_disconnect_closes_upstream_stream_and_next_request_works(self):
        entered, closed = asyncio.Event(), asyncio.Event()
        class BlockingStream(httpx.AsyncByteStream):
            async def __aiter__(self):
                entered.set()
                await asyncio.Event().wait()
                yield b''
            async def aclose(self): closed.set()
        calls = 0
        async def handler(request):
            nonlocal calls
            calls += 1
            return httpx.Response(200, stream=BlockingStream()) if calls == 1 else success()
        class Request:
            async def receive(self):
                await entered.wait()
                return {'type':'http.disconnect'}
        engine = self.engine(handler)
        with self.assertRaises(ClientDisconnected):
            await asyncio.wait_for(reply_until_disconnected(Request(), engine, self.payload, {}), 2)
        self.assertTrue(closed.is_set())
        self.assertFalse(engine.gate.locked())
        self.assertIsNone(engine.last_usage)
        self.assertEqual(await engine.reply(self.payload, {}), 'Recovered reply')
        self.assertEqual(calls, 2)

    async def test_deadline_cancels_transport_without_retry_then_recovers(self):
        cancelled = asyncio.Event()
        calls = 0
        async def handler(request):
            nonlocal calls
            calls += 1
            if calls == 1:
                try: await asyncio.Event().wait()
                finally: cancelled.set()
            return success()
        engine = self.engine(handler)
        engine.deadline = 0.02
        with self.assertRaises(ModelUnavailable): await engine.reply(self.payload, {})
        self.assertEqual(calls, 1)
        self.assertTrue(cancelled.is_set())
        self.assertFalse(await engine.ready())
        self.assertFalse(engine.gate.locked())
        engine.deadline = 10
        self.assertEqual(await engine.reply(self.payload, {}), 'Recovered reply')

    async def test_upstream_failure_logged_without_sensitive_body_then_recovers(self):
        calls = 0
        async def handler(request):
            nonlocal calls
            calls += 1
            return httpx.Response(403, text='private-token-and-body') if calls == 1 else success()
        engine = self.engine(handler)
        with self.assertLogs('services.workspace_preview.managed_intelligence', level='WARNING') as logs:
            with self.assertRaises(ModelUnavailable) as error: await engine.reply(self.payload, {})
        diagnostic = ' '.join(logs.output)
        self.assertIn('upstream_status=403', diagnostic)
        self.assertIn('mode=private_vllm', diagnostic)
        self.assertNotIn('private-token', diagnostic + str(error.exception))
        self.assertNotIn('synthetic.identity.token', diagnostic)
        self.assertEqual(calls, 1)
        self.assertFalse(await engine.ready())
        self.assertEqual(await engine.reply(self.payload, {}), 'Recovered reply')
