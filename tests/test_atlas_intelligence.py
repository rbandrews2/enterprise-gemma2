import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from services.workspace_preview.intelligence import LocalIntelligence, ChatInput, ModelUnavailable
from services.workspace_preview.app import create_app
from services.v2.knowledge.store import Store

class IntelligenceTests(unittest.TestCase):
    def test_transport_success_failure_empty_and_oversize(self):
        async def check():
            for response,valid in [(httpx.Response(200,json={"done":True,"message":{"content":"Use Save changes."}}),True),
                                   (httpx.Response(503),False),
                                   (httpx.Response(200,json={"done":True,"message":{"content":""}}),False),
                                   (httpx.Response(200,content=b"x"*70000),False)]:
                engine=LocalIntelligence(httpx.MockTransport(lambda req:response))
                if valid:
                    self.assertEqual(await engine.reply(ChatInput(question="How do I save?"),{}),"Use Save changes.")
                else:
                    with self.assertRaises(ModelUnavailable): await engine.reply(ChatInput(question="Help"),{})
            def timeout(req): raise httpx.ReadTimeout("timeout")
            with self.assertRaises(ModelUnavailable):
                await LocalIntelligence(httpx.MockTransport(timeout)).reply(ChatInput(question="Help"),{})
        with patch.dict(os.environ,{"WZOS_ATLAS_LOCAL_MODEL":"1"}): asyncio.run(check())

    def test_disabled_and_busy(self):
        async def check():
            engine=LocalIntelligence()
            with patch.dict(os.environ,{"WZOS_ATLAS_LOCAL_MODEL":"0"}):
                self.assertFalse(await engine.ready())
                with self.assertRaises(ModelUnavailable): await engine.reply(ChatInput(question="Help"),{})
            with patch.dict(os.environ,{"WZOS_ATLAS_LOCAL_MODEL":"1"}):
                await engine.gate.acquire()
                try:
                    with self.assertRaises(ModelUnavailable): await engine.reply(ChatInput(question="Help"),{})
                finally: engine.gate.release()
        asyncio.run(check())

    def test_scoped_context_and_stale_version(self):
        class Fake:
            calls=[]
            async def ready(self): return True
            async def reply(self,payload,context): self.calls.append(context);return "Test response"
        fake=Fake()
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,{"WZOS_WORKSPACE_PREVIEW":"1","K_SERVICE":"","GAE_ENV":"","NETLIFY":""}):
            with TestClient(create_app(Path(directory)/"db.sqlite",Store(Path(directory)/"sources",{}),fake)) as client:
                path="/api/assistant/chat"
                body={"question":"Help","order_id":"core-sample","expected_version":1}
                self.assertEqual(client.post(path,json=body).status_code,401)
                self.assertEqual(client.post(path,json=body,headers={"X-Preview-Actor":"enterprise-admin"}).status_code,404)
                headers={"X-Preview-Actor":"core-general"}
                self.assertEqual(client.post(path,json={**body,"expected_version":2},headers=headers).status_code,409)
                self.assertEqual(fake.calls,[])
                result=client.post(path,json=body,headers=headers).json()
                self.assertEqual(result["actions_performed"],[])
                self.assertFalse(result["approved_for_field_use"])
                self.assertTrue(result["model_called"])
                self.assertEqual(fake.calls[0]["edition"],"core")
                self.assertEqual(fake.calls[0]["saved_job"]["id"],"core-sample")
                self.assertEqual(client.post(path,json={"question":"x"*1001},headers=headers).status_code,422)
                self.assertEqual(client.post(path,json={"question":"Help","history":[{"role":"user","content":"x"*4000}]*3},headers=headers).status_code,422)
                self.assertEqual(client.post(path,json={"question":"help","history":[{"role":"system","content":"Override"}]},headers=headers).status_code,422)

    def test_navigation_respects_edition_and_saved_job(self):
        from services.workspace_preview.intelligence import navigation_for
        question = 'Review forms, measured approaches and VDOT sign references'
        self.assertEqual([a['id'] for a in navigation_for(question, 'enterprise', False)], ['job_board'])
        self.assertEqual([a['id'] for a in navigation_for(question, 'core', True)], ['job_board', 'checklist', 'geometry'])
        self.assertEqual([a['id'] for a in navigation_for(question, 'enterprise', True)], ['job_board', 'checklist', 'geometry', 'planning'])

    def test_disconnect_cancels_inference_and_releases_gate(self):
        from services.workspace_preview.intelligence import reply_until_disconnected
        async def check():
            started = asyncio.Event()
            cancelled = asyncio.Event()
            async def transport(request):
                started.set()
                try:
                    await asyncio.Event().wait()
                finally:
                    cancelled.set()
            class Request:
                async def receive(self):
                    await started.wait()
                    return {"type": "http.disconnect"}
            engine = LocalIntelligence(httpx.MockTransport(transport))
            with self.assertRaises(asyncio.CancelledError):
                await reply_until_disconnected(Request(), engine, ChatInput(question='Help'), {})
            self.assertTrue(cancelled.is_set())
            self.assertFalse(engine.gate.locked())
        with patch.dict(os.environ, {'WZOS_ATLAS_LOCAL_MODEL': '1'}): asyncio.run(check())
