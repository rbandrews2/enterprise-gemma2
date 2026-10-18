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
