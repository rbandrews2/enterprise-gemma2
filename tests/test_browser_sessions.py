import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.workspace_preview.storage import SQLiteStorage
from services.workspace_preview.files import LocalFiles
from services.v2.knowledge.store import Store
from services.workspace_preview.browser_sessions import COOKIE
from services.workspace_preview.accounts import digest

class FakeProvider:
    def __init__(self):
        self.claims={'uid':'one','email':'one@example.test','email_verified':True,'auth_time':time.time()}
        self.cookies={};self.revoked=False
    def __call__(self,token):
        if token!='valid':raise ValueError('invalid')
        return dict(self.claims)
    def create_session(self,token,lifetime):
        cookie='signed-session-'+str(len(self.cookies));self.cookies[cookie]=dict(self.claims);return cookie
    def verify_session(self,cookie):
        if self.revoked:raise ValueError('revoked')
        return self.cookies[cookie]

class BrowserSessionTests(unittest.TestCase):
    def make_storage(self,root):
        return SQLiteStorage(root/"db")
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)
        env=patch.dict(os.environ,{'WZOS_ACCOUNT_WORKSPACE':'1'});env.start();self.addCleanup(env.stop)
        self.provider=FakeProvider();self.storage=self.make_storage(root)
        self.app=create_app(root/'unused',Store(root/'sources',{}),account_workspace=True,storage=self.storage,verifier=self.provider,file_store=LocalFiles(root/'files'))
        self.client=TestClient(self.app,base_url='https://testserver');self.addCleanup(self.client.close)
        self.h={'X-WZOS-Session':'1'}
    def login(self):
        r=self.client.post('/api/account/session',headers={**self.h,'Authorization':'Bearer valid'})
        self.assertEqual(r.status_code,200,r.text);return r
    def test_cookie_flags_restore_and_logout_replay(self):
        r=self.login();value=self.client.cookies.get(COOKIE)
        for flag in ['HttpOnly','Secure','SameSite=strict','Max-Age=1209600','Path=/']:self.assertIn(flag,r.headers['set-cookie'])
        self.assertNotIn('Domain=',r.headers['set-cookie'])
        self.assertEqual(self.client.get('/api/account',headers=self.h).status_code,200)
        self.assertEqual(self.client.get('/api/account').status_code,403)
        self.assertEqual(self.client.post('/api/account/logout',headers=self.h).status_code,200)
        self.assertEqual(self.client.get('/api/account',headers={**self.h,'Cookie':COOKIE+'='+value}).status_code,401)
    def test_fresh_verified_auth_and_csrf_required(self):
        self.assertEqual(self.client.post('/api/account/session',headers={'Authorization':'Bearer valid'}).status_code,403)
        self.assertEqual(self.client.post('/api/account/session',headers={**self.h,'Authorization':'Bearer valid','Origin':'https://evil.example'}).status_code,403)
        self.provider.claims['auth_time']=time.time()-301
        self.assertEqual(self.client.post('/api/account/session',headers={**self.h,'Authorization':'Bearer valid'}).status_code,401)
        self.provider.claims.update(auth_time=time.time(),email_verified=False)
        self.assertEqual(self.client.post('/api/account/session',headers={**self.h,'Authorization':'Bearer valid'}).status_code,403)
    def test_registry_expiry_provider_revocation_and_forgery(self):
        self.login();value=self.client.cookies.get(COOKIE)
        self.provider.revoked=True
        self.assertEqual(self.client.get('/api/account',headers=self.h).status_code,401)
        self.provider.revoked=False
        with self.storage.connect() as db:db.execute('UPDATE browser_sessions SET expires_at=? WHERE hash=?',('2000-01-01',digest(value)))
        self.assertEqual(self.client.get('/api/account',headers=self.h).status_code,401)
        self.assertEqual(self.client.get('/api/account',headers={**self.h,'Cookie':COOKIE+'=forged'}).status_code,401)
    def test_failed_issuance_preserves_existing_session(self):
        self.login();original=self.client.cookies.get(COOKIE)
        with patch.object(self.provider,'create_session',side_effect=RuntimeError('private provider detail')):
            response=self.client.post('/api/account/session',headers={**self.h,'Authorization':'Bearer valid'})
        self.assertEqual(response.status_code,503)
        self.assertNotIn('private provider detail',response.text)
        self.assertNotIn('set-cookie',response.headers)
        self.assertEqual(self.client.cookies.get(COOKIE),original)
        self.assertEqual(self.client.get('/api/account',headers=self.h).status_code,200)

    def test_replacement_invalidates_old_cookie_and_logout_needs_csrf_header(self):
        self.login();original=self.client.cookies.get(COOKIE)
        self.login()
        self.assertNotEqual(self.client.cookies.get(COOKIE),original)
        self.assertEqual(self.client.get('/api/account',headers={**self.h,'Cookie':COOKIE+'='+original}).status_code,401)
        self.assertEqual(self.client.post('/api/account/logout').status_code,403)
        self.assertEqual(self.client.get('/api/account',headers=self.h).status_code,200)

    def test_all_devices_and_membership_rechecked(self):
        self.login();first=self.client.cookies.get(COOKIE)
        # A second independent browser keeps its own registry entry.
        self.client.cookies.clear();self.login();second=self.client.cookies.get(COOKIE)
        with self.storage.connect() as db:
            db.execute('INSERT INTO organizations VALUES (?,?,?,?)',('org','Example','core',1))
            db.execute('INSERT INTO memberships VALUES (?,?,?,?)',('org','one','member',1))
        h={**self.h,'X-WZOS-Organization':'org'}
        self.assertEqual(self.client.get('/api/session',headers=h).json()['role'],'member')
        with self.storage.connect() as db:db.execute('UPDATE memberships SET active=0 WHERE user_id=?',('one',))
        self.assertEqual(self.client.get('/api/session',headers=h).status_code,403)
        self.assertEqual(self.client.post('/api/account/logout-all',headers=self.h).status_code,200)
        for cookie in [first,second]:self.assertEqual(self.client.get('/api/account',headers={**self.h,'Cookie':COOKIE+'='+cookie}).status_code,401)


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'),'Dedicated PostgreSQL test database not configured')
class PostgreSQLBrowserSessionTests(BrowserSessionTests):
    def make_storage(self,root):
        from uuid import uuid4
        from psycopg.conninfo import make_conninfo
        from services.workspace_preview.postgres import PostgreSQLStorage
        dsn=os.environ['WZOS_TEST_DATABASE_URL'];schema='test_'+uuid4().hex
        bootstrap=PostgreSQLStorage(dsn);self.addCleanup(bootstrap.close)
        with bootstrap.connect() as db:db.execute('CREATE SCHEMA '+schema)
        def cleanup():
            with bootstrap.connect() as db:db.execute('DROP SCHEMA '+schema+' CASCADE')
        self.addCleanup(cleanup)
        storage=PostgreSQLStorage(make_conninfo(dsn,options='-c search_path='+schema));self.addCleanup(storage.close)
        storage.initialize();return storage
