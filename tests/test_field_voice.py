import asyncio
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4
import wave

import httpx
from fastapi.testclient import TestClient
from services.v2.knowledge.store import Store
from services.workspace_preview.app import create_app
from services.workspace_preview.files import LocalFiles
from services.workspace_preview.storage import SQLiteStorage
from services.workspace_preview.field_voice import Report
from services.workspace_preview.field_voice_transport import Speech, Extractor, validate_audio
from services.workspace_preview.intelligence import ModelUnavailable


def audio(seconds=1):
    data = io.BytesIO()
    with wave.open(data, 'wb') as stream:
        stream.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
        stream.writeframes(b'\0\0' * int(seconds*16000))
    return data.getvalue()


def report():
    return {'is_relevant': True, 'work_description': 'Right lane closure finished.',
        'route_location': 'Route 29', 'production_quantities': [
            {'item_name': 'Traffic drums', 'quantity': 50, 'unit': 'each'},
            {'item_name': 'Arrow boards', 'quantity': 4, 'unit': 'each'}],
        'incidents': [{'details': 'Passing car clipped a cone and left.', 'time_mentioned': '9:15 AM', 'priority': None}],
        'unresolved': ['Confirm incident priority and time.']}


class FieldVoiceTests(unittest.TestCase):
    def make_storage(self, root):
        return SQLiteStorage(root/'voice.sqlite')

    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup); self.root = Path(temp.name)
        env = patch.dict(os.environ, {'WZOS_ACCOUNT_WORKSPACE': '1', 'K_SERVICE': '', 'GAE_ENV': '',
            'WZOS_FIELD_VOICE_ENABLED': '1', 'WZOS_FIELD_VOICE_SPEECH_ENABLED': '1'})
        env.start(); self.addCleanup(env.stop)
        self.storage = self.make_storage(self.root)
        claims = {u: {'uid': u, 'name': u.title(), 'email': u+'@example.test', 'email_verified': True}
                  for u in ('admin', 'member', 'other', 'core')}
        self.app = create_app(self.root/'unused', Store(self.root/'sources', {}),
            account_workspace=True, storage=self.storage, verifier=lambda t: claims[t], file_store=LocalFiles(self.root/'files'))
        self.client = TestClient(self.app); self.addCleanup(self.client.close)
        self.org = self.organization('admin'); self.other = self.organization('other'); self.core = self.organization('core', 'core')
        invitation = self.client.post('/api/account/invitations', headers=self.h('admin'), json={'email': 'member@example.test', 'role': 'member'})
        self.assertEqual(invitation.status_code, 200, invitation.text)
        self.assertEqual(self.client.post('/api/account/join', headers=self.h('member'), json={'token': invitation.json()['token']}).status_code, 200)
        response = self.client.post('/api/orders', headers=self.h(), json={'request_id': str(uuid4()),
            'title': 'Synthetic field report', 'address': 'Route 29', 'locality': 'Norfolk', 'work_type': 'road_maintenance'})
        self.assertEqual(response.status_code, 201, response.text); self.job = response.json()['id']
        self.basis = {'job_id': self.job, 'expected_job_version': 1}
        self.calls = []
        parent = self
        class Fake:
            async def extract(self, transcript, job, schema):
                parent.calls.append(job['id']); return report()
        self.app.state.field_voice_extractor = Fake()

    def h(self, who='member', org=None):
        return {'Authorization': 'Bearer '+who, 'X-WZOS-Organization': org or self.org}

    def organization(self, who, edition='enterprise'):
        code = self.app.state.accounts.issue_activation(edition)
        response = self.client.post('/api/account/organizations', headers={'Authorization': 'Bearer '+who},
            json={'name': 'Synthetic '+who, 'activation_code': code})
        self.assertEqual(response.status_code, 200, response.text); return response.json()['id']

    def create(self, fields=None):
        response = self.client.post('/api/field-voice/drafts', headers=self.h(), json={
            **self.basis, 'request_id': str(uuid4()), 'fields': fields or {'work_date': '2026-10-18', 'report': report()}})
        self.assertEqual(response.status_code, 200, response.text); return response.json()

    def test_draft_review_atomic_send_retry_no_sms_and_no_raw_transcript(self):
        secret = 'PRIVATE TRANSCRIPT ONLY - '+str(uuid4())
        response = self.client.post('/api/field-voice/extract', headers=self.h(), json={**self.basis, 'transcript': secret})
        self.assertEqual(response.status_code, 200, response.text)
        draft = self.create(); endpoint='/api/field-voice/drafts/'+draft['id']+'/send-to-office'
        self.assertEqual(self.client.post(endpoint, headers=self.h(), json={'expected_version': 1, 'reviewed': False}).status_code, 422)
        result = self.client.post(endpoint, headers=self.h(), json={'expected_version': 1, 'reviewed': True})
        self.assertEqual(result.status_code, 200, result.text); self.assertEqual(len(result.json()['submission_ids']), 2)
        self.assertEqual(self.client.post(endpoint, headers=self.h(), json={'expected_version': 1, 'reviewed': True}).json(), result.json())
        with self.storage.connect() as db:
            snapshots = db.execute('SELECT payload FROM form_submissions').fetchall()
            self.assertEqual(len(snapshots), 2)
            self.assertNotIn(secret, str([dict(r) for r in db.execute('SELECT * FROM field_voice_drafts').fetchall()]))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM sms_outbox').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM fixture_messages').fetchone()[0], 1)
        daily = json.loads(snapshots[0]['payload'])
        self.assertTrue(any(json.loads(r['payload'])['template_id']=='daily-work-report' for r in snapshots))
        self.assertEqual(daily['field_voice_review']['reviewed_by'], 'member')

    def test_edition_tenant_owner_stale_denials_before_inference(self):
        body = {**self.basis, 'transcript': 'Synthetic road work completed.'}
        for headers, payload, expected in [(self.h('core', self.core), body, 403),
                (self.h('other', self.other), body, 404), (self.h(), {**body, 'expected_job_version': 99}, 409)]:
            response=self.client.post('/api/field-voice/extract', headers=headers, json=payload)
            self.assertEqual(response.status_code, expected, response.text)
        self.assertEqual(self.calls, [])
        core_templates=self.client.get('/api/forms/templates',headers=self.h('core',self.core)).json()['items']
        self.assertNotIn('daily-work-report',[t['id'] for t in core_templates])
        self.assertEqual(self.client.get('/api/forms/templates/daily-work-report/1',headers=self.h('core',self.core)).status_code,404)
        draft=self.create()
        self.assertEqual(self.client.get('/api/field-voice/drafts/'+draft['id'],headers=self.h('other',self.other)).status_code,404)
        with patch.dict(os.environ, {'WZOS_FIELD_VOICE_ENABLED':'0'}):
            self.assertFalse(self.client.get('/api/field-voice/config',headers=self.h()).json()['enabled'])
            self.assertEqual(self.client.get('/api/field-voice/jobs',headers=self.h()).status_code,503)

    def test_draft_version_conflicts_and_unresolved_quantities_cannot_send(self):
        data={'work_date':'2026-10-18','report':report()};data['report']['production_quantities'][0]['quantity']=None
        draft=self.create(data);path='/api/field-voice/drafts/'+draft['id']
        self.assertEqual(self.client.post(path+'/send-to-office',headers=self.h(),json={'expected_version':1,'reviewed':True}).status_code,422)
        self.assertEqual(self.client.patch(path,headers=self.h(),json={'expected_version':99,'fields':data}).status_code,409)
        with self.storage.connect() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM form_submissions').fetchone()[0],0)

    def test_irrelevant_and_invalid_model_output_never_save(self):
        class Fake:
            result={'is_relevant':False}
            async def extract(self,*args):return self.result
        fake=Fake();self.app.state.field_voice_extractor=fake
        for result, status in [({'is_relevant':False},422),({'is_relevant':True,'tool_calls':['send_sms']},503)]:
            fake.result=result
            response=self.client.post('/api/field-voice/extract',headers=self.h(),json={**self.basis,'transcript':'Order a sandwich for me.'})
            self.assertEqual(response.status_code,status,response.text)
        with self.storage.connect() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM field_voice_drafts').fetchone()[0],0)

    def test_assignment_access_uses_delivered_snapshot_and_revocation_blocks(self):
        with self.storage.connect() as db:
            db.execute('UPDATE preview_orders SET owner_id=? WHERE id=?',('admin',self.job))
            plan,assignment=str(uuid4()),str(uuid4())
            db.execute('INSERT INTO dispatch_plans VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                (plan,self.org,self.job,'sent',1,json.dumps({'delivery_snapshot':{'order_title':'Delivered title','address':'Route 29'}}),'admin','now','now','admin','now',str(uuid4())))
            db.execute('INSERT INTO dispatch_assignments VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (assignment,self.org,plan,self.job,'member','role','accepted','now','later',None,None,'','now','now'))
        response=self.client.get('/api/field-voice/jobs',headers=self.h());self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['items'][0]['title'],'Delivered title')
        with self.storage.connect() as db:db.execute("UPDATE dispatch_assignments SET status='cancelled' WHERE id=?",(assignment,))
        self.assertEqual(self.client.post('/api/field-voice/extract',headers=self.h(),json={**self.basis,'transcript':'Road work done.'}).status_code,404)

    def test_partial_receipt_failure_rolls_back_bundle_and_notifications(self):
        from fastapi import HTTPException
        from services.workspace_preview.field_voice import printable_snapshot
        draft=self.create(); count=0
        def fail_second(*args):
            nonlocal count
            count+=1
            if count==2:raise HTTPException(422,'Synthetic receipt validation failure')
            return printable_snapshot(*args)
        with patch('services.workspace_preview.field_voice.printable_snapshot',side_effect=fail_second):
            result=self.client.post('/api/field-voice/drafts/'+draft['id']+'/send-to-office',headers=self.h(),json={'expected_version':1,'reviewed':True})
        self.assertEqual(result.status_code,422,result.text)
        with self.storage.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM form_submissions').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM fixture_messages').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT state FROM field_voice_drafts WHERE id=?',(draft['id'],)).fetchone()[0],'draft')


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'), 'Dedicated PostgreSQL database not configured')
class PostgreSQLFieldVoiceTests(FieldVoiceTests):
    def make_storage(self,root):
        from psycopg.conninfo import make_conninfo
        from services.workspace_preview.postgres import PostgreSQLStorage
        dsn=os.environ['WZOS_TEST_DATABASE_URL'];schema='test_'+uuid4().hex
        base=PostgreSQLStorage(dsn);self.addCleanup(base.close)
        with base.connect() as db:db.execute('CREATE SCHEMA '+schema)
        def cleanup():
            with base.connect() as db:db.execute('DROP SCHEMA '+schema+' CASCADE')
        self.addCleanup(cleanup)
        storage=PostgreSQLStorage(make_conninfo(dsn,options='-c search_path='+schema));self.addCleanup(storage.close);storage.initialize();return storage


