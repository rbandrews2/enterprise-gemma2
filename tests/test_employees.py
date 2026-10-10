import os
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.workspace_preview.storage import SQLiteStorage
from services.workspace_preview.files import LocalFiles
from services.v2.knowledge.store import Store
from tests import test_accounts_storage


class EmployeeTests(unittest.TestCase):
    def make_storage(self, root):
        return SQLiteStorage(root/'employees.sqlite')

    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name);self.storage=self.make_storage(self.root)
        env=patch.dict(os.environ,{'WZOS_ACCOUNT_WORKSPACE':'1'});env.start();self.addCleanup(env.stop)
        self.claims={u:{'uid':u,'email':u+'@example.test','email_verified':True} for u in ['admin','member','other']}
        self.app=create_app(self.root/'unused',Store(self.root/'sources',{}),account_workspace=True,storage=self.storage,verifier=lambda token:self.claims[token],file_store=LocalFiles(self.root/'files'))
        self.client=TestClient(self.app);self.addCleanup(self.client.close)
        code=self.app.state.accounts.issue_activation('enterprise')
        self.org=self.client.post('/api/account/organizations',headers=self.headers(),json={'name':'Employee test','activation_code':code}).json()['id']
        invitation=self.client.post('/api/account/invitations',headers=self.headers(),json={'email':'member@example.test'}).json()['token']
        self.client.post('/api/account/join',headers=self.headers('member'),json={'token':invitation})

    def headers(self,user='admin'):
        return {'Authorization':'Bearer '+user,'X-WZOS-Organization':getattr(self,'org','')}

    def profile(self,user='member',**changes):
        return self.client.put('/api/account/employees/'+user,headers=self.headers(),json={'expected_version':0,'employee_number':'emp-1','address':'Private home address',**changes})

    def qualification(self,**changes):
        return self.client.put('/api/account/employees/member/qualifications/flagger',headers=self.headers(),json={'expected_version':0,'title':'Flagger credential',**changes})

    def test_private_reads_and_admin_writes(self):
        self.assertEqual(self.profile().status_code,200)
        self.assertEqual(self.client.get('/api/account/employees/member',headers=self.headers('member')).json()['profile']['address'],'Private home address')
        self.assertEqual(self.client.get('/api/account/employees/admin',headers=self.headers('member')).status_code,404)
        self.assertEqual(self.client.get('/api/account/employees',headers=self.headers('member')).status_code,403)
        self.assertEqual(self.client.put('/api/account/employees/member',headers=self.headers('member'),json={'expected_version':1,'employee_number':'new'}).status_code,403)
        self.assertEqual(self.client.get('/api/account/employees/member',headers=self.headers('other')).status_code,403)

    def test_unique_numbers_retries_and_stale_changes(self):
        self.assertEqual(self.profile().json()['employee_number'],'EMP-1')
        self.assertEqual(self.profile().json()['version'],1)
        self.assertEqual(self.profile(address='Changed').status_code,409)
        self.assertEqual(self.profile('admin').status_code,409)
        self.assertEqual(self.profile(expected_version=1,address='Changed').json()['version'],2)
        history=self.client.get('/api/account/employees/member/history',headers=self.headers()).json()['items']
        self.assertEqual(len(history),2)
        self.assertEqual(history[0]['actor_id'],'admin')

    def test_qualification_review_expiry_and_history(self):
        self.assertEqual(self.qualification().json()['current_status'],'unreviewed')
        self.assertEqual(self.qualification(expected_version=1,review_status='verified',review_note='Reviewed').status_code,422)
        data={'expected_version':1,'review_status':'verified','review_note':'Checked official record','issuer':'Agency','evidence_reference':'Private record 42','expires_on':str(date.today()-timedelta(days=1))}
        self.assertEqual(self.qualification(**data).json()['current_status'],'expired')
        self.assertEqual(self.qualification(**data).json()['version'],2)
        self.assertEqual(self.qualification(**{**data,'review_note':'Changed'}).status_code,409)
        result=self.client.get('/api/account/employees/member',headers=self.headers('member')).json()
        self.assertEqual(result['qualifications'][0]['current_status'],'expired')
        self.assertEqual(len(self.client.get('/api/account/employees/member/history',headers=self.headers('member')).json()['items']),2)

    def test_dates_validation_and_bounds(self):
        from services.workspace_preview.employees import qualification_state
        self.assertEqual(qualification_state({'review_status':'verified'}),'verified_expiry_unknown')
        self.assertEqual(self.qualification(issued_on='2026-02-02',expires_on='2026-01-01').status_code,422)
        self.assertEqual(self.qualification(issued_on=str(date.today()+timedelta(days=2))).status_code,422)
        self.assertEqual(self.profile(phone='5551234').status_code,422)
        self.assertEqual(self.client.get('/api/account/employees?limit=51',headers=self.headers()).status_code,422)
        self.assertEqual(self.client.get('/api/account/employees?offset=99',headers=self.headers()).json()['items'],[])
        self.assertEqual(self.profile('missing').status_code,404)

    def test_other_organization_and_disabled_membership(self):
        self.profile()
        code=self.app.state.accounts.issue_activation('core')
        other=self.client.post('/api/account/organizations',headers=self.headers('other'),json={'name':'Other org','activation_code':code}).json()['id']
        headers={**self.headers('other'),'X-WZOS-Organization':other}
        self.assertEqual(self.client.get('/api/account/employees/member',headers=headers).status_code,404)
        self.assertEqual(self.client.put('/api/account/employees/member',headers=headers,json={'expected_version':0,'employee_number':'EMP-1'}).status_code,404)
        self.client.put('/api/account/members/member',headers=self.headers(),json={'role':'member','active':False})
        self.assertEqual(self.client.get('/api/account/employees/member',headers=self.headers('member')).status_code,403)
        self.assertEqual(self.client.get('/api/account/employees/member',headers=self.headers()).json()['active'],0)

    def test_script_and_page_wiring(self):
        self.assertEqual(self.client.get('/employees.js').status_code,200)
        self.assertIn('/employees.js',self.client.get('/').text)


@unittest.skipUnless(os.environ.get('WZOS_TEST_DATABASE_URL'),'Disposable PostgreSQL required')
class PostgreSQLEmployeeTests(EmployeeTests):
    make_storage=test_accounts_storage.PostgreSQLAccountStorageTests.make_storage
