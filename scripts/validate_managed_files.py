"""Synthetic private-file acceptance against the named restricted staging service.

Requires an active operator fixture from validate_managed_accounts.py. No emails,
public ACLs, signed public links, or customer uploads. Re-run verify after deployment.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4
import requests
from validate_managed_accounts import gc, PROJECT, SERVICE, ORIGIN

BUCKET = 'enterprise-gemma2-wzos-v2-files-staging'
# One-pixel PNG, immutable synthetic content (no location or personal information).
DATA = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAX+XDSwAAAABJRU5ErkJggg==')


def save(path, value):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f: json.dump(value,f,indent=2)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['upload','verify'])
    parser.add_argument('--state',required=True,type=Path)
    parser.add_argument('--evidence',required=True,type=Path)
    parser.add_argument('--require-new-revision',action='store_true')
    args=parser.parse_args()
    state=json.loads(args.state.read_text())
    if state.get('disabled'): raise SystemExit('Use active synthetic fixtures')
    iam=gc('auth','print-identity-token')
    url=gc('run','services','describe',SERVICE,'--region=us-central1','--format=value(status.url)')
    revision=gc('run','services','describe',SERVICE,'--region=us-central1','--format=value(status.latestReadyRevisionName)')
    key=gc('secrets','versions','access','latest','--secret=wzos-v2-staging-auth-web-key')
    for who in ('admin','member','other'):
        try:
            r=requests.post('https://securetoken.googleapis.com/v1/token',params={'key':key},data={'grant_type':'refresh_token','refresh_token':state['users'][who]['refreshToken']},headers={'Referer':ORIGIN+'/'},timeout=30)
        except requests.RequestException: raise RuntimeError('Provider refresh unavailable') from None
        assert r.status_code==200, 'Provider refresh failed'
        token=r.json();state['users'][who].update(idToken=token['id_token'],refreshToken=token['refresh_token'])
    save(args.state,state)
    config=requests.get(url+'/api/identities',headers={'X-Serverless-Authorization':'Bearer '+iam},timeout=30)
    assert config.status_code==200
    auth_header=config.json().get('auth_header','Authorization')
    assert auth_header in ('Authorization','X-WZOS-Authorization')
    def call(path, who='member', expected=200, method='GET', **kwargs):
        org=state['orgs']['other' if who=='other' else 'main']
        h={auth_header:'Bearer '+state['users'][who]['idToken'],'X-Serverless-Authorization':'Bearer '+iam,'X-WZOS-Organization':org,'Origin':ORIGIN}
        h.update(kwargs.pop('headers',{}))
        r=requests.request(method,url+path,headers=h,timeout=40,**kwargs)
        assert r.status_code==expected, path+' expected '+str(expected)+' got '+str(r.status_code)
        return r
    if args.action=='upload':
        if 'file_fixture' not in state:
            state['file_fixture']={'request_id':str(uuid4()),'file_id':str(uuid4()),'original_revision':revision}
            save(args.state,state)
        fixture=state['file_fixture']
        body={'request_id':fixture['request_id'],'title':'Synthetic private-file acceptance','work_type':'other','address':'Synthetic test road','locality':'Norfolk'}
        fixture['order_id']=call('/api/orders',method='POST',expected=201,json=body).json()['id']
        save(args.state,state)
        path='/api/files/'+fixture['file_id']
        params={'entity_kind':'order','entity_id':fixture['order_id'],'filename':'synthetic-site.png'}
        uploaded=call(path,method='PUT',params=params,data=DATA,headers={'Content-Type':'image/png'}).json()
        assert uploaded['sha256']==hashlib.sha256(DATA).hexdigest()
        assert call(path,method='PUT',params=params,data=DATA,headers={'Content-Type':'image/png'}).json()==uploaded
        call(path,method='PUT',params=params,data=DATA+b'conflict',headers={'Content-Type':'image/png'},expected=409)
        call('/api/files/'+str(uuid4()),method='PUT',params=params,data=b'not-a-png',headers={'Content-Type':'image/png'},expected=415)
    fixture=state['file_fixture'];path='/api/files/'+fixture['file_id']
    if args.require_new_revision: assert revision!=fixture['original_revision'], 'Deploy a new revision before persistence acceptance'
    for who in ('member','admin'):
        r=call(path,who)
        assert r.content==DATA, 'Downloaded bytes differ'
        assert r.headers['Content-Disposition'].startswith('attachment;')
        assert r.headers['X-Content-Type-Options']=='nosniff'
        assert r.headers['Cache-Control']=='no-store'
    call(path,'other',expected=404)
    listed=call('/api/files',params={'entity_kind':'order','entity_id':fixture['order_id']}).json()
    assert fixture['file_id'] in [f['id'] for f in listed['items']]
    call('/api/files','other',expected=404,params={'entity_kind':'order','entity_id':fixture['order_id']})
    object_key=hashlib.sha256(state['orgs']['main'].encode()).hexdigest()+'/'+fixture['file_id']
    public=requests.get('https://storage.googleapis.com/'+BUCKET+'/'+quote(object_key,safe='/'),timeout=30)
    assert public.status_code==403, 'Anonymous object access must be denied'
    anonymous=requests.get(url+path,timeout=30)
    assert anonymous.status_code==403, 'Anonymous service access must be denied'
    from google.cloud import storage
    blob=storage.Client(project=PROJECT).bucket(BUCKET).get_blob(object_key,timeout=30)
    assert blob and blob.metadata['sha256']==hashlib.sha256(DATA).hexdigest()
    evidence={**fixture,'current_revision':revision,'organization_id':state['orgs']['main'],'bucket':BUCKET,'object_key':object_key,'generation':str(blob.generation),'sha256':hashlib.sha256(DATA).hexdigest(),'size_bytes':len(DATA),'anonymous_object_status':public.status_code,'anonymous_service_status':anonymous.status_code,'cross_organization_status':404,'passed':True}
    save(args.evidence,evidence)
    print('PASS: private upload/download, SHA-256, idempotency/conflict, MIME rejection, admin/member, tenant isolation and anonymous denial; revision',revision)


if __name__=='__main__': main()
