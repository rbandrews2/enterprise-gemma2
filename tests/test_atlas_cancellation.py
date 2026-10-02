import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import httpx
from services.workspace_preview.app import create_app
from services.v2.knowledge.store import Store


class CancellationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = patch.dict(os.environ, {'WZOS_WORKSPACE_PREVIEW':'1','K_SERVICE':'','GAE_ENV':'','NETLIFY':''})
        self.env.start(); self.addCleanup(self.env.stop)
        class Engine:
            def __init__(self):
                self.entered, self.closed = asyncio.Event(), asyncio.Event()
                self.calls = 0
                self.gate = asyncio.Lock()
            async def reply(self, payload, context):
                async with self.gate:
                    self.calls += 1
                    if self.calls == 1:
                        self.entered.set()
                        try:
                            await asyncio.Event().wait()
                        finally:
                            self.closed.set()
                    return 'Recovered'
        self.engine = Engine()
        root = Path(self.tmp.name)
        # Distinct application instances, one shared persistent database.
        apps = [create_app(root/'db.sqlite', Store(root/'sources', {}), self.engine) for _ in range(2)]
        self.clients = [httpx.AsyncClient(transport=httpx.ASGITransport(app=a), base_url='http://testserver',
                        headers={'X-Preview-Actor':'enterprise-general'}) for a in apps]
        for client in self.clients:
            self.addAsyncCleanup(client.aclose)

    async def test_other_instance_cancels_only_own_request_and_recovers(self):
        a,b = self.clients
        rid = str(uuid4()); body={'question':'Explain the unusual project detail','request_id':rid}
        pending = asyncio.create_task(a.post('/api/assistant/chat',json=body))
        try:
            await asyncio.wait_for(self.engine.entered.wait(),3)
            for actor in ('enterprise-admin','core-general'):
                forbidden = await b.post(f'/api/assistant/requests/{rid}/cancel',headers={'X-Preview-Actor':actor})
                self.assertEqual(forbidden.status_code,404)
            result = await b.post(f'/api/assistant/requests/{rid}/cancel')
            self.assertEqual(result.json()['state'],'cancel_requested')
            self.assertFalse(result.json()['provider_stop_verified'])
            response = await asyncio.wait_for(pending,3)
            self.assertEqual(response.status_code,499)
            self.assertTrue(self.engine.closed.is_set())
            self.assertFalse(self.engine.gate.locked())
            status = await b.get(f'/api/assistant/requests/{rid}')
            self.assertEqual(status.json()['state'],'cancelled')
            recovered = await a.post('/api/assistant/chat',json={**body,'request_id':str(uuid4())})
            self.assertEqual(recovered.status_code,200)
            self.assertEqual(recovered.json()['answer'],'Recovered')
            duplicate = await a.post('/api/assistant/chat',json=body)
            self.assertEqual(duplicate.status_code,409)
            self.assertEqual(self.engine.calls,2)
        finally:
            pending.cancel()
            await asyncio.gather(pending,return_exceptions=True)

    async def test_cancel_before_start_is_idempotent_and_does_not_invoke_model(self):
        a,b = self.clients;rid=str(uuid4())
        for _ in range(2):
            self.assertEqual((await b.post(f'/api/assistant/requests/{rid}/cancel')).status_code,200)
        response=await a.post('/api/assistant/chat',json={'question':'An unusual detail','request_id':rid})
        self.assertEqual(response.status_code,499)
        self.assertEqual(self.engine.calls,0)
        self.assertEqual((await b.get('/api/assistant/requests/not-a-uuid')).status_code,422)

    async def test_unknown_status_and_cross_origin_denied(self):
        client=self.clients[0];rid=str(uuid4())
        self.assertEqual((await client.get(f'/api/assistant/requests/{rid}')).status_code,404)
        self.assertEqual((await client.post(f'/api/assistant/requests/{rid}/cancel',headers={'Origin':'https://other.example'})).status_code,403)

    async def test_timeout_closes_task_and_marks_failure(self):
        from services.workspace_preview.atlas_requests import AtlasRequests
        rid=str(uuid4())
        with patch.object(AtlasRequests,'deadline',0.1):
            response=await self.clients[0].post('/api/assistant/chat',json={'question':'An unusual detail','request_id':rid})
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json()['code'],'timeout')
        self.assertTrue(self.engine.closed.is_set())
        self.assertFalse(self.engine.gate.locked())
        self.assertEqual((await self.clients[1].get(f'/api/assistant/requests/{rid}')).json()['state'],'failed')

    async def test_provider_failure_is_terminal_and_cancel_does_not_rewrite_it(self):
        from services.workspace_preview.intelligence import ModelUnavailable
        from unittest.mock import AsyncMock
        rid=str(uuid4());self.engine.reply=AsyncMock(side_effect=ModelUnavailable('Unavailable',code='provider_error'))
        response=await self.clients[0].post('/api/assistant/chat',json={'question':'An unusual detail','request_id':rid})
        self.assertEqual(response.status_code,503)
        self.assertEqual((await self.clients[1].post(f'/api/assistant/requests/{rid}/cancel')).json()['state'],'failed')
