import json
import os
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.workspace_preview.daily_meetings import DailyProvider, frame_origins
from services.workspace_preview.storage import SQLiteStorage
from services.v2.knowledge.store import Store


class FakeDaily:
    enabled = True
    origin = 'https://synthetic.daily.co'
    def __init__(self):
        self.rooms = {}; self.creations = 0; self.closed = []; self.users = []
        self.fail_close = False; self.after_token = lambda: None
    def room(self, name, end, create=False, starts_at=0):
        if name not in self.rooms:
            if not create: raise HTTPException(409, 'Admin must start')
            self.rooms[name] = end; self.creations += 1
        if self.rooms[name] != end: raise HTTPException(502, 'Expired')
    def token(self, name, user, end):
        self.users.append(user); self.after_token(); return 'synthetic-token-not-a-real-credential'
    def close(self, name):
        if self.fail_close: raise HTTPException(502, 'Provider unavailable')
        self.closed.append(name); self.rooms[name] = 0


class DailyMeetingTests(unittest.TestCase):
    def make_storage(self, root): return SQLiteStorage(root/'db')
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup); root=Path(tmp.name)
        env=patch.dict(os.environ, {'WZOS_WORKSPACE_PREVIEW':'1'});env.start();self.addCleanup(env.stop)
        self.provider=FakeDaily(); self.storage=self.make_storage(root)
        with patch('services.workspace_preview.daily_meetings.DailyProvider',return_value=self.provider):
            self.app=create_app(root/'unused',Store(root/'sources',{}),storage=self.storage)
        self.client=TestClient(self.app);self.addCleanup(self.client.close)
        self.id=str(uuid4());now=datetime.now(timezone.utc)
        self.body={'request_id':self.id,'title':'Synthetic meeting','start':(now-timedelta(minutes=1)).isoformat(),
                   'end':(now+timedelta(minutes=20)).isoformat(),'meeting_provider':'daily'}
        self.assertEqual(self.save().status_code,200)
    def h(self,user='enterprise-admin'):return {'X-Preview-Actor':user}
    def save(self,body=None,user='enterprise-admin',record=None,kind='schedule'):
        return self.client.put('/api/modules/'+kind+'/'+(record or self.id),headers=self.h(user),json=body or self.body)
    def post(self,action,user='enterprise-admin',record=None):
        return self.client.post('/api/meetings/'+(record or self.id)+'/'+action,headers=self.h(user))
    def test_admin_prepares_member_joins_and_duplicate_has_one_room(self):
        self.assertEqual(self.post('prepare','enterprise-general').status_code,403)
        self.assertEqual(self.post('join','enterprise-general').status_code,409)
        self.assertEqual(self.post('prepare').status_code,200)
        self.assertEqual(self.post('prepare').status_code,200)
        self.assertEqual(self.provider.creations,1)
        joined=self.post('join','enterprise-general');self.assertEqual(joined.status_code,200,joined.text)
        self.assertEqual(self.provider.users[-1]['role'],'member')
        self.assertIn('/wzos-',joined.json()['url']);self.assertNotIn('token=',joined.json()['url'])
    def test_tenant_assignment_core_and_auth_boundaries(self):
        self.assertEqual(self.post('prepare','core-admin').status_code,403)
        self.assertEqual(self.client.get('/api/meetings/config').status_code,401)
        self.assertEqual(self.save({**self.body,'assignees':['enterprise-admin'],'expected_version':1}).status_code,200)
        self.assertEqual(self.post('prepare').status_code,200)
        self.assertEqual(self.post('join','enterprise-general').status_code,404)
        self.assertEqual(self.save(self.body,'core-admin').status_code,200)
        self.assertEqual(self.post('prepare','core-admin').status_code,403)
        self.assertEqual(self.provider.creations,1)
        self.assertEqual(len(set(self.provider.rooms)),1)
    def test_filter_and_duration_validation(self):
        listed=self.client.get('/api/modules/schedule?meetings_only=true&limit=1',headers=self.h()).json()
        self.assertEqual(listed['total'],1);self.assertEqual(listed['items'][0]['meeting_provider'],'daily')
        self.assertEqual(self.client.get('/api/modules/schedule?meetings_only=true&offset=1',headers=self.h()).json()['items'],[])
        end=datetime.fromisoformat(self.body['start'])+timedelta(hours=2)
        self.assertEqual(self.save({**self.body,'end':end.isoformat()}).status_code,422)
        self.assertEqual(self.save({**self.body,'meeting_url':'https://meet.google.com/abc-defg-hij'}).status_code,422)
        self.assertEqual(self.save(kind='forms').status_code,422)
    def test_schedule_edit_closes_room_but_same_id_form_does_not(self):
        self.assertEqual(self.post('prepare').status_code,200)
        form={'request_id':self.id,'title':'Independent form'}
        self.assertEqual(self.save(form,kind='forms').status_code,200)
        self.assertEqual(self.save({**form,'details':'Changed','expected_version':1},kind='forms').status_code,200)
        self.assertEqual(self.provider.closed,[])
        self.assertEqual(self.save({**self.body,'status':'cancelled','expected_version':1}).status_code,200)
        self.assertEqual(len(self.provider.closed),1)
        self.assertEqual(self.post('join').status_code,409)
    def test_provider_cancel_failure_keeps_schedule_unchanged(self):
        self.post('prepare');self.provider.fail_close=True
        self.assertEqual(self.save({**self.body,'status':'cancelled','expected_version':1}).status_code,502)
        rows=self.client.get('/api/modules/schedule',headers=self.h()).json()['items']
        self.assertEqual(rows[0]['status'],'draft');self.assertEqual(rows[0]['version'],1)
    def test_access_changed_while_token_minted_is_discarded(self):
        self.post('prepare')
        def change():
            with self.storage.connect() as db:
                db.execute("UPDATE daily_meeting_rooms SET state='closed' WHERE record_id=?",(self.id,))
        self.provider.after_token=change
        r=self.post('join');self.assertEqual(r.status_code,409);self.assertNotIn('token',r.json())
    def test_rate_limit_and_future_meeting(self):
        for _ in range(6):self.assertEqual(self.post('prepare').status_code,200)
        self.assertEqual(self.post('prepare').status_code,429)
        now=datetime.now(timezone.utc)+timedelta(hours=2)
        future=str(uuid4())
        self.save({**self.body,'request_id':future,'start':now.isoformat(),'end':(now+timedelta(minutes=30)).isoformat()},record=future)
        with patch('services.workspace_preview.daily_meetings.time.monotonic',return_value=time.monotonic()+120):
            self.assertEqual(self.post('prepare',record=future).status_code,409)
    def test_config_and_exact_frame_origin(self):
        config=self.client.get('/api/meetings/config',headers=self.h()).json()
        self.assertEqual(config['daily_origin'],self.provider.origin)
        response=self.client.get('/');csp=response.headers['content-security-policy']
        self.assertIn('frame-src https://synthetic.daily.co',csp)
        self.assertNotIn('*.daily.co',csp)
        expected = frame_origins(self.provider.origin)
        self.assertEqual(expected, ('https://synthetic.daily.co', 'https://synthetic.dailywebrtc.com', 'https://synthetic.dailywebrtc.net'))
        for origin in expected:
            self.assertIn(origin, csp)
            self.assertIn('"' + origin + '"', response.headers['permissions-policy'])
        self.assertNotIn('*.dailywebrtc', csp)
        self.assertNotIn('other.dailywebrtc.com', csp)
        self.assertEqual(frame_origins('https://synthetic.daily.co.evil.example'), ())
        self.assertEqual(frame_origins('http://synthetic.daily.co'), ())


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'),'Dedicated PostgreSQL database not configured')
class PostgreSQLDailyMeetingTests(DailyMeetingTests):
    def make_storage(self,root):
        from tests.test_form_submissions import PostgreSQLFormSubmissionTests
        return PostgreSQLFormSubmissionTests.make_storage(self,root)


