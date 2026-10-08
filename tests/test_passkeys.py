import hashlib
import json
import os
import struct
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import cbor2
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.workspace_preview.storage import SQLiteStorage
from services.workspace_preview.files import LocalFiles
from services.v2.knowledge.store import Store
from services.workspace_preview.passkeys import encode


class Provider:
    def __init__(self): self.uid='one'; self.age=0; self.disabled=False
    def __call__(self,token):
        if token!='valid':raise ValueError('invalid')
        return {'uid':self.uid,'email':self.uid+'@example.test','email_verified':True,'auth_time':time.time()-self.age}
    def passkey_token(self,uid):
        if self.disabled:raise ValueError('disabled')
        return 'custom-'+uid


class PasskeyTests(unittest.TestCase):
    def make_storage(self,root):return SQLiteStorage(root/'db.sqlite')
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);root=Path(self.temp.name)
        env=patch.dict(os.environ,{'WZOS_ACCOUNT_WORKSPACE':'1','WZOS_PASSKEY_ORIGIN':'http://localhost:8083','WZOS_PASSKEY_RP_ID':'localhost'})
        env.start();self.addCleanup(env.stop)
        self.storage=self.make_storage(root);self.provider=Provider()
        self.app=create_app(account_workspace=True,storage=self.storage,verifier=self.provider,file_store=LocalFiles(root/'files'),knowledge_store=Store(root/'sources',{}))
        self.client=TestClient(self.app,base_url='https://localhost:8083');self.addCleanup(self.client.close)
        self.headers={'X-WZOS-Session':'1','Origin':'http://localhost:8083'}
        self.fresh={**self.headers,'Authorization':'Bearer valid'}
        self.key=ec.generate_private_key(ec.SECP256R1());self.cid=b'credential-id-1234'
    def client_data(self,options,kind,origin='http://localhost:8083'):
        return json.dumps({'type':'webauthn.'+kind,'challenge':options['challenge'],'origin':origin}).encode()
    def registration(self,options,origin='http://localhost:8083',flags=0x45):
        numbers=self.key.public_key().public_numbers()
        cose=cbor2.dumps({1:2,3:-7,-1:1,-2:numbers.x.to_bytes(32,'big'),-3:numbers.y.to_bytes(32,'big')})
        data=hashlib.sha256(b'localhost').digest()+bytes([flags])+struct.pack('>I',0)+bytes(16)+struct.pack('>H',len(self.cid))+self.cid+cose
        return {'id':encode(self.cid),'rawId':encode(self.cid),'type':'public-key','response':{'clientDataJSON':encode(self.client_data(options,'create',origin)),'attestationObject':encode(cbor2.dumps({'fmt':'none','attStmt':{},'authData':data}))}}
    def enroll(self):
        result=self.client.post('/api/account/passkeys/register/options',headers=self.fresh)
        self.assertEqual(result.status_code,200,result.text)
        response=self.client.post('/api/account/passkeys/register/verify',headers=self.fresh,json={'credential':self.registration(result.json())})
        self.assertEqual(response.status_code,200,response.text)
    def authentication(self,options,origin='http://localhost:8083',flags=5,handle='one',count=1):
        client=self.client_data(options,'get',origin)
        data=hashlib.sha256(b'localhost').digest()+bytes([flags])+struct.pack('>I',count)
        signature=self.key.sign(data+hashlib.sha256(client).digest(),ec.ECDSA(hashes.SHA256()))
        return {'id':encode(self.cid),'rawId':encode(self.cid),'type':'public-key','response':{'clientDataJSON':encode(client),'authenticatorData':encode(data),'signature':encode(signature),'userHandle':encode(hashlib.sha256(handle.encode()).digest())}}
    def test_signed_enrollment_login_and_replay(self):
        self.enroll()
        options=self.client.post('/api/account/passkeys/login/options',headers=self.headers).json()
        body={'credential':self.authentication(options)}
        result=self.client.post('/api/account/passkeys/login/verify',headers=self.headers,json=body)
        self.assertEqual(result.status_code,200,result.text);self.assertEqual(result.json(),{'custom_token':'custom-one'})
        self.assertEqual(result.headers['cache-control'],'no-store')
        self.assertEqual(self.client.post('/api/account/passkeys/login/verify',headers=self.headers,json=body).status_code,401)
    def test_auth_origin_signature_handle_and_uv_fail_closed(self):
        self.enroll()
        for change in ('origin','signature','handle','uv','challenge'):
            options=self.client.post('/api/account/passkeys/login/options',headers=self.headers).json()
            if change=='challenge':options['challenge']='incorrect'
            body=self.authentication(options,origin='https://evil.example' if change=='origin' else 'http://localhost:8083',handle='other' if change=='handle' else 'one',flags=1 if change=='uv' else 5)
            if change=='signature':body['response']['signature']=encode(b'bad-signature')
            result=self.client.post('/api/account/passkeys/login/verify',headers=self.headers,json={'credential':body})
            self.assertEqual(result.status_code,401,(change,result.text))
    def test_registration_origin_uv_recent_auth_and_headers(self):
        self.provider.age=301
        self.assertEqual(self.client.post('/api/account/passkeys/register/options',headers=self.fresh).status_code,401)
        self.provider.age=0
        self.assertEqual(self.client.post('/api/account/passkeys/register/options',headers={'Authorization':'Bearer valid'}).status_code,403)
        for origin,flags in [('https://evil.example',0x45),('http://localhost:8083',0x41)]:
            options=self.client.post('/api/account/passkeys/register/options',headers=self.fresh).json()
            self.assertEqual(self.client.post('/api/account/passkeys/register/verify',headers=self.fresh,json={'credential':self.registration(options,origin,flags)}).status_code,400)
    def test_expired_challenge_and_cookie_binding(self):
        self.enroll();options=self.client.post('/api/account/passkeys/login/options',headers=self.headers).json()
        body={'credential':self.authentication(options)}
        with TestClient(self.app,base_url='https://localhost:8083') as other:
            self.assertEqual(other.post('/api/account/passkeys/login/verify',headers=self.headers,json=body).status_code,401)
        with self.storage.connect() as db:db.execute('UPDATE passkey_challenges SET expires_at=0')
        self.assertEqual(self.client.post('/api/account/passkeys/login/verify',headers=self.headers,json=body).status_code,401)
    def test_removal_is_account_scoped_and_revokes_remembered_sessions(self):
        self.enroll();self.provider.uid='other'
        self.assertEqual(self.client.get('/api/account/passkeys',headers=self.fresh).json()['items'],[])
        path='/api/account/passkeys/'+encode(self.cid)
        self.assertEqual(self.client.delete(path,headers=self.fresh).status_code,404)
        self.provider.uid='one'
        with self.storage.connect() as db:db.execute('INSERT INTO browser_sessions VALUES (?,?,?)',('hash','one','2099'))
        self.assertEqual(self.client.delete(path,headers=self.fresh).status_code,200)
        with self.storage.connect() as db:self.assertEqual(db.execute('SELECT COUNT(*) AS n FROM browser_sessions').fetchone()['n'],0)
    def test_disabled_provider_and_counter_rollback(self):
        self.enroll();self.provider.disabled=True
        options=self.client.post('/api/account/passkeys/login/options',headers=self.headers).json()
        self.assertEqual(self.client.post('/api/account/passkeys/login/verify',headers=self.headers,json={'credential':self.authentication(options)}).status_code,503)
        self.provider.disabled=False
        options=self.client.post('/api/account/passkeys/login/options',headers=self.headers).json()
        self.assertEqual(self.client.post('/api/account/passkeys/login/verify',headers=self.headers,json={'credential':self.authentication(options,count=1)}).status_code,401)
    def test_enrollment_challenge_cannot_switch_accounts(self):
        options=self.client.post('/api/account/passkeys/register/options',headers=self.fresh).json();self.provider.uid='other'
        self.assertEqual(self.client.post('/api/account/passkeys/register/verify',headers=self.fresh,json={'credential':self.registration(options)}).status_code,401)


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'),'Dedicated PostgreSQL database not configured')
class PostgreSQLPasskeyTests(PasskeyTests):
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
