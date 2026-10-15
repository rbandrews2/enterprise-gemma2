"""Offline build acceptance using only isolated synthetic records. No live credentials."""
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, '/app')


def main():
    expected = {'fastapi': '0.143.1', 'starlette': '1.8.0', 'pip': '26.2.1'}
    versions = {name: importlib.metadata.version(name) for name in expected}
    assert versions == expected, 'Patched runtime package versions do not match'
    assert os.getuid() == 10001, 'Image must run as the existing unprivileged user'
    from package_source_library import verify
    snapshot = verify('/app/.local-data/knowledge')
    assert snapshot['files'], 'Frozen agency library is empty'
    from fastapi.testclient import TestClient
    from services.workspace_preview.app import create_app
    from services.workspace_preview.storage import SQLiteStorage
    from services.workspace_preview.intelligence import LocalIntelligence
    from services.v2.knowledge.store import Store
    os.environ['WZOS_WORKSPACE_PREVIEW'] = '1'
    with tempfile.TemporaryDirectory(prefix='wzos-hub-build-') as directory:
        root = Path(directory)
        app = create_app(storage=SQLiteStorage(root/'db'), knowledge_store=Store(root/'sources', {}), intelligence=LocalIntelligence())
        with TestClient(app) as client:
            admin = {'X-Preview-Actor': 'enterprise-admin'}
            assert client.get('/api/admin/dashboard').status_code == 401
            assert client.get('/api/admin/dashboard', headers={'X-Preview-Actor': 'enterprise-general'}).status_code == 403
            response = client.get('/api/admin/dashboard', headers=admin)
            assert response.status_code == 200 and response.json()['status'] == 'amber'
            assert any(m['id'] == 'assignments' for m in response.json()['modules'])
            assert client.get('/api/integrations/v1/orders').status_code == 401
            assert client.get('/api/admin/dashboard', headers={**admin, 'Origin': 'https://untrusted.example'}).status_code == 403
            assert client.post('/api/admin/dashboard/notes', headers=admin, content=b'x'*16385).status_code == 413
            page = client.get('/')
            assert page.status_code == 200 and '/organization-hub.js' in page.text
            assert page.headers['referrer-policy'] == 'strict-origin-when-cross-origin'
            assert page.headers['x-frame-options'] == 'DENY'
            assert client.get('/organization-hub.js').status_code == 200
    print('HUB_IMAGE_CHECK_PASS', json.dumps({'versions': versions, 'uid': os.getuid(), 'source_files': len(snapshot['files'])}))


if __name__ == '__main__':
    main()
