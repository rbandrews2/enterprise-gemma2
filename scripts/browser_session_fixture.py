"""Loopback-only synthetic provider for browser cookie transport checks.
Not Google emulator acceptance; never use real credentials or deploy this runner.
"""
import argparse, os, sys, tempfile, time, threading, secrets
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.workspace_preview.app import create_app
from services.workspace_preview.storage import SQLiteStorage
from services.workspace_preview.files import LocalFiles
from services.v2.knowledge.store import Store

class Provider:
    def __init__(self): self.cookies={}
    def __call__(self, token):
        if token!='synthetic-token': raise ValueError('invalid')
        return {'uid':'browser-member','email':'member@example.test','email_verified':True,'auth_time':time.time()}
    def create_session(self,token,lifetime):
        cookie=secrets.token_urlsafe(32);self.cookies[cookie]=self(token);return cookie
    def verify_session(self,cookie):return self.cookies[cookie]

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role',choices=['member','admin'],default='member')
    parser.add_argument('--port',type=int,choices=[8081,8083],default=8083)
    args=parser.parse_args()
    if any(os.getenv(k) for k in ('K_SERVICE','GAE_ENV','NETLIFY')):raise SystemExit('Loopback only')
    os.environ.update(WZOS_ACCOUNT_WORKSPACE='1',WZOS_AUTH_EMULATOR='1',FIREBASE_AUTH_EMULATOR_HOST='127.0.0.1:9099',WZOS_AUTH_PROJECT='demo-browser-check',WZOS_AUTH_WEB_API_KEY='synthetic')
    provider=FastAPI()
    provider.add_middleware(CORSMiddleware,allow_origins=[f'http://localhost:{args.port}'],allow_methods=['POST'],allow_headers=['Content-Type'])
    @provider.post('/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword')
    def sign_in(body:dict):
        if body.get('email')!='member@example.test' or body.get('password')!='synthetic-only':raise HTTPException(401)
        return {'idToken':'synthetic-token','refreshToken':'synthetic-refresh','expiresIn':'3600'}
    with tempfile.TemporaryDirectory(prefix='wzos-browser-') as directory:
        root=Path(directory);storage=SQLiteStorage(root/'db.sqlite')
        app=create_app(account_workspace=True,storage=storage,verifier=Provider(),file_store=LocalFiles(root/'files'),knowledge_store=Store(root/'sources',{}))
        # Browser tooling can restrict secondary loopback ports. Route only the
        # synthetic provider through this fixture's same-origin endpoint.
        from fastapi.responses import Response
        @app.middleware('http')
        async def fixture_transport(request, call_next):
            if request.url.path=='/account.js':
                script=(Path(__file__).resolve().parents[1]/'services/workspace_preview/static/account.js').read_text()
                script=script.replace("authBase=config.auth_emulator+'/identitytoolkit.googleapis.com'", "authBase=location.origin+'/identitytoolkit.googleapis.com'")
                return Response(script,media_type='text/javascript')
            return await call_next(request)
        app.add_api_route('/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword',sign_in,methods=['POST'])
        with storage.connect() as db:
            db.execute('INSERT INTO organizations VALUES (?,?,?,?)',('browser-org','Synthetic browser checks','enterprise',1))
            db.execute('INSERT INTO memberships VALUES (?,?,?,?)',('browser-org','browser-member',args.role,1))
        thread=threading.Thread(target=lambda:uvicorn.run(provider,host='127.0.0.1',port=9099,log_level='warning'),daemon=True);thread.start()
        uvicorn.run(app,host='127.0.0.1',port=args.port,log_level='warning')
