"""Real loopback HTTP lifecycle checks; synthetic provider, no GPU or credentials."""
import asyncio
import json
import os
import unittest
from unittest.mock import patch

from services.workspace_preview.intelligence import ChatInput, ClientDisconnected, reply_until_disconnected
from services.workspace_preview.vllm_intelligence import VLLMIntelligence


class SocketReliabilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_disconnect_closes_real_socket_and_next_request_recovers(self):
        await self.exercise_socket(False)

    async def test_explicit_cancel_closes_real_socket_without_client_disconnect(self):
        await self.exercise_socket(True)

    async def exercise_socket(self, explicit):
        entered, disconnected = asyncio.Event(), asyncio.Event()
        calls, handlers, errors = [], set(), []

        async def provider(reader, writer):
            task = asyncio.current_task()
            handlers.add(task)
            try:
                headers = await reader.readuntil(b'\r\n\r\n')
                length = next(int(line.split(b':', 1)[1]) for line in headers.split(b'\r\n')
                              if line.lower().startswith(b'content-length:'))
                calls.append(json.loads(await reader.readexactly(length)))
                if len(calls) == 1:
                    # Headers arrive, but the provider holds the response body open.
                    writer.write(b'HTTP/1.1 200 OK\r\nContent-Length: 1000\r\n\r\n')
                    await writer.drain()
                    entered.set()
                    if await asyncio.wait_for(reader.read(1), 3) == b'':
                        disconnected.set()
                else:
                    body = json.dumps({'choices': [{'finish_reason': 'stop', 'message': {'content': 'Recovered'}}],
                                       'usage': {'prompt_tokens': 12, 'completion_tokens': 1}}).encode()
                    writer.write(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n'
                                 + f'Content-Length: {len(body)}\r\n\r\n'.encode() + body)
                    await writer.drain()
            except Exception as error:
                errors.append(type(error).__name__)
            finally:
                writer.close()
                await writer.wait_closed()
                handlers.discard(task)

        server = await asyncio.start_server(provider, '127.0.0.1', 0)
        port = server.sockets[0].getsockname()[1]
        async def token(audience):
            return 'synthetic.identity.token'
        class Request:
            async def receive(self):
                await entered.wait()
                if explicit:
                    await asyncio.Event().wait()
                return {'type': 'http.disconnect'}
        async def cancelled():
            return entered.is_set()
        try:
            with patch.dict(os.environ, {'WZOS_ATLAS_VLLM_ENABLED': '1',
                                         'WZOS_ATLAS_VLLM_URL': 'https://atlas-example.run.app'}):
                engine = VLLMIntelligence(token_provider=token)
                # Test-only endpoint override; production HTTPS validation stays intact.
                engine.endpoint = f'http://127.0.0.1:{port}/v1/chat/completions'
                payload = ChatInput(question='Synthetic lifecycle check')
                with self.assertRaises(ClientDisconnected):
                    await asyncio.wait_for(reply_until_disconnected(Request(), engine, payload, {}, cancelled if explicit else None), 5)
                await asyncio.wait_for(disconnected.wait(), 3)
                self.assertFalse(engine.gate.locked())
                self.assertIsNone(engine.last_usage)
                self.assertEqual(await engine.reply(payload, {}), 'Recovered')
                self.assertEqual(len(calls), 2)
                self.assertTrue(all(call['model'] == 'google/gemma-4-31B-it' for call in calls))
                self.assertFalse(errors, errors)
        finally:
            server.close()
            await server.wait_closed()
            for task in list(handlers):
                task.cancel()
            await asyncio.gather(*list(handlers), return_exceptions=True)
