import os
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.v2.knowledge.store import Store

class ModuleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{"WZOS_WORKSPACE_PREVIEW":"1"})
        self.env.start()
        root=Path(self.temp.name)
        self.client=TestClient(create_app(root/'db',Store(root/'sources',{})))
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.env.stop)
        self.addCleanup(self.client.close)
    def headers(self, actor): return {"X-Preview-Actor":actor}
    def body(self): return {"request_id":str(uuid4()),"title":"Synthetic record","details":"Test only"}
    def save(self,kind,body,actor="enterprise-admin",record=None):
        return self.client.put('/api/modules/'+kind+'/'+(record or str(uuid4())),json=body,headers=self.headers(actor))
    def test_forms_scope_retries_conflicts_and_link(self):
        record=str(uuid4());body=self.body()
        first=self.save('forms',body,'enterprise-general',record)
        self.assertEqual(first.status_code,200)
        self.assertEqual(self.save('forms',body,'enterprise-general',record).json()['version'],1)
        body['details']='changed'
        self.assertEqual(self.save('forms',body,'enterprise-general',record).status_code,409)
        body['expected_version']=1
        self.assertEqual(self.save('forms',body,'enterprise-general',record).json()['version'],2)
        self.assertEqual(self.client.get('/api/modules/forms',headers=self.headers('enterprise-admin')).json()['total'],1)
        self.assertEqual(self.client.get('/api/modules/forms',headers=self.headers('core-admin')).json()['total'],0)
        body=self.body();body['order_id']='core-sample'
        self.assertEqual(self.save('forms',body).status_code,404)
        self.assertEqual(self.client.get('/api/modules/forms?limit=51',headers=self.headers('enterprise-admin')).status_code,422)
    def test_schedule_access_and_timezone(self):
        body=self.body();body.update(start='2026-09-23T08:00:00-04:00',end='2026-09-23T09:00:00-04:00')
        self.assertEqual(self.save('schedule',body,'enterprise-general').status_code,403)
        saved=self.save('schedule',body)
        self.assertEqual(saved.status_code,200)
        self.assertEqual(saved.json()['start'],'2026-09-23T12:00:00+00:00')
        page=self.client.get('/api/modules/schedule',headers=self.headers('enterprise-general')).json()
        self.assertEqual(page['total'],1);self.assertFalse(page['can_edit'])
        body['end']=body['start']
        self.assertEqual(self.save('schedule',body).status_code,422)
        body['start']='2026-09-23T08:00:00'
        self.assertEqual(self.save('schedule',body).status_code,422)
    def test_general_cannot_read_or_edit_admin_incident(self):
        record=str(uuid4());body=self.body()
        self.assertEqual(self.save('forms',body,record=record).status_code,200)
        self.assertEqual(self.client.get('/api/modules/forms',headers=self.headers('enterprise-general')).json()['items'],[])
        body['expected_version']=1
        self.assertEqual(self.save('forms',body,'enterprise-general',record).status_code,404)
    def test_pagination_and_unknown_module(self):
        for _ in range(3): self.assertEqual(self.save('forms',self.body()).status_code,200)
        page=self.client.get('/api/modules/forms?limit=2&offset=2',headers=self.headers('enterprise-admin')).json()
        self.assertEqual(page['total'],3);self.assertEqual(len(page['items']),1)
        self.assertEqual(self.client.get('/api/modules/messages',headers=self.headers('enterprise-admin')).status_code,422)

    def test_vehicle_inspection_roundtrip_and_validation(self):
        body=self.body();body.update(form_type="dvir",inspection={"vehicle_id":"TEST-7","brakes":"fail","defects":"Synthetic brake issue"})
        record=str(uuid4())
        response=self.save('forms',body,'enterprise-general',record)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['inspection']['tires'],'not_checked')
        self.assertEqual(response.json()['inspection']['brakes'],'fail')
        rows=self.client.get('/api/modules/forms',headers=self.headers('enterprise-general')).json()['items']
        self.assertEqual(rows[0]['inspection']['vehicle_id'],'TEST-7')
        body['inspection']['defects']=''
        self.assertEqual(self.save('forms',body).status_code,422)
        body['inspection']['brakes']='pass';body['inspection']['odometer']=-1
        self.assertEqual(self.save('forms',body).status_code,422)
        body['inspection']['odometer']=100
        self.assertEqual(self.save('schedule',body).status_code,422)
        other=self.body();other['expected_version']=1
        self.assertEqual(self.save('forms',other,'enterprise-general',record).status_code,409)

    def test_jsa_history_and_schedule_conflicts(self):
        record=str(uuid4());body=self.body();body.update(form_type='jsa',safety={'hazards':'Synthetic hazard','controls':'Synthetic control'})
        self.assertEqual(self.save('forms',body,record=record).status_code,200)
        body.update(expected_version=1,details='Updated review')
        self.assertEqual(self.save('forms',body,record=record).status_code,200)
        history=self.client.get('/api/modules/forms/'+record+'/history',headers=self.headers('enterprise-admin')).json()['items']
        self.assertEqual([r['version'] for r in history],[2,1])
        self.assertEqual(history[1]['record']['details'],'Test only')
        self.assertEqual(self.client.get('/api/modules/forms/'+record+'/history',headers=self.headers('enterprise-general')).status_code,404)
        event=self.body();event.update(start='2026-09-25T08:00:00Z',end='2026-09-25T10:00:00Z',assignees=['enterprise-general'])
        self.assertEqual(self.save('schedule',event).status_code,200)
        self.assertEqual(self.save('schedule',event).status_code,409)
        event['assignees']=['core-general']
        self.assertEqual(self.save('schedule',event).status_code,422)
        page=self.client.get('/api/modules/schedule?day=2026-09-26',headers=self.headers('enterprise-admin')).json()
        self.assertEqual(page['total'],0)

    def test_test_messages_and_study_isolation(self):
        admin=self.headers('enterprise-admin');general=self.headers('enterprise-general')
        body={'request_id':str(uuid4()),'recipient_id':'enterprise-general','text':'Synthetic message'}
        self.assertEqual(self.client.post('/api/messages',headers=admin,json=body).status_code,200)
        self.assertEqual(self.client.post('/api/messages',headers=admin,json=body).status_code,200)
        self.assertEqual(len(self.client.get('/api/messages',headers=general).json()['items']),1)
        self.assertEqual(self.client.get('/api/messages',headers=self.headers('core-admin')).json()['items'],[])
        body.update(request_id=str(uuid4()),recipient_id='core-general')
        self.assertEqual(self.client.post('/api/messages',headers=admin,json=body).status_code,404)
        catalog=self.client.get('/api/training',headers=admin).json();course=catalog['items'][0]['id']
        self.assertFalse(catalog['certification_enabled'])
        self.assertEqual(self.client.put('/api/training/'+course,headers=admin,json={'status':'studying'}).status_code,200)
        self.assertEqual(self.client.get('/api/training',headers=general).json()['items'][0]['study_status'],'not_started')
        self.assertEqual(self.client.put('/api/training/'+course,headers=admin,json={'status':'certified'}).status_code,422)
        self.assertEqual(self.client.get('/api/time/export?team=true',headers=general).status_code,403)
        response=self.client.get('/api/time/export',headers=admin)
        self.assertEqual(response.status_code,200);self.assertIn('Payroll calculated',response.text)
        self.assertEqual(self.client.get('/api/time/entries?start_date=2026-09-25&end_date=2026-09-24',headers=admin).status_code,422)

    def test_meeting_links_admin_only_scoped_validated_and_versioned(self):
        body=self.body();body.update(start="2026-10-09T13:00:00Z",end="2026-10-09T14:00:00Z",meeting_url="https://meet.google.com/abc-defg-hij")
        record=str(uuid4())
        self.assertEqual(self.save('schedule',body,'enterprise-general',record).status_code,403)
        saved=self.save('schedule',body,record=record)
        self.assertEqual(saved.status_code,200)
        member=self.client.get('/api/modules/schedule',headers=self.headers('enterprise-general')).json()
        self.assertFalse(member['can_edit']);self.assertEqual(member['items'][0]['meeting_url'],body['meeting_url'])
        self.assertEqual(self.client.get('/api/modules/schedule',headers=self.headers('core-admin')).json()['total'],0)
        body.update(status='cancelled',expected_version=1)
        self.assertEqual(self.save('schedule',body,'enterprise-general',record).status_code,403)
        self.assertEqual(self.save('schedule',body,record=record).json()['version'],2)
        body.update(status='draft',expected_version=0)
        self.assertEqual(self.save('schedule',body,record=record).status_code,409)
        for link in ['http://meet.google.com/abc-defg-hij','https://meet.google.com.evil.test/abc-defg-hij','https://meet.google.com@evil.test/abc-defg-hij','javascript:alert(1)','https://meet.google.com/abc-defg-hij?token=secret']:
            body['meeting_url']=link
            self.assertEqual(self.save('schedule',body).status_code,422)
        form=self.body();form['meeting_url']='https://meet.google.com/abc-defg-hij'
        self.assertEqual(self.save('forms',form).status_code,422)

    def test_meeting_filter_counts_before_pagination_and_preserves_scope(self):
        for i in range(4):
            body=self.body();body.update(title=f'Schedule {i}',start='2026-10-09T13:00:00Z',end='2026-10-09T14:00:00Z')
            if i % 2: body['meeting_url']='https://meet.google.com/abc-defg-hij'
            self.assertEqual(self.save('schedule',body).status_code,200)
        path='/api/modules/schedule?meetings_only=true&limit=1'
        first=self.client.get(path,headers=self.headers('enterprise-general')).json()
        second=self.client.get(path+'&offset=1',headers=self.headers('enterprise-general')).json()
        self.assertEqual(first['total'],2);self.assertEqual(second['total'],2)
        self.assertEqual(len(first['items']),1);self.assertEqual(len(second['items']),1)
        self.assertNotEqual(first['items'][0]['id'],second['items'][0]['id'])
        self.assertTrue(first['items'][0]['meeting_url'])
        self.assertEqual(self.client.get(path+'&offset=2',headers=self.headers('enterprise-general')).json()['items'],[])
        self.assertEqual(self.client.get(path,headers=self.headers('core-admin')).json()['total'],0)
        self.assertEqual(self.client.get('/api/modules/schedule',headers=self.headers('enterprise-admin')).json()['total'],4)
        self.assertEqual(self.client.get('/api/modules/forms?meetings_only=true',headers=self.headers('enterprise-admin')).status_code,422)
