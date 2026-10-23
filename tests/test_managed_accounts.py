import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from tests import test_accounts_storage
from services.workspace_preview.managed_accounts import issue_organization_grant


class FakeProvider:
    def __init__(self, claims):
        self.claims = claims
        self.users = {}
        self.created = 0
        self.fail_enable = False

    def __call__(self, token):
        if token in self.users and self.users[token].disabled:
            raise ValueError('Disabled')
        return self.claims[token]

    def create_managed(self, uid, email, password, name):
        if any(u.email == email for u in self.users.values()):
            raise ValueError('Existing provider account')
        self.users[uid] = SimpleNamespace(email=email, disabled=True)
        self.claims[uid] = {'uid':uid, 'email':email, 'email_verified':False, 'name':name}
        self.created += 1

    def get_managed(self, uid):
        return self.users[uid]

    def enable_managed(self, uid):
        if self.fail_enable:
            raise RuntimeError('Provider unavailable')
        self.users[uid].disabled = False

    def change_managed_password(self, uid, password):
        assert uid in self.users


class ManagedAccountsTests(unittest.TestCase):
    make_storage = test_accounts_storage.AccountStorageTests.make_storage
    build = test_accounts_storage.AccountStorageTests.build
    create_org = test_accounts_storage.AccountStorageTests.create_org
    headers = test_accounts_storage.AccountStorageTests.headers
    add = test_accounts_storage.AccountStorageTests.add

    def setUp(self):
        test_accounts_storage.AccountStorageTests.setUp(self)
        self.provider = FakeProvider(self.claims)
        self.app.state.accounts.verify = self.provider
        self.payload = {'request_id':str(uuid4()),'name':'Test Employee','email':'employee@example.test',
                        'username':'test.employee','password':'Synthetic-only-pass-42','role':'member'}

    def provision(self, who='creator', payload=None, org=None):
        return self.client.post('/api/account/managed/accounts', headers=self.headers(who,org), json=payload or self.payload)

    def test_admin_provisions_without_invitation_first_password_required(self):
        result = self.provision(); self.assertEqual(result.status_code,200,result.text)
        uid=result.json()['id']; self.assertFalse(result.json()['invitation_required'])
        self.assertEqual(self.provision().json(),result.json());self.assertEqual(self.provider.created,1)
        self.assertTrue(self.client.get('/api/account',headers=self.headers(uid)).json()['password_change_required'])
        self.assertEqual(self.client.get('/api/orders',headers=self.headers(uid)).status_code,403)
        self.assertEqual(self.client.post('/api/account/managed/password',headers=self.headers(uid),json={'password':'My-private-new-pass-42'}).status_code,200)
        self.assertEqual(self.client.get('/api/orders',headers=self.headers(uid)).status_code,200)
        with self.app.state.accounts.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM invitations').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT role FROM memberships WHERE user_id=?',(uid,)).fetchone()[0],'member')
            saved=str([dict(r) for r in db.execute('SELECT * FROM managed_accounts').fetchall()])
        self.assertNotIn(self.payload['password'],saved)

    def test_member_foreign_and_role_denial(self):
        self.add('member')
        self.assertEqual(self.provision('member').status_code,403)
        self.assertEqual(self.provision('other').status_code,403)
        self.assertEqual(self.provision(payload={**self.payload,'role':'manager'}).status_code,422)
        self.assertEqual(self.provider.created,0)

    def test_capacity_and_existing_personal_identity_not_overwritten(self):
        with self.app.state.accounts.connect() as db:
            db.execute('INSERT INTO organization_entitlements VALUES (?,?,1)',(self.org,'seat-test'))
        self.assertEqual(self.provision().status_code,409)
        self.assertEqual(self.provider.created,0)
        self.assertEqual(self.provision(payload={**self.payload,'email':'creator@example.test'}).status_code,409)

    def test_duplicate_email_at_provider_does_not_grant_membership(self):
        self.provider.users['unrelated']=SimpleNamespace(email=self.payload['email'],disabled=False)
        self.assertEqual(self.provision().status_code,409)
        with self.app.state.accounts.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM managed_accounts').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM memberships WHERE organization_id=?',(self.org,)).fetchone()[0],1)

    def test_pending_setup_retry_preserves_identity_and_request_details(self):
        self.provider.fail_enable=True
        self.assertEqual(self.provision().status_code,503)
        uid=next(iter(self.provider.users));self.assertTrue(self.provider.users[uid].disabled)
        self.assertEqual(self.provision(payload={**self.payload,'role':'admin'}).status_code,409)
        self.provider.fail_enable=False
        self.assertEqual(self.provision().status_code,200);self.assertEqual(self.provider.created,1)

    def test_validation_never_echoes_password(self):
        for body in [{**self.payload,'username':'@bad'}, {**self.payload,'role':'owner'}, {**self.payload,'password':'short'}]:
            r=self.provision(payload=body);self.assertEqual(r.status_code,422)
            self.assertNotIn(body['password'],r.text)

    def test_username_login_generic_and_throttled(self):
        uid=self.provision().json()['id']
        data={'idToken':'synthetic-token','refreshToken':'synthetic-refresh','expiresIn':'3600','localId':uid}
        with patch('services.workspace_preview.managed_accounts.password_sign_in',return_value=data.copy()) as provider:
            r=self.client.post('/api/account/managed/sign-in',json={'username':'TEST.EMPLOYEE','password':'synthetic-pass'})
            self.assertEqual(r.status_code,200,r.text);self.assertNotIn('email',r.json());self.assertIn('no-store',r.headers['cache-control'])
            provider.assert_called_once()
        for _ in range(10):
            r=self.client.post('/api/account/managed/sign-in',json={'username':'missing','password':'synthetic-pass'})
            self.assertEqual(r.status_code,401)
        self.assertEqual(self.client.post('/api/account/managed/sign-in',json={'username':'missing','password':'synthetic-pass'}).status_code,429)

    def test_unverified_managed_cannot_claim_email_for_new_organization_or_invitation(self):
        uid=self.provision().json()['id']
        self.client.post('/api/account/managed/password',headers=self.headers(uid),json={'password':'My-private-new-pass-42'})
        issue_organization_grant(self.app.state.accounts,self.payload['email'],'enterprise',25)
        r=self.client.post('/api/account/organizations',headers=self.headers(uid),json={'name':'Forbidden'})
        self.assertEqual(r.status_code,403)
        code=self.app.state.accounts.issue_activation('enterprise')
        self.assertEqual(self.client.post('/api/account/organizations',headers=self.headers(uid),json={'name':'Forbidden','activation_code':code}).status_code,403)

    def test_email_bound_grant_single_use_seats_and_no_global_bypass(self):
        grant=issue_organization_grant(self.app.state.accounts,'other@example.test','enterprise',25)
        self.assertIsNone(self.client.get('/api/account',headers=self.headers()).json()['organization_creation_grant'])
        self.assertEqual(self.client.post('/api/account/organizations',headers=self.headers(),json={'name':'No approval'}).status_code,403)
        self.claims['other']['email_verified']=False
        self.assertEqual(self.client.post('/api/account/organizations',headers=self.headers('other'),json={'name':'Test company'}).status_code,403)
        self.claims['other']['email_verified']=True
        r=self.client.post('/api/account/organizations',headers=self.headers('other'),json={'name':'Test company'})
        self.assertEqual(r.status_code,200,r.text);org=r.json()['id']
        self.assertEqual(self.client.post('/api/account/organizations',headers=self.headers('other'),json={'name':'Test company'}).json()['id'],org)
        self.assertEqual(self.client.get('/api/account/license',headers=self.headers('other',org)).json()['seat_limit'],25)
        with self.app.state.accounts.connect() as db:
            self.assertEqual(db.execute('SELECT organization_id FROM organization_creation_grants WHERE id=?',(grant,)).fetchone()[0],org)


@unittest.skipUnless(os.environ.get('WZOS_TEST_DATABASE_URL'),'PostgreSQL test database required')
class PostgreSQLManagedAccountsTests(ManagedAccountsTests):
    make_storage = test_accounts_storage.PostgreSQLAccountStorageTests.make_storage
