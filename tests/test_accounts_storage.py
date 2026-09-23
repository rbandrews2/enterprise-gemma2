import os
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.workspace_preview.storage import SQLiteStorage
from services.workspace_preview.files import LocalFiles
from services.v2.knowledge.store import Store


class AccountStorageTests(unittest.TestCase):
    def make_storage(self, root):
        return SQLiteStorage(root/'account.sqlite')

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.env=patch.dict(os.environ,{'WZOS_ACCOUNT_WORKSPACE':'1'});self.env.start();self.addCleanup(self.env.stop)
        self.root=Path(self.temp.name);self.storage=self.make_storage(self.root)
        self.files=LocalFiles(self.root/'files')
        self.claims={name:{'uid':name,'email':name+'@example.test','email_verified':True} for name in ('owner','member','other','admin')}
        self.build()
        self.org=self.create_org('owner')

    def build(self):
        self.app=create_app(self.root/'unused.sqlite',Store(self.root/'sources',{}),account_workspace=True,storage=self.storage,verifier=lambda token:self.claims[token],file_store=self.files)
        self.client=TestClient(self.app);self.addCleanup(self.client.close)

    def headers(self, who='owner', org=None):
        return {'Authorization':'Bearer '+who,'X-WZOS-Organization':org or getattr(self,'org','')}

    def create_org(self, who):
        code=self.app.state.accounts.issue_activation('enterprise')
        r=self.client.post('/api/account/organizations',json={'name':'Test organization','activation_code':code},headers=self.headers(who))
        self.assertEqual(r.status_code,200,r.text);return r.json()['id']

    def add(self, who, role='member'):
        r=self.client.post('/api/account/invitations',json={'email':who+'@example.test','role':role},headers=self.headers())
        self.assertEqual(r.status_code,200,r.text)
        r=self.client.post('/api/account/join',json={'token':r.json()['token']},headers=self.headers(who))
        self.assertEqual(r.status_code,200,r.text)

    def order(self, who='member'):
        r=self.client.post('/api/orders',headers=self.headers(who),json={'request_id':str(uuid4()),'title':'Saved job','work_type':'line_striping','address':'Test road','locality':'Norfolk'})
        self.assertEqual(r.status_code,201,r.text);return r.json()['id']

    def test_verified_identity_and_no_fixture_bypass(self):
        self.assertEqual(self.client.get('/api/orders',headers={'X-Preview-Actor':'enterprise-admin'}).status_code,401)
        self.assertEqual(self.client.get('/api/orders',headers=self.headers('other')).status_code,403)
        self.claims['other']['email_verified']=False
        self.assertEqual(self.client.get('/api/account',headers=self.headers('other')).status_code,403)
        self.assertEqual(self.client.get('/api/orders',headers=self.headers()).json()['items'],[])

    def test_member_admin_owner_and_revocation(self):
        self.add('member');self.add('admin','admin')
        self.assertEqual(self.client.get('/api/session',headers=self.headers('member')).json()['role'],'general')
        self.assertEqual(self.client.get('/api/time/entries?team=true',headers=self.headers('member')).status_code,403)
        self.assertEqual(self.client.get('/api/time/entries?team=true',headers=self.headers('admin')).status_code,200)
        change={'role':'admin','active':True}
        self.assertEqual(self.client.put('/api/account/members/member',json=change,headers=self.headers('admin')).status_code,403)
        self.assertEqual(self.client.put('/api/account/members/owner',json={'role':'member','active':False},headers=self.headers()).status_code,409)
        self.assertEqual(self.client.put('/api/account/members/member',json={'role':'member','active':False},headers=self.headers()).status_code,200)
        self.assertEqual(self.client.get('/api/orders',headers=self.headers('member')).status_code,403)

    def test_invitation_is_verified_email_bound_and_cannot_self_promote(self):
        self.add('member')
        self.assertEqual(self.client.post('/api/account/invitations',json={'email':'other@example.test','role':'admin'},headers=self.headers('member')).status_code,403)
        invitation=self.client.post('/api/account/invitations',json={'email':'other@example.test'},headers=self.headers()).json()['token']
        self.assertEqual(self.client.post('/api/account/join',json={'token':invitation},headers=self.headers('member')).status_code,403)
        self.assertEqual(self.client.post('/api/account/organizations',json={'name':'Self upgrade','activation_code':'x'*32,'edition':'enterprise'},headers=self.headers('member')).status_code,422)

    def test_all_module_records_survive_application_restart(self):
        self.add('member');order=self.order()
        clock={'request_id':str(uuid4()),'action':'clock_in','order_id':order}
        self.assertEqual(self.client.post('/api/time/commands',headers=self.headers('member'),json=clock).status_code,200)
        formid=str(uuid4());body={'request_id':str(uuid4()),'title':'Stored form','order_id':order}
        r=self.client.put('/api/modules/forms/'+formid,headers=self.headers('member'),json=body)
        self.assertEqual(r.status_code,200,r.text)
        body.update(expected_version=1,details='Revision two')
        self.assertEqual(self.client.put('/api/modules/forms/'+formid,headers=self.headers('member'),json=body).status_code,200)
        schedule={ 'request_id':str(uuid4()),'title':'Team assignment','assignees':['member'],'start':'2026-10-01T08:00:00Z','end':'2026-10-01T09:00:00Z'}
        self.assertEqual(self.client.put('/api/modules/schedule/'+str(uuid4()),headers=self.headers(),json=schedule).status_code,200)
        message={'request_id':str(uuid4()),'recipient_id':'member','text':'Stored internal message'}
        self.assertEqual(self.client.post('/api/messages',headers=self.headers(),json=message).status_code,200)
        course=self.client.get('/api/training',headers=self.headers('member')).json()['items'][0]['id']
        self.assertEqual(self.client.put('/api/training/'+course,headers=self.headers('member'),json={'status':'studying'}).status_code,200)
        self.client.close();self.build()
        self.assertEqual(self.client.get('/api/modules/forms',headers=self.headers('member')).json()['total'],1)
        self.assertEqual(len(self.client.get('/api/modules/forms/'+formid+'/history',headers=self.headers('member')).json()['items']),2)
        self.assertEqual(self.client.get('/api/modules/schedule',headers=self.headers('member')).json()['total'],1)
        self.assertEqual(len(self.client.get('/api/messages',headers=self.headers('member')).json()['items']),1)
        self.assertEqual(self.client.get('/api/time/status',headers=self.headers('member')).json()['active']['status'],'working')
        self.assertEqual(self.client.get('/api/training',headers=self.headers('member')).json()['items'][0]['study_status'],'studying')
        # A second organization never sees the first organization's saved records.
        other=self.create_org('other')
        self.assertEqual(self.client.get('/api/modules/forms',headers=self.headers('other',other)).json()['total'],0)
        self.assertEqual(self.client.get('/api/orders/'+order,headers=self.headers('other',other)).status_code,404)

    def test_same_user_retry_cannot_cross_organization(self):
        body={'request_id':str(uuid4()),'title':'Private job','work_type':'other','address':'Test road','locality':'Norfolk'}
        first=self.client.post('/api/orders',headers=self.headers(),json=body)
        self.assertEqual(first.status_code,201)
        second=self.create_org('owner')
        self.assertEqual(self.client.post('/api/orders',headers=self.headers('owner',second),json=body).status_code,409)

    def test_report_snapshots_and_checklists_persist(self):
        self.add('member');order=self.order()
        items={key:{'status':'needs_attention','notes':'Synthetic test'} for key in ('site','authority','forms','crew','communication')}
        r=self.client.put('/api/orders/'+order+'/checklist',headers=self.headers('member'),json={'expected_version':0,'expected_order_version':1,'items':items})
        self.assertEqual(r.status_code,200,r.text)
        report_id=str(uuid4())
        r=self.client.post('/api/orders/'+order+'/reports',headers=self.headers('member'),json={'request_id':report_id,'expected_order_version':1})
        self.assertEqual(r.status_code,200,r.text)
        self.client.close();self.build()
        r=self.client.get('/api/orders/'+order+'/reports/'+report_id,headers=self.headers('member'))
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['report']['checklist']['version'],1)

    def test_files_private_idempotent_and_survive_restart(self):
        self.add('member');order=self.order();file_id=str(uuid4())
        path='/api/files/'+file_id+'?entity_kind=order&entity_id='+order+'&filename=site.pdf'
        headers={**self.headers('member'),'Content-Type':'application/pdf'};data=b'%PDF-1.7\nSynthetic fixture'
        self.assertEqual(self.client.put(path,headers=headers,content=data).status_code,200)
        self.assertEqual(self.client.put(path,headers=headers,content=data).status_code,200)
        self.assertEqual(self.client.put(path,headers=headers,content=data+b'changed').status_code,409)
        self.client.close();self.build()
        self.assertEqual(self.client.get('/api/files/'+file_id,headers=self.headers('member')).content,data)
        other=self.create_org('other')
        self.assertEqual(self.client.get('/api/files/'+file_id,headers=self.headers('other',other)).status_code,404)
        bad=path.replace(file_id,str(uuid4()))
        self.assertEqual(self.client.put(bad,headers=headers,content=b'wrong format').status_code,415)
        self.assertEqual(self.client.put(bad,headers=headers,content=b'%PDF-'+b'x'*(10*1024*1024)).status_code,413)


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'),'Dedicated PostgreSQL test database not configured')
class PostgreSQLAccountStorageTests(AccountStorageTests):
    def make_storage(self, root):
        import psycopg
        from psycopg.conninfo import make_conninfo
        from services.workspace_preview.postgres import PostgreSQLStorage
        dsn=os.environ['WZOS_TEST_DATABASE_URL'];schema='test_'+uuid4().hex
        with psycopg.connect(dsn,autocommit=True) as db: db.execute('CREATE SCHEMA '+schema)
        def cleanup():
            with psycopg.connect(dsn,autocommit=True) as db: db.execute('DROP SCHEMA '+schema+' CASCADE')
        self.addCleanup(cleanup)
        storage=PostgreSQLStorage(make_conninfo(dsn,options='-c search_path='+schema))
        storage.initialize();return storage