class VoiceTransportTests(unittest.TestCase):
    def test_wav_duration_format_and_truncation(self):
        validate_audio(audio(30))
        for value in [audio(31),audio()[:-3],b'not audio',b'x'*(6*1024*1024+1)]:
            with self.assertRaises(ValueError):validate_audio(value)

    def test_structured_extraction_private_auth_no_tools_and_fail_closed(self):
        calls=[]
        async def token(audience):self.assertEqual(audience,'https://synthetic-atlas.run.app');return 'test.identity.token'
        def handle(request):
            body=json.loads(request.content);calls.append(body)
            self.assertEqual(body['response_format']['type'],'json_schema');self.assertNotIn('tools',body)
            self.assertEqual(request.headers['Authorization'],'Bearer test.identity.token')
            return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':json.dumps(report())}}]})
        with patch.dict(os.environ,{'WZOS_ATLAS_VLLM_ENABLED':'1','WZOS_ATLAS_VLLM_URL':'https://synthetic-atlas.run.app'}):
            engine=Extractor(httpx.MockTransport(handle),token)
            self.assertTrue(asyncio.run(engine.extract('Synthetic traffic work.',{},Report.model_json_schema()))['is_relevant'])
            self.assertEqual(len(calls),1)
            failing=Extractor(httpx.MockTransport(lambda _:httpx.Response(400,text='PRIVATE PROVIDER ERROR')),token)
            with self.assertRaises(ModelUnavailable) as error:asyncio.run(failing.extract('Synthetic road work.',{},Report.model_json_schema()))
            self.assertNotIn('PRIVATE',str(error.exception))

    def test_speech_uses_us_inline_audio_without_storage(self):
        async def token():return 'synthetic-token'
        def handle(request):
            self.assertIn('us-speech.googleapis.com',str(request.url));self.assertNotIn('uri',json.loads(request.content))
            return httpx.Response(200,json={'results':[{'alternatives':[{'transcript':'Used 50 drums.'}]}]})
        with patch.dict(os.environ,{'WZOS_FIELD_VOICE_SPEECH_ENABLED':'1'}):
            self.assertEqual(asyncio.run(Speech(httpx.MockTransport(handle),token).transcribe(audio())),'Used 50 drums.')
