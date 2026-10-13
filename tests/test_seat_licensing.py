import os
import hashlib
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.workspace_preview.accounts import Accounts
from services.workspace_preview.storage import SQLiteStorage
from services.workspace_preview import timeclock


class SeatLicensingTests(unittest.TestCase):
    def storage(self, root):
        return SQLiteStorage(root/'seats.sqlite')

    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.db=self.storage(Path(temp.name))
        self.claims={u:{'uid':u,'email':u+'@example.test','email_verified':True} for u in ('buyer','member','admin','other')}
        self.accounts=Accounts(self.db.connect,lambda token:self.claims[token])
        app=FastAPI();self.accounts.register(app)
        timeclock.initialize(self.db.connect)
        timeclock.register(app,self.db.connect,self.accounts.actor,lambda *args:None)
        self.client=TestClient(app);self.addCleanup(self.client.close)
        self.org=None

    def headers(self, user='buyer'):
        return {'Authorization':'Bearer '+user,'X-WZOS-Organization':self.org or ''}

    def create(self, seats=2, edition='enterprise', email='buyer@example.test'):
        self.code=self.accounts.issue_activation(edition,seat_limit=seats,purchaser_email=email)
        result=self.client.post('/api/account/organizations',headers=self.headers(),json={'name':'Licensed organization','activation_code':self.code})
        self.assertEqual(result.status_code,200,result.text);self.org=result.json()['id']

    def invite(self, user, role='member'):
        response=self.client.post('/api/account/invitations',headers=self.headers(),json={'email':user+'@example.test','role':role})
        self.assertEqual(response.status_code,200,response.text);return response.json()['token']

    def join(self, user, token):
        return self.client.post('/api/account/join',headers=self.headers(user),json={'token':token})

    def status(self):
        return self.client.get('/api/account/license',headers=self.headers()).json()

    def test_first_admin_consumes_one_seat_and_edition_is_server_owned(self):
        self.create(1,'core');s=self.status()
        self.assertEqual((s['edition'],s['seat_limit'],s['seats_used'],s['seats_available']),('core',1,1,0))
        self.assertEqual(self.join('member',self.invite('member')).status_code,409)

    def test_admin_member_same_seat_rule_and_duplicate_join_is_idempotent(self):
        self.create();invite=self.invite('admin','admin')
        self.assertEqual(self.join('admin',invite).status_code,200)
        self.assertEqual(self.join('admin',invite).status_code,200)
        self.assertEqual(self.status()['seats_used'],2)
        blocked=self.invite('member')
        self.assertEqual(self.join('member',blocked).status_code,409)
        with self.db.connect() as db:
            self.assertIsNone(db.execute('SELECT accepted_by FROM invitations WHERE hash=?',(hashlib.sha256(blocked.encode()).hexdigest(),)).fetchone()['accepted_by'])

    def test_final_seat_is_atomic_under_concurrent_acceptance(self):
        self.create();invitations={u:self.invite(u) for u in ('member','other')}
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses=list(pool.map(lambda u:self.join(u,invitations[u]).status_code, invitations))
        self.assertEqual(sorted(responses),[200,409]);self.assertEqual(self.status()['seats_used'],2)

    def test_disable_frees_seat_reactivation_cannot_overbook_and_clock_is_denied(self):
        self.create();self.join('member',self.invite('member'))
        endpoint='/api/account/members/member'
        self.assertEqual(self.client.put(endpoint,headers=self.headers(),json={'role':'member','active':False}).status_code,200)
        self.assertEqual(self.client.get('/api/time/entries',headers=self.headers('member')).status_code,403)
        self.assertEqual(self.join('other',self.invite('other')).status_code,200)
        self.assertEqual(self.client.put(endpoint,headers=self.headers(),json={'role':'admin','active':True}).status_code,409)
        self.assertEqual(self.status()['seats_used'],2)

    def test_wrong_verified_buyer_cannot_redeem_or_consume_activation(self):
        code=self.accounts.issue_activation('core',seat_limit=3,purchaser_email='other@example.test')
        result=self.client.post('/api/account/organizations',headers=self.headers(),json={'name':'Wrong buyer','activation_code':code})
        self.assertEqual(result.status_code,403)
        with self.db.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM organizations').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM organization_entitlements').fetchone()[0],0)
            self.assertIsNone(db.execute('SELECT used_by FROM activation_codes').fetchone()[0])

    def test_redeem_retry_preserves_license_and_first_admin(self):
        self.create()
        retry=self.client.post('/api/account/organizations',headers=self.headers(),json={'name':'Different name','activation_code':self.code})
        self.assertEqual(retry.json()['id'],self.org);self.assertEqual(self.status()['seats_used'],1)

    def test_member_cannot_read_other_org_license_or_choose_a_larger_limit(self):
        self.create();self.join('member',self.invite('member'))
        self.assertEqual(self.client.get('/api/account/license',headers=self.headers('member')).status_code,403)
        self.assertEqual(self.client.get('/api/account/license',headers=self.headers('other')).status_code,403)
        self.assertEqual(self.client.post('/api/account/organizations',headers=self.headers(),json={'name':'Injection','activation_code':self.code,'seat_limit':999}).status_code,422)

    def test_invalid_allowances_and_explicit_legacy_status(self):
        for seats in (0,-1,True,1.5,100001):
            with self.assertRaises(ValueError):self.accounts.issue_activation('core',seat_limit=seats)
        with self.assertRaises(ValueError):self.accounts.issue_activation('core',purchaser_email='buyer@example.test')
        code=self.accounts.issue_activation('core')
        r=self.client.post('/api/account/organizations',headers=self.headers(),json={'name':'Legacy fixture','activation_code':code});self.org=r.json()['id']
        self.assertEqual(self.status()['licensing_status'],'legacy_unconfigured')
        self.assertIsNone(self.status()['seat_limit'])


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'),'Dedicated PostgreSQL test database not configured')
class PostgreSQLSeatLicensingTests(SeatLicensingTests):
    def storage(self, root):
        from psycopg.conninfo import make_conninfo
        from services.workspace_preview.postgres import PostgreSQLStorage
        dsn=os.environ['WZOS_TEST_DATABASE_URL'];schema='seats_'+uuid4().hex
        bootstrap=PostgreSQLStorage(dsn);self.addCleanup(bootstrap.close)
        with bootstrap.connect() as db:db.execute('CREATE SCHEMA '+schema)
        def cleanup():
            with bootstrap.connect() as db:db.execute('DROP SCHEMA '+schema+' CASCADE')
        self.addCleanup(cleanup)
        store=PostgreSQLStorage(make_conninfo(dsn,options='-c search_path='+schema));self.addCleanup(store.close)
        store.initialize();return store
