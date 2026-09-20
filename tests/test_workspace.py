import asyncio
import unittest
import httpx
from fastapi.testclient import TestClient
from services.v2.app import create_app


class WorkspaceTests(unittest.TestCase):
    def test_local_assets(self):
        with TestClient(create_app()) as client:
            page = client.get('/v2/workspace')
            self.assertEqual(page.status_code, 200)
            self.assertIn('no-store', page.headers['cache-control'])
            self.assertIn('coordinate preview has no road or satellite imagery', page.text)
            script = client.get('/v2/workspace.js')
            self.assertEqual(script.status_code, 200)
            self.assertIn('text/javascript', script.headers['content-type'])

    def test_remote_assets_rejected(self):
        async def check():
            transport = httpx.ASGITransport(app=create_app(), client=('203.0.113.1', 123))
            async with httpx.AsyncClient(transport=transport, base_url='http://localhost') as client:
                for path in ('/v2/workspace', '/v2/workspace.js'):
                    self.assertEqual((await client.get(path)).status_code, 403)
        asyncio.run(check())
