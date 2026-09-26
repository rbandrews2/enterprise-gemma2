import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.workspace_preview.intelligence import ChatInput, LocalIntelligence, ModelUnavailable, configured_intelligence
from services.workspace_preview.cloud_intelligence import CloudRunIntelligence, metadata_identity_token, service_url
from services.v2.knowledge.store import Store

ORIGIN='https://wzos-inference-example.us-central1.run.app'
TOKEN='synthetic.service.identity'
ENV={'WZOS_ATLAS_PROVIDER':'cloud_run','WZOS_ATLAS_CLOUD_ENABLED':'1','WZOS_ATLAS_CLOUD_RUN_URL':ORIGIN,
     'WZOS_ATLAS_MODEL':'gemma3:4b','WZOS_WORKSPACE_PREVIEW':'1','K_SERVICE':'','GAE_ENV':'','NETLIFY':''}

class CloudIntelligenceTests(unittest.TestCase):
    def test_origin_validation_and_explicit_enablement(self):
        self.assertEqual(service_url(ORIGIN+'/'),ORIGIN)
        for invalid in ('http://example.run.app','https://evil.test','https://example.run.app.evil.test',
                        'https://name:secret@example.run.app',ORIGIN+'/api/chat',ORIGIN+'?key=x',ORIGIN+'#x',
                        ORIGIN+':443','https://tag---service.run.app','http://127.0.0.1:11435',' '+ORIGIN):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError): service_url(invalid)
        with patch.dict(os.environ,{**ENV,'WZOS_ATLAS_CLOUD_ENABLED':'0'}):
            with self.assertRaises(ValueError): configured_intelligence()
        with patch.dict(os.environ,{**ENV,'WZOS_ATLAS_PROVIDER':'local'}):
            self.assertIsInstance(configured_intelligence(),LocalIntelligence)
        with patch.dict(os.environ,{**ENV,'WZOS_ATLAS_PROVIDER':'unknown'}):
            with self.assertRaises(ValueError): configured_intelligence()

    def test_metadata_is_bounded_and_unavailable_outside_cloud(self):
        async def check():
            captured=[]
            def transport(request):
                captured.append(request)
                return httpx.Response(200,headers={'Metadata-Flavor':'Google'},text=TOKEN)
            with patch.dict(os.environ,{'K_SERVICE':''}):
                with self.assertRaises(ModelUnavailable): await metadata_identity_token(ORIGIN,httpx.MockTransport(transport))
            self.assertEqual(captured,[])
            with patch.dict(os.environ,{'K_SERVICE':'synthetic-test-only'}):
                self.assertEqual(await metadata_identity_token(ORIGIN,httpx.MockTransport(transport)),TOKEN)
                request=captured[0]
                self.assertEqual(request.url.host,'metadata.google.internal')
                self.assertEqual(request.url.params['audience'],ORIGIN)
                self.assertEqual(request.headers['Metadata-Flavor'],'Google')
                for response in (httpx.Response(302,headers={'Location':'https://untrusted.example'}),
                                 httpx.Response(200,text=TOKEN),httpx.Response(200,headers={'Metadata-Flavor':'Google'},text='x'*20000),
                                 httpx.Response(200,headers={'Metadata-Flavor':'Google'},text='not-an-id-token'),httpx.Response(503)):
                    with self.assertRaises(ModelUnavailable) as caught:
                        await metadata_identity_token(ORIGIN,httpx.MockTransport(lambda req:response))
                    self.assertNotIn(TOKEN,str(caught.exception))
        asyncio.run(check())

    def test_private_transport_targets_exact_origin_and_never_follows_redirect(self):
        async def check():
            audiences=[]; calls=[]
            async def token_provider(audience):
                audiences.append(audience); return TOKEN
            def transport(request):
                calls.append(request)
                self.assertEqual(str(request.url).split('/api')[0],ORIGIN)
                self.assertEqual(request.headers['Authorization'],'Bearer '+TOKEN)
                if request.url.path=='/api/tags':
                    return httpx.Response(200,json={'models':[{'name':'gemma3:4b'}]})
                self.assertEqual(json.loads(request.content)['model'],'gemma3:4b')
                return httpx.Response(200,json={'done':True,'message':{'content':'Synthetic transport response.'}})
            engine=CloudRunIntelligence(httpx.MockTransport(transport),token_provider)
            self.assertTrue(await engine.ready())
            self.assertEqual(await engine.reply(ChatInput(question='Explain a useful follow-up.'),{'role':'member','edition':'core'}),'Synthetic transport response.')
            self.assertEqual(audiences,[ORIGIN,ORIGIN]); self.assertEqual(len(calls),2)
            redirects=[]
            def redirect(request):
                redirects.append(request)
                return httpx.Response(307,headers={'Location':'https://untrusted.example/collect'})
            engine=CloudRunIntelligence(httpx.MockTransport(redirect),token_provider)
            with self.assertRaises(ModelUnavailable): await engine.reply(ChatInput(question='Explain.'),{})
            self.assertEqual(len(redirects),1)
            self.assertFalse(engine.gate.locked())
            with patch.dict(os.environ,{'WZOS_ATLAS_CLOUD_ENABLED':'0'}):
                self.assertFalse(await engine.ready())
                with self.assertRaises(ModelUnavailable): await engine.reply(ChatInput(question='Explain.'),{})
            self.assertEqual(len(redirects),1)
        with patch.dict(os.environ,ENV): asyncio.run(check())

    def test_identity_failure_never_calls_model(self):
        async def check():
            calls=[]
            async def no_token(audience): raise ModelUnavailable('Service identity unavailable')
            engine=CloudRunIntelligence(httpx.MockTransport(lambda request:calls.append(request)),no_token)
            self.assertFalse(await engine.ready())
            with self.assertRaises(ModelUnavailable): await engine.reply(ChatInput(question='Explain.'),{})
            self.assertEqual(calls,[]); self.assertFalse(engine.gate.locked())
        with patch.dict(os.environ,ENV): asyncio.run(check())

    def test_account_scope_checks_precede_service_identity_and_inference(self):
        calls=[]; audiences=[]
        async def token_provider(audience): audiences.append(audience);return TOKEN
        def transport(request):
            calls.append(request)
            return httpx.Response(200,json={'done':True,'message':{'content':'Synthetic authorized response.'}})
        with patch.dict(os.environ,ENV),tempfile.TemporaryDirectory() as directory:
            engine=CloudRunIntelligence(httpx.MockTransport(transport),token_provider)
            with TestClient(create_app(Path(directory)/'test.sqlite',Store(Path(directory)/'sources',{}),engine)) as client:
                url='/api/assistant/chat'; body={'question':'Explain a useful follow-up.','order_id':'core-sample','expected_version':1}
                self.assertEqual(client.post(url,json=body).status_code,401)
                self.assertEqual(client.post(url,json=body,headers={'X-Preview-Actor':'enterprise-admin'}).status_code,404)
                self.assertEqual(client.post(url,json={**body,'expected_version':2},headers={'X-Preview-Actor':'core-general'}).status_code,409)
                self.assertEqual(client.post(url,json={**body,'page':'report'},headers={'X-Preview-Actor':'core-general'}).status_code,403)
                self.assertEqual(audiences,[]);self.assertEqual(calls,[])
                guide=client.post(url,json={'question':'Does changing study status issue a certificate?'},headers={'X-Preview-Actor':'core-general'}).json()
                self.assertFalse(guide['model_called']);self.assertEqual(audiences,[])
                response=client.post(url,json=body,headers={'X-Preview-Actor':'core-general','Authorization':'Bearer caller-not-forwarded'})
                self.assertEqual(response.status_code,200,response.text)
                self.assertTrue(response.json()['model_called']);self.assertEqual(len(calls),1)
                self.assertNotIn('caller-not-forwarded',str(calls[0].headers))
