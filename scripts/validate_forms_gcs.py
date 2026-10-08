"""Operator-only Forms integration gate using the existing private staging bucket.
Synthetic identities and a temporary local DB; validates real GCS, not live auth/IAM.
"""
import hashlib, os, sys, tempfile
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.workspace_preview.files import GoogleFiles
from services.v2.knowledge.store import Store

def main():
    if os.getenv('K_SERVICE'):raise SystemExit('Operator test only')
    os.environ['WZOS_WORKSPACE_PREVIEW']='1'
    files=GoogleFiles('enterprise-gemma2-wzos-v2-files-staging')
    item,fid=str(uuid4()),str(uuid4())
    admin={'X-Preview-Actor':'enterprise-admin'};member={'X-Preview-Actor':'enterprise-general'}
    payload=b'%PDF-1.7\n% synthetic private storage acceptance\n'
    keys=[]
    original_put=files.put
    def tracked_put(key,*args):
        keys.append(key);return original_put(key,*args)
    files.put=tracked_put
    try:
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            def app():return create_app(root/'db',Store(root/'sources',{}),file_store=files)
            with TestClient(app()) as client:
                body={'expected_version':0,'title':'Synthetic private storage test','category':'company_form','description':'Disposable acceptance fixture','file_id':None,'link':None}
                assert client.put('/api/forms/library/'+item,headers=admin,json=body).status_code==200
                path='/api/files/'+fid
                params={'entity_kind':'form_library','entity_id':item,'filename':'synthetic.pdf'}
                r=client.put(path,params=params,headers={**admin,'Content-Type':'application/pdf'},content=payload)
                assert r.status_code==200,r.status_code
                assert r.json()['sha256']==hashlib.sha256(payload).hexdigest()
                assert client.get(path,headers=member).status_code==404
                assert client.put('/api/forms/library/'+item,headers=admin,json={**body,'expected_version':1,'file_id':fid}).status_code==200
                assert client.get(path,headers=member).content==payload
                assert client.get(path,headers={'X-Preview-Actor':'core-admin'}).status_code==404
                assert client.post('/api/forms/library/'+item+'/delete',headers=member,json={'expected_version':2}).status_code==403
            with TestClient(app()) as client:
                assert client.get(path,headers=member).content==payload
            print('PASS: real private GCS form upload, checksum, publication, member access, tenant denial and restart persistence')
    finally:
        for key in set(keys):
            files.delete(key)
            assert not files.bucket.blob(key).exists(timeout=20),'Test cleanup failed'
        print('CLEANUP: synthetic test objects removed')
if __name__=='__main__':main()
