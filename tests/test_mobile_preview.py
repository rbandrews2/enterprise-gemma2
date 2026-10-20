import asyncio
import os
import unittest
from unittest.mock import patch
import httpx
from scripts.run_mobile_preview import MobilePreview, build_application

async def fixture(scope, receive, send):
    await send({'type': 'http.response.start', 'status': 200, 'headers': [
        (b'content-security-policy', b"default-src 'self'; frame-ancestors 'none'; base-uri 'none'"),
        (b'x-frame-options', b'DENY')]})
    await send({'type': 'http.response.body', 'body': b'Synthetic app'})

class SimulatorTests(unittest.TestCase):
    def fetch(self, path='/', host='127.0.0.1:8083', peer='127.0.0.1'):
        async def call():
            transport = httpx.ASGITransport(app=MobilePreview(fixture), client=(peer, 8000))
            async with httpx.AsyncClient(transport=transport, base_url='http://'+host) as client:
                return await client.get(path)
        return asyncio.run(call())

    def test_only_local_app_root_allows_same_origin_frame(self):
        result = self.fetch()
        self.assertEqual(result.headers['x-frame-options'], 'SAMEORIGIN')
        self.assertIn("frame-ancestors 'self'", result.headers['content-security-policy'])
        self.assertIn("base-uri 'none'", result.headers['content-security-policy'])
        self.assertEqual(self.fetch('/another').headers['x-frame-options'], 'DENY')

    def test_external_hosts_and_clients_are_denied(self):
        self.assertEqual(self.fetch(host='attacker.example').status_code, 403)
        self.assertEqual(self.fetch(peer='192.0.2.1').status_code, 403)

    def test_simulator_assets_are_served_without_cache_or_arbitrary_files(self):
        result = self.fetch('/__simulator')
        self.assertEqual(result.status_code, 200)
        self.assertIn('WZOS mobile workspace', result.text)
        self.assertIn('src="/"', result.text)
        self.assertEqual(result.headers['cache-control'], 'no-store')
        self.assertEqual(result.headers['x-frame-options'], 'DENY')
        self.assertIn('text/css', self.fetch('/__simulator/preview.css').headers['content-type'])
        self.assertIn('application/javascript', self.fetch('/__simulator/preview.js').headers['content-type'])

    def test_cloud_runtime_is_refused_before_application_creation(self):
        with patch.dict(os.environ, {'K_SERVICE': 'production'}):
            with self.assertRaises(RuntimeError):
                build_application()

    def dispatch(self, path='/api/dispatch/my-assignments', actor='enterprise-admin', origin=None):
        async def call():
            transport=httpx.ASGITransport(app=MobilePreview(fixture), client=('127.0.0.1',8000))
            headers={'X-Preview-Actor':actor}
            if origin: headers['Origin']=origin
            async with httpx.AsyncClient(transport=transport,base_url='http://127.0.0.1:8083') as client:
                return await client.get(path,headers=headers)
        return asyncio.run(call())

    def test_preview_assignments_are_read_only_synthetic_and_identity_scoped(self):
        admin=self.dispatch();member=self.dispatch(actor='enterprise-general')
        self.assertEqual(admin.status_code,200)
        self.assertEqual(admin.headers['cache-control'],'no-store')
        self.assertEqual(admin.headers['x-wzos-synthetic-preview'],'1')
        self.assertEqual(admin.json()['total'],1)
        self.assertNotEqual(admin.json()['items'][0]['id'],member.json()['items'][0]['id'])
        self.assertEqual(admin.json()['items'][0]['status'],'accepted')
        self.assertIn('Synthetic preview',admin.json()['items'][0]['notes'])
        self.assertEqual(self.dispatch('/api/dispatch/notifications').json(),{'pending_count':0})

    def test_preview_assignment_filters_and_boundaries(self):
        self.assertEqual(self.dispatch(actor='core-admin').status_code,403)
        self.assertEqual(self.dispatch(actor='unknown').status_code,401)
        self.assertEqual(self.dispatch(origin='https://example.com').status_code,403)
        self.assertEqual(self.dispatch('/api/dispatch/my-assignments?phase=finished').json()['total'],0)
        self.assertEqual(self.dispatch('/api/dispatch/my-assignments?offset=25').json()['items'],[])
        self.assertEqual(self.dispatch('/api/dispatch/my-assignments?phase=invalid').status_code,422)
        self.assertEqual(self.dispatch('/api/dispatch/my-assignments?offset=-1').status_code,422)

    def test_field_voice_preview_is_enterprise_only_without_processing(self):
        config=self.dispatch('/api/field-voice/config').json()
        self.assertTrue(config['enabled'])
        self.assertTrue(config['preview_only'])
        self.assertFalse(config['speech_enabled'])
        for path in ('/api/field-voice/config','/api/field-voice/jobs','/api/field-voice/drafts'):
            self.assertEqual(self.dispatch(path,actor='core-general').status_code,403)
            self.assertEqual(self.dispatch(path,actor='unknown').status_code,401)
            self.assertEqual(self.dispatch(path).headers['cache-control'],'no-store')
        self.assertEqual(self.dispatch('/api/field-voice/jobs').json()['items'][0]['id'],'enterprise-sample')
        self.assertEqual(self.dispatch('/api/field-voice/drafts').json()['items'],[])
