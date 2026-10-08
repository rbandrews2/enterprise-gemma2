"""Real-provider restricted-staging auth probe; synthetic cryptographic ceremonies.
No real biometric/device acceptance. Creates one identity and disables it on exit.
No organization memberships, messages or customer records are created.
"""
import base64,hashlib,json,secrets,struct,subprocess,sys,time
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cbor2,requests,firebase_admin
from firebase_admin import auth,credentials
from google.oauth2.credentials import Credentials
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
PROJECT='enterprise-gemma2'
ORIGIN='https://8080-cs-1002772085547-default.cs-us-east1-pkhd.cloudshell.dev'
HOST=ORIGIN.split('://')[1]
def gc(*args):return subprocess.check_output(['gcloud',*args,'--project='+PROJECT],text=True).strip()
def enc(b):return base64.urlsafe_b64encode(b).rstrip(b'=').decode()
class OperatorCredential(credentials.Base):
    def get_credential(self):return Credentials(gc('auth','print-access-token'),quota_project_id=PROJECT)
def main():
    provider=firebase_admin.initialize_app(OperatorCredential(),options={'projectId':PROJECT})
    uid=None;passed=False;removed=False;client=requests.Session()
    key=gc('secrets','versions','access','latest','--secret=wzos-v2-staging-auth-web-key')
    url=gc('run','services','describe','wzos-v2-accounts','--region=us-central1','--format=value(status.url)')
    client.headers.update({'X-Serverless-Authorization':'Bearer '+gc('auth','print-identity-token'),'Origin':ORIGIN,'X-WZOS-Session':'1'})
    def api(path,body=None,method='POST',expected=200):
        r=client.request(method,url+path,json=body,timeout=40)
        assert r.status_code==expected,f'{path}: status {r.status_code}, expected {expected}'
        return r
    def google(action,body):
        r=requests.post('https://identitytoolkit.googleapis.com/v1/accounts:'+action,params={'key':key},headers={'Referer':ORIGIN+'/'},json=body,timeout=30)
        assert r.status_code==200,'Google exchange failed: '+str(r.status_code)
        return r.json()
    try:
        email='wzos-passkey-probe-'+uuid4().hex+'@example.test';password=secrets.token_urlsafe(32)
        uid=auth.create_user(email=email,password=password,email_verified=True,app=provider).uid
        token=google('signInWithPassword',{'email':email,'password':password,'returnSecureToken':True})['idToken']
        client.headers['X-WZOS-Authorization']='Bearer '+token
        private=ec.generate_private_key(ec.SECP256R1());cid=secrets.token_bytes(32)
        options=api('/api/account/passkeys/register/options').json()
        numbers=private.public_key().public_numbers()
        cose=cbor2.dumps({1:2,3:-7,-1:1,-2:numbers.x.to_bytes(32,'big'),-3:numbers.y.to_bytes(32,'big')})
        def cdata(kind,challenge):return json.dumps({'type':'webauthn.'+kind,'challenge':challenge,'origin':ORIGIN}).encode()
        data=hashlib.sha256(HOST.encode()).digest()+bytes([0x45])+struct.pack('>I',0)+bytes(16)+struct.pack('>H',len(cid))+cid+cose
        credential={'id':enc(cid),'rawId':enc(cid),'type':'public-key','response':{'clientDataJSON':enc(cdata('create',options['challenge'])),'attestationObject':enc(cbor2.dumps({'fmt':'none','attStmt':{},'authData':data}))}}
        api('/api/account/passkeys/register/verify',{'credential':credential,'label':'Disposable operator probe'})
        del client.headers['X-WZOS-Authorization']
        options=api('/api/account/passkeys/login/options').json();cd=cdata('get',options['challenge'])
        data=hashlib.sha256(HOST.encode()).digest()+bytes([5])+struct.pack('>I',1)
        signature=private.sign(data+hashlib.sha256(cd).digest(),ec.ECDSA(hashes.SHA256()))
        credential={'id':enc(cid),'rawId':enc(cid),'type':'public-key','response':{'clientDataJSON':enc(cd),'authenticatorData':enc(data),'signature':enc(signature),'userHandle':enc(hashlib.sha256(uid.encode()).digest())}}
        result=api('/api/account/passkeys/login/verify',{'credential':credential}).json()
        exchanged=google('signInWithCustomToken',{'token':result['custom_token'],'returnSecureToken':True})
        assert exchanged['localId']==uid,'Custom token identity mismatch'
        api('/api/account/passkeys/login/verify',{'credential':credential},expected=401)
        client.headers['X-WZOS-Authorization']='Bearer '+exchanged['idToken']
        api('/api/account/passkeys/'+enc(cid),method='DELETE')
        removed=True
        print('PASS: restricted runtime token signing and Google custom-token exchange')
        response=api('/api/account/session')
        cookie_header=response.headers.get('Set-Cookie','')
        assert all(flag in cookie_header for flag in ('Secure','HttpOnly','SameSite=strict')),'Cookie security flags missing'
        del client.headers['X-WZOS-Authorization']
        api('/api/account',method='GET')
        api('/api/account/logout')
        api('/api/account',method='GET',expected=401)
        passed=True
        print('PASS: real Google sign-in, restricted runtime passkey verification/signing, Google custom-token exchange, replay denial and credential removal')
    except Exception as exc:
        print('AUTH PROBE FAILED: '+str(exc) if isinstance(exc,AssertionError) else 'AUTH PROBE FAILED: '+type(exc).__name__+' (credentials suppressed)')
    finally:
        if uid:
            auth.update_user(uid,disabled=True,app=provider);auth.revoke_refresh_tokens(uid,app=provider)
            print('CLEANUP: synthetic identity disabled and tokens revoked; credential_removed='+str(removed))
        client.close();firebase_admin.delete_app(provider)
    return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())

