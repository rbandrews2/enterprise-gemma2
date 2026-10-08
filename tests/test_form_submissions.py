import os,tempfile,unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.workspace_preview.storage import SQLiteStorage
from services.v2.knowledge.store import Store

class FormSubmissionTests(unittest.TestCase):
    def make_storage(self,root):return SQLiteStorage(root/'db')
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);root=Path(self.temp.name)
        env=patch.dict(os.environ,{'WZOS_WORKSPACE_PREVIEW':'1'});env.start();self.addCleanup(env.stop)
        self.storage=self.make_storage(root);self.app=create_app(storage=self.storage,knowledge_store=Store(root/'sources',{}))
        self.client=TestClient(self.app);self.addCleanup(self.client.close)
        self.form=str(uuid4());self.body={'request_id':str(uuid4()),'title':'Synthetic safety form','details':'Original content'}
        self.assertEqual(self.client.put('/api/modules/forms/'+self.form,headers=self.h(),json=self.body).status_code,200)
        self.sub={'request_id':str(uuid4()),'form_id':self.form,'expected_form_version':1}
    def h(self,who='enterprise-general'):return {'X-Preview-Actor':who}
    def send(self,body=None,who='enterprise-general'):return self.client.post('/api/form-submissions',headers=self.h(who),json=body or self.sub)
    def items(self,who='enterprise-general',query=''):return self.client.get('/api/form-submissions'+query,headers=self.h(who))
    def test_snapshot_retry_and_later_edits(self):
        response=self.send();self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(self.send().json(),response.json())
        self.body.update(expected_version=1,details='Changed later')
        self.client.put('/api/modules/forms/'+self.form,headers=self.h(),json=self.body)
        saved=self.items().json()['items'][0]
        self.assertEqual(saved['form']['details'],'Original content');self.assertEqual(saved['form_version'],1)
        self.assertEqual(len(saved['payload_hash']),64);self.assertFalse(saved['external_delivery'])
        self.assertEqual(self.send({**self.sub,'request_id':str(uuid4())}).status_code,409)
        self.assertEqual(self.send({**self.sub,'expected_form_version':2}).status_code,409)
    def test_scope_and_member_cannot_submit_others_or_review(self):
        self.assertEqual(self.send(who='core-admin').status_code,404)
        sid=self.send().json()['id']
        self.assertEqual(self.items('core-admin').json()['items'],[])
        payload={'expected_version':1,'status':'reviewed','note':'Read'}
        url='/api/form-submissions/'+sid+'/review'
        self.assertEqual(self.client.post(url,headers=self.h(),json=payload).status_code,403)
        self.assertEqual(self.client.post(url,headers=self.h('core-admin'),json=payload).status_code,404)
        # Same-organization admin-created drafts remain private to their owner until submitted.
        other=str(uuid4());self.client.put('/api/modules/forms/'+other,headers=self.h('enterprise-admin'),json=self.body)
        self.assertEqual(self.send({**self.sub,'form_id':other,'request_id':str(uuid4())}).status_code,404)
    def test_admin_review_retry_and_stale_conflict(self):
        sid=self.send().json()['id'];url='/api/form-submissions/'+sid+'/review'
        body={'expected_version':1,'status':'changes_requested','note':''}
        self.assertEqual(self.client.post(url,headers=self.h('enterprise-admin'),json=body).status_code,422)
        body['note']='Add the work location'
        r=self.client.post(url,headers=self.h('enterprise-admin'),json=body);self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.client.post(url,headers=self.h('enterprise-admin'),json=body).json(),r.json())
        self.assertEqual(self.items().json()['items'][0]['note'],body['note'])
        self.assertEqual(self.client.post(url,headers=self.h('enterprise-admin'),json={**body,'status':'reviewed'}).status_code,409)
    def test_pagination_and_missing_versions(self):
        self.assertEqual(self.send({**self.sub,'expected_form_version':2}).status_code,409)
        self.send()
        self.assertEqual(self.items(query='?limit=1').json()['total'],1)
        self.assertEqual(self.items(query='?offset=1').json()['items'],[])
        self.assertEqual(self.items(query='?limit=51').status_code,422)

@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'),'Dedicated PostgreSQL database not configured')
class PostgreSQLFormSubmissionTests(FormSubmissionTests):
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