class DailyProviderTests(unittest.TestCase):
    def provider(self,handler):
        with patch.dict(os.environ,{'WZOS_DAILY_API_KEY':'synthetic-server-key','WZOS_DAILY_DOMAIN':'synthetic.daily.co','WZOS_DAILY_ENABLED':'1'}):
            return DailyProvider(httpx.MockTransport(handler))
    def test_room_and_token_properties_no_recording(self):
        calls=[];end=int(time.time())+1200;name='wzos-'+'a'*40
        def handler(r):
            calls.append(r)
            if r.method=='GET':return httpx.Response(404)
            body=json.loads(r.content)
            if r.url.path.endswith('meeting-tokens'):return httpx.Response(200,json={'token':'synthetic-authorization-token'})
            return httpx.Response(200,json={'name':name,'privacy':'private','url':'https://synthetic.daily.co/'+name,'config':body['properties']})
        provider=self.provider(handler);provider.room(name,end,True,int(time.time())-10)
        provider.token(name,{'organization_id':'org','id':'member','role':'member'},end)
        body=json.loads(calls[-1].content)['properties']
        self.assertFalse(body['is_owner']);self.assertFalse(body['start_cloud_recording'])
        self.assertFalse(body['auto_start_transcription']);self.assertLessEqual(body['exp'],int(time.time())+300)
        self.assertEqual(json.loads(calls[1].content)['properties']['max_participants'],10)
    def test_redirect_errors_oversize_and_wrong_room_fail_closed(self):
        for response in [httpx.Response(302,headers={'Location':'https://evil.test'}),httpx.Response(500,json={'secret':'never expose'}),httpx.Response(200,content=b'a'*65537),httpx.Response(200,json={})]:
            with self.subTest(status=response.status_code):
                provider=self.provider(lambda r:response)
                with self.assertRaises(HTTPException) as caught:provider.room('name',100)
                self.assertEqual(caught.exception.status_code,502)
                self.assertNotIn('secret',str(caught.exception.detail))
    def test_invalid_domain_and_unconfigured_disabled(self):
        with patch.dict(os.environ,{'WZOS_DAILY_DOMAIN':'good.daily.co.evil.test','WZOS_DAILY_ENABLED':'1'}):
            p=DailyProvider();self.assertFalse(p.enabled)
            with self.assertRaises(HTTPException) as error:p.call('GET','rooms')
            self.assertEqual(error.exception.status_code,503)
    def test_malformed_configuration_and_close_response_are_not_accepted(self):
        provider=self.provider(lambda r:httpx.Response(200,json={'config':None}))
        with self.assertRaises(HTTPException) as caught:provider.room('name',100)
        self.assertEqual(caught.exception.status_code,502)
        with self.assertRaises(HTTPException) as caught:provider.close('name')
        self.assertEqual(caught.exception.status_code,502)
        provider=self.provider(lambda r:httpx.Response(200,json={'name':'other-room','privacy':'private',
                            'config':{'exp':int(time.time())-1,'eject_at_room_exp':True}}))
        with self.assertRaises(HTTPException):provider.close('name')
    def test_close_uses_confirmed_near_future_expiration(self):
        def handler(request):
            body=json.loads(request.content)
            self.assertGreater(body['properties']['exp'],int(time.time()))
            self.assertLessEqual(body['properties']['exp'],int(time.time())+2)
            return httpx.Response(200,json={'name':'name','privacy':'private','config':body['properties']})
        self.provider(handler).close('name')
