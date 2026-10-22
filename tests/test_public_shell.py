"""Public launch caching must never include authenticated workspace data."""
import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.v2.knowledge.store import Store

class PublicShellTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory=Path(temporary.name)
        environment=patch.dict(os.environ, {'WZOS_WORKSPACE_PREVIEW':'1','K_SERVICE':'','GAE_ENV':'','NETLIFY':''})
        environment.start()
        self.addCleanup(environment.stop)
        self.client=TestClient(create_app(directory/'preview.sqlite', Store(directory/'sources', {})))
        self.addCleanup(self.client.close)

    def headers(self):
        return {'X-Preview-Actor':'enterprise-admin'}

    def test_embedded_plugins_blocked_with_and_without_maps(self):
        for key in ('', 'synthetic-public-browser-key'):
            with patch.dict(os.environ, {'WZOS_GOOGLE_MAPS_BROWSER_KEY':key}):
                for path in ('/', '/api/app/version'):
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn("object-src 'none'", response.headers['content-security-policy'])
                    self.assertIn("frame-ancestors 'none'", response.headers['content-security-policy'])
    def test_public_shell_and_versioned_assets(self):
        page = self.client.get('/')
        version = self.client.get('/api/app/version').json()['version']
        self.assertEqual(page.headers['cache-control'], 'no-store')
        self.assertEqual(page.headers['x-wzos-public-shell'], '1')
        self.assertIn('class="app-starting"', page.text)
        self.assertIn('/startup.js?v='+version, page.text)
        self.assertIn('/workspace-layout.css?v='+version, page.text)
        self.assertNotIn('admin@workzoneos.org', page.text)
        for path in ('/startup.js', '/workspace-layout.css', '/wzos-logo.png'):
            asset = self.client.get(path+'?v='+version)
            self.assertEqual(asset.status_code, 200)
            self.assertEqual(asset.headers['x-wzos-public-asset'], '1')
            self.assertIn('immutable', asset.headers['cache-control'])
            self.assertEqual(self.client.get(path).headers['cache-control'], 'no-store')
            self.assertEqual(self.client.get(path+'?v=stale').headers['cache-control'], 'no-store')

    def test_private_routes_and_worker_are_never_public_assets(self):
        version = self.client.get('/api/app/version').json()['version']
        for path in ('/api/session','/api/orders','/api/app/version','/app-shell-worker.js'):
            response=self.client.get(path+'?v='+version, headers=self.headers())
            self.assertEqual(response.headers['cache-control'], 'no-store')
            self.assertNotIn('x-wzos-public-asset', response.headers)
        worker=self.client.get('/app-shell-worker.js').text
        self.assertNotIn('__RELEASE__', worker)
        self.assertIn(version, worker)


    def test_shortcut_manifest_and_apple_icons_use_supplied_brand(self):
        manifest = self.client.get('/manifest.webmanifest').json()
        self.assertEqual(manifest['id'], '/')
        self.assertEqual(manifest['display'], 'standalone')
        self.assertEqual(manifest['start_url'], '/')
        self.assertEqual({icon['purpose'] for icon in manifest['icons']}, {'any', 'maskable'})
        for icon in manifest['icons']:
            self.assertIn('brand=20261020', icon['src'])
            response=self.client.get(icon['src'])
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content[:8], b'\x89PNG\r\n\x1a\n')
        self.assertIn('/install-icon-180.png?brand=20261020', self.client.get('/').text)
