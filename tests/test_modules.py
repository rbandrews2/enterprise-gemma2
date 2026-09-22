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
