import os
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.v2.knowledge.store import Store

class TimeClockTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{'WZOS_WORKSPACE_PREVIEW':'1','K_SERVICE':'','GAE_ENV':'','NETLIFY':''});self.env.start()
        self.db=Path(self.temp.name)/'db.sqlite'
        self.client=TestClient(create_app(self.db,Store(Path(self.temp.name)/'sources',{})));self.client.__enter__()
        self.headers={'X-Preview-Actor':'core-general'}
    def tearDown(self):
        self.client.__exit__(None,None,None);self.env.stop();self.temp.cleanup()
    def command(self, action, state=None, at='2026-09-22T08:00:00+00:00', **extra):
        body={'request_id':str(uuid4()),'action':action,**extra}
        if state:body.update(shift_id=state['id'],expected_version=state['version'])
        with patch('services.workspace_preview.timeclock.utc_now',return_value=at):
            return self.client.post('/api/time/commands',headers=self.headers,json=body)
    def test_shift_tasks_breaks_and_retries(self):
        state=self.command('clock_in',order_id='core-sample').json()['entry']
        self.assertIsNotNone(state['order_title'])
        self.assertEqual(self.command('clock_in').status_code,409)
        self.assertEqual(self.command('break_end',state).status_code,409)
        old=state
        state=self.command('switch_task',state,at='2026-09-22T09:00:00+00:00',task='travel').json()['entry']
        self.assertEqual(self.command('break_start',old).status_code,409)
        state=self.command('break_start',state,at='2026-09-22T09:30:00+00:00').json()['entry']
        self.assertEqual(self.command('switch_task',state,at='2026-09-22T09:31:00+00:00',task='setup').status_code,409)
        state=self.command('break_end',state,at='2026-09-22T09:45:00+00:00').json()['entry']
        state=self.command('clock_out',state,at='2026-09-22T10:00:00+00:00').json()['entry']
        self.assertEqual(state['work_seconds'],6300);self.assertEqual(state['break_seconds'],900)
        self.assertEqual(len(state['segments']),3);self.assertEqual(state['status'],'closed')
        self.assertFalse(state['payroll_calculated'])
        self.assertIsNone(self.client.get('/api/time/status',headers=self.headers).json()['active'])
    def test_idempotent_conflicts_and_payload_validation(self):
        body={'request_id':str(uuid4()),'action':'clock_in','task':'setup'}
        first=self.client.post('/api/time/commands',json=body,headers=self.headers)
        self.assertEqual(first.status_code,200)
        self.assertEqual(self.client.post('/api/time/commands',json=body,headers=self.headers).json(),first.json())
        self.assertEqual(self.client.post('/api/time/commands',json={**body,'task':'other'},headers=self.headers).status_code,409)
        for extra in ({'employee_id':'core-admin'},{'clock_in':'2020-01-01'},{'expected_version':True}):
            self.assertEqual(self.client.post('/api/time/commands',json={**body,**extra},headers=self.headers).status_code,422)
        history=self.client.get('/api/time/entries',headers=self.headers).json()
        self.assertEqual(history['total'],1)
    def test_access_scope_and_restart(self):
        self.assertEqual(self.client.get('/api/time/status').status_code,401)
        self.assertEqual(self.command('clock_in',order_id='enterprise-sample').status_code,404)
        state=self.command('clock_in').json()['entry']
        for actor in ['core-admin','enterprise-admin','enterprise-general']:
            headers={'X-Preview-Actor':actor}
            self.assertIsNone(self.client.get('/api/time/status',headers=headers).json()['active'])
            self.assertEqual(self.client.get('/api/time/entries',headers=headers).json()['total'],0)
            self.assertEqual(self.client.post('/api/time/commands',headers=headers,json={'request_id':str(uuid4()),'action':'clock_out','shift_id':state['id'],'expected_version':1}).status_code,409)
        self.assertEqual(self.client.get('/api/time/entries?team=true',headers=self.headers).status_code,403)
        self.assertEqual(self.client.get('/api/time/entries?team=true',headers={'X-Preview-Actor':'core-admin'}).json()['total'],1)
        self.assertEqual(self.client.get('/api/time/entries?team=true',headers={'X-Preview-Actor':'enterprise-admin'}).json()['total'],0)
        self.assertEqual(self.client.get('/api/time/entries?limit=51',headers=self.headers).status_code,422)
        with TestClient(create_app(self.db,Store(Path(self.temp.name)/'sources',{}))) as second:
            self.assertEqual(second.get('/api/time/status',headers=self.headers).json()['active']['id'],state['id'])
    def test_clock_out_on_break_and_backwards_clock(self):
        state=self.command('clock_in').json()['entry']
        self.assertEqual(self.command('clock_out',state,at='2026-09-22T07:00:00+00:00').status_code,409)
        state=self.command('break_start',state,at='2026-09-22T08:10:00+00:00').json()['entry']
        state=self.command('clock_out',state,at='2026-09-22T08:20:00+00:00').json()['entry']
        self.assertEqual(state['work_seconds'],600);self.assertEqual(state['break_seconds'],600)
        self.assertTrue(all(s['end'] for s in state['segments']))
        self.assertTrue(all(b['end'] for b in state['breaks']))
    def test_atlas_receives_own_clock_only(self):
        class Fake:
            context=None
            async def reply(self,payload,context):self.context=context;return 'Use the time clock controls.'
        fake=Fake();self.command('clock_in',task='travel')
        with TestClient(create_app(self.db,Store(Path(self.temp.name)/'sources',{}),fake)) as client:
            response=client.post('/api/assistant/chat',headers=self.headers,json={'question':'Am I clocked in?'})
            self.assertEqual(response.status_code,200)
            self.assertEqual(fake.context['time_clock']['status'],'working')
            self.assertEqual(fake.context['time_clock']['task'],'travel')
            self.assertEqual(response.json()['actions_performed'],[])
            self.assertIn('time_clock',[a['id'] for a in response.json()['navigation']])
            client.post('/api/assistant/chat',headers={'X-Preview-Actor':'core-admin'},json={'question':'Am I clocked in?'})
            self.assertEqual(fake.context['time_clock']['status'],'off_clock')

    def test_concurrent_clock_ins_allow_one_shift(self):
        from concurrent.futures import ThreadPoolExecutor
        def start(_): return self.command('clock_in').status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses=list(pool.map(start,range(2)))
        self.assertEqual(sorted(statuses),[200,409])
        self.assertEqual(self.client.get('/api/time/entries',headers=self.headers).json()['total'],1)
