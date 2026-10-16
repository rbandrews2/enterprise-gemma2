import hashlib
import json
import os
import unittest
from uuid import uuid4
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from services.workspace_preview.scanner_transport import RemoteScanner, scanner_origin
from services.workspace_preview.scanner_service import create_app
from services.workspace_preview.security import ScanResult, configured_scanner

ORIGIN = 'https://wzos-scanner-synthetic.run.app'
CALLER = 'wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com'
TOKEN = 'synthetic.google.token'
DATA = b'%PDF-1.7 synthetic test only'


class Engine:
    def __init__(self, status='clean'):
        self.status, self.calls = status, []
    def scan(self, data):
        self.calls.append(data)
        return ScanResult(self.status, 'ClamAV 1.5.4/28154')


def claims(token, audience):
    if token != TOKEN:
        raise ValueError('private credentials must never appear in errors')
    return {'email':CALLER, 'email_verified':True, 'sub':'12345',
            'aud':audience, 'iss':'https://accounts.google.com'}


def headers(data=DATA):
    return {'Authorization':'Bearer '+TOKEN, 'Content-Type':'application/octet-stream',
            'X-Scan-Request':str(uuid4()), 'X-Content-SHA256':hashlib.sha256(data).hexdigest()}


class ScannerServiceTests(unittest.TestCase):
    def client(self, engine=None, verifier=claims):
        return TestClient(create_app(audience=ORIGIN, caller=CALLER, verifier=verifier,
                                     scanner=engine or Engine()))

    def test_identity_before_body_and_no_browser_access(self):
        engine = Engine()
        with self.client(engine) as client:
            self.assertEqual(client.post('/scan', content=DATA).status_code,401)
            rejected = headers(); rejected['Authorization']='Bearer wrong.synthetic.token'
            response = client.post('/scan',headers=rejected,content=DATA)
            self.assertEqual(response.status_code,403)
            self.assertNotIn('private credentials',response.text)
            self.assertEqual(client.get('/docs').status_code,404)
            self.assertEqual(client.get('/healthz').json(),{'status':'alive'})
        self.assertEqual(engine.calls,[])

    def test_wrong_caller_audience_issuer_and_unverified_identity(self):
        for key,value in [('email','another@enterprise-gemma2.iam.gserviceaccount.com'),
                          ('email_verified',False),('aud','https://another.run.app'),
                          ('iss','https://untrusted.example'),('sub','')]:
            def changed(token,audience):
                return {**claims(token,audience),key:value}
            with self.client(verifier=changed) as client:
                self.assertEqual(client.post('/scan',headers=headers(),content=DATA).status_code,403)

    def test_exact_hash_size_and_request_contract(self):
        engine = Engine('infected')
        with self.client(engine) as client:
            h = headers()
            response=client.post('/scan',headers=h,content=DATA)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json(),{'version':1,'request_id':h['X-Scan-Request'],
                'sha256':hashlib.sha256(DATA).hexdigest(),'byte_count':len(DATA),
                'status':'infected','engine':'ClamAV 1.5.4/28154'})
            self.assertEqual(response.headers['cache-control'],'no-store')
        self.assertEqual(engine.calls,[DATA])

    def test_malformed_integrity_size_and_encoding_never_scan(self):
        engine = Engine()
        changes = [{'X-Content-SHA256':'0'*64},{'X-Scan-Request':'not-a-uuid'},
                   {'Content-Type':'application/json'},{'Content-Encoding':'gzip'},
                   {'Content-Length':'10485761'},{'Content-Length':'1'},
                   {'Content-Length':str(len(DATA)+1)}]
        with self.client(engine) as client:
            for change in changes:
                h = {**headers(),**change}
                self.assertIn(client.post('/scan',headers=h,content=DATA).status_code,(400,413))
        self.assertEqual(engine.calls,[])

    def test_unknown_unavailable_or_bad_engine_result_never_clean(self):
        with self.client(Engine('unavailable')) as client:
            self.assertEqual(client.post('/scan',headers=headers(),content=DATA).status_code,503)
        with self.client(Engine('error')) as client:
            result=client.post('/scan',headers=headers(),content=DATA).json()
            self.assertEqual((result['status'],result['engine']),('error',''))


