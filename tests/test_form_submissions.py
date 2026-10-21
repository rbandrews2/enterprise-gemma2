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

    def test_completed_printable_is_saved_once_and_received_only_by_office(self):
        body={'request_id':str(uuid4()),'template_id':'jsa','template_revision':1,'fields':{'work_date':'2026-10-16','competent_person':'Synthetic supervisor'},'location':'Synthetic work site'}
        endpoint='/api/form-submissions/completed'
        response=self.client.post(endpoint,headers=self.h(),json=body)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(self.client.post(endpoint,headers=self.h(),json=body).json(),response.json())
        self.assertEqual(self.items('enterprise-admin').json()['items'][0]['form']['fields']['competent_person'],'Synthetic supervisor')
        self.assertEqual(self.items('core-admin').json()['items'],[])
        inbox=self.client.get('/api/messages',headers=self.h('enterprise-admin')).json()['items']
        self.assertEqual(len([m for m in inbox if 'sent to office' in m['body']]),1)
        self.assertEqual(self.client.post(endpoint,headers=self.h(),json={**body,'location':'Changed'}).status_code,409)
        self.assertEqual(self.client.post(endpoint,headers=self.h('core-admin'),json=body).status_code,409)

    def test_completed_printable_rejects_unknown_fields_invalid_dates_and_oversize_values(self):
        body={'request_id':str(uuid4()),'template_id':'jsa','template_revision':1,'fields':{}}
        endpoint='/api/form-submissions/completed'
        for fields in [{},{'unknown':'bad'},{'work_date':'not-a-date'},{'competent_person':'x'*201},{'competent_person':{'html':'unsafe'}}]:
            response=self.client.post(endpoint,headers=self.h(),json={**body,'fields':fields})
            self.assertEqual(response.status_code,422,response.text)
        self.assertEqual(self.items().json()['total'],0)

    def test_signature_snapshot_review_scope_and_retry_conflict(self):
        signature={'version':1,'mode':'drawn','signer_name':'Synthetic Worker','strokes':[[{'x':0.1,'y':0.2},{'x':0.6,'y':0.8}]]}
        body={'request_id':str(uuid4()),'template_id':'jsa','template_revision':1,'fields':{'competent_person':'Synthetic supervisor'},'signature':signature}
        endpoint='/api/form-submissions/completed'
        response=self.client.post(endpoint,headers=self.h(),json=body)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['form']['signature'],signature)
        self.assertEqual(self.client.post(endpoint,headers=self.h(),json=body).json(),response.json())
        saved=self.items('enterprise-admin').json()['items'][0]
        self.assertEqual(saved['form']['signature'],signature)
        self.assertEqual(self.items('core-admin').json()['items'],[])
        changed={**body,'signature':{**signature,'signer_name':'Different signer'}}
        self.assertEqual(self.client.post(endpoint,headers=self.h(),json=changed).status_code,409)

    def test_signature_rejects_markup_bad_geometry_and_oversized_strokes(self):
        body={'request_id':str(uuid4()),'template_id':'jsa','template_revision':1,'fields':{'competent_person':'Synthetic supervisor'}}
        signature={'version':1,'mode':'drawn','signer_name':'Synthetic Worker','strokes':[[{'x':0.1,'y':0.2}]]}
        invalid=[{**signature,'svg':'<script>bad</script>'},{**signature,'signer_name':' '},
                 {**signature,'strokes':[]},{**signature,'mode':'typed'},
                 {**signature,'strokes':[[{'x':1.1,'y':0.2}]]},
                 {**signature,'strokes':[[{'x':'0.1','y':0.2}]]},
                 {**signature,'strokes':[[{'x':0.1,'y':0.2}]*129]},
                 {**signature,'strokes':[[{'x':0.1,'y':0.2}]]*41}]
        for value in invalid:
            response=self.client.post('/api/form-submissions/completed',headers=self.h(),json={**body,'signature':value})
            self.assertEqual(response.status_code,422,response.text)
        typed={**signature,'mode':'typed','strokes':[]}
        response=self.client.post('/api/form-submissions/completed',headers=self.h(),json={**body,'signature':typed})
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['form']['signature'],typed)

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

