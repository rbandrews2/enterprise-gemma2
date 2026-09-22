import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.v2.knowledge.store import Store

class ReportTests(unittest.TestCase):
    def test_scoped_report_and_stale_checklist(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,{"WZOS_WORKSPACE_PREVIEW":"1"}):
            root=Path(directory)
            with TestClient(create_app(root/'db',Store(root/'sources',{}))) as client:
                admin={"X-Preview-Actor":"enterprise-admin"}
                general={"X-Preview-Actor":"enterprise-general"}
                path='/api/orders/enterprise-sample/report'
                self.assertEqual(client.get(path).status_code,401)
                self.assertEqual(client.get(path,headers={"X-Preview-Actor":"core-admin"}).status_code,403)
                self.assertEqual(client.get('/api/orders/core-sample/report',headers=admin).status_code,404)
                original=client.get(path,headers=general).json()
                self.assertIsNone(original['checklist']);self.assertFalse(original['approved_for_field_use'])
                items={key:{"status":"not_reviewed","notes":""} for key in ('site','authority','forms','crew','communication')}
                self.assertEqual(client.put('/api/orders/enterprise-sample/checklist',headers=general,json={"expected_version":0,"expected_order_version":1,"items":items}).status_code,200)
                body={"request_id":str(uuid4()),"title":"Private admin draft","order_id":"enterprise-sample"}
                self.assertEqual(client.put('/api/modules/forms/'+str(uuid4()),headers=admin,json=body).status_code,200)
                self.assertEqual(client.get(path,headers=general).json()['forms_total'],0)
                self.assertEqual(client.get(path,headers=admin).json()['forms_total'],1)
                order=original['order'];payload={key:order[key] for key in ('title','work_type','address','locality','work_date','notes')}
                payload.update(expected_version=1,notes='Changed scope')
                self.assertEqual(client.put('/api/orders/enterprise-sample',headers=general,json=payload).status_code,200)
                report=client.get(path,headers=general).json()
                self.assertEqual(report['order']['version'],2)
                self.assertTrue(report['checklist']['stale'])