class RemoteScannerTests(unittest.TestCase):
    def scanner(self, handler, token_provider=lambda audience:TOKEN):
        with patch.dict(os.environ,{'WZOS_SCANNER_URL':ORIGIN}):
            return RemoteScanner(token_provider=token_provider,transport=httpx.MockTransport(handler))

    def reply(self, request, **changes):
        result={'version':1,'request_id':request.headers['x-scan-request'],
                'sha256':hashlib.sha256(request.content).hexdigest(),'byte_count':len(request.content),
                'status':'clean','engine':'ClamAV 1.5.4/28154',**changes}
        return httpx.Response(200,stream=httpx.ByteStream(json.dumps(result).encode()),
                              headers={'content-type':'application/json'})

    def test_service_and_client_round_trip(self):
        engine=Engine()
        with TestClient(create_app(audience=ORIGIN,caller=CALLER,verifier=claims,scanner=engine)) as service:
            def handler(request):
                self.assertEqual(str(request.url),ORIGIN+'/scan')
                self.assertEqual(request.headers['authorization'],'Bearer '+TOKEN)
                self.assertEqual(request.headers['x-serverless-authorization'],'Bearer '+TOKEN)
                response=service.post('/scan',headers=dict(request.headers),content=request.content)
                return httpx.Response(response.status_code,headers=response.headers,
                                      stream=httpx.ByteStream(response.content))
            self.assertEqual(self.scanner(handler).scan(DATA),ScanResult('clean','ClamAV 1.5.4/28154'))
        self.assertEqual(engine.calls,[DATA])

    def test_binding_schema_engine_and_status_mismatches_are_held(self):
        for change in ({'request_id':str(uuid4())},{'sha256':'0'*64},{'byte_count':0},
                       {'version':True},{'byte_count':True},{'extra':'unexpected'},
                       {'status':'unavailable'},{'engine':''},{'engine':'private details'}):
            self.assertEqual(self.scanner(lambda request:self.reply(request,**change)).scan(DATA).status,'error')

    def test_redirect_error_oversized_and_malformed_responses_do_not_retry(self):
        for status,body,extra in [(302,b'',{'location':'https://untrusted.example'}),
                                  (503,b'private server details',{}),(200,b'not json',{}),
                                  (200,b' '*4097,{}),(200,b'{}',{'content-encoding':'gzip'})]:
            calls=[]
            def handler(request):
                calls.append(request)
                return httpx.Response(status,stream=httpx.ByteStream(body),
                                      headers={'content-type':'application/json',**extra})
            self.assertEqual(self.scanner(handler).scan(DATA).status,'error')
            self.assertEqual(len(calls),1)

    def test_missing_identity_timeout_and_total_deadline_are_held(self):
        self.assertEqual(self.scanner(lambda request:self.reply(request),lambda audience:'').scan(DATA).status,'error')
        def timeout(request): raise httpx.ReadTimeout('private details')
        self.assertEqual(self.scanner(timeout).scan(DATA).status,'error')
        with patch('services.workspace_preview.scanner_transport.monotonic',side_effect=[0,71]):
            self.assertEqual(self.scanner(lambda request:self.reply(request)).scan(DATA).status,'error')

    def test_verified_cold_start_response_fits_bounded_service_wait(self):
        calls=[]
        def delayed(request):
            calls.append(request)
            self.assertEqual(request.extensions['timeout']['read'],65)
            self.assertEqual(request.extensions['timeout']['connect'],5)
            return self.reply(request)
        # Real Cloud Run acceptance observed a valid response after31.76s.
        with patch('services.workspace_preview.scanner_transport.monotonic',
                   side_effect=[0,31.76,31.76]):
            self.assertEqual(self.scanner(delayed).scan(DATA),ScanResult('clean','ClamAV 1.5.4/28154'))
        self.assertEqual(len(calls),1)

    def test_url_pinning_partial_configuration_and_busy_input(self):
        for url in ('http://scanner.run.app','https://scanner.run.app.evil.example',
                    'https://scanner.run.app/scan','https://user@scanner.run.app',
                    'https://scanner.run.app:443','https://scanner.run.app?token=x'):
            with self.assertRaises(ValueError): scanner_origin(url)
        with patch.dict(os.environ,{'WZOS_SCANNER_URL':'invalid','WZOS_CLAMSCAN_PATH':'/valid/local'}):
            self.assertIsInstance(configured_scanner(),RemoteScanner)
            self.assertEqual(configured_scanner().scan(DATA).status,'error')
        scanner=self.scanner(lambda request:self.reply(request))
        self.assertEqual(scanner.scan(b'').status,'error')
        self.assertEqual(scanner.scan(b'x'*(10485761)).status,'error')
        scanner.slots.acquire()
        try: self.assertEqual(scanner.scan(DATA).status,'error')
        finally: scanner.slots.release()
