"""Loopback-only account/file browser validation with Google's Auth emulator.

Run the emulator separately using demo-wzos-validation, 127.0.0.1:9099.
No real accounts, cloud credentials, cloud storage or external messages.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if __name__ == '__main__':
    if any(os.getenv(k) for k in ('K_SERVICE', 'GAE_ENV', 'NETLIFY')):
        raise SystemExit('Account validation is local only')
    os.environ.update(WZOS_ACCOUNT_WORKSPACE='1', WZOS_AUTH_EMULATOR='1',
                      FIREBASE_AUTH_EMULATOR_HOST='127.0.0.1:9099',
                      WZOS_AUTH_PROJECT='demo-wzos-validation', WZOS_AUTH_WEB_API_KEY='fake-api-key')
    from services.workspace_preview.app import create_app
    from services.workspace_preview.storage import SQLiteStorage
    from services.workspace_preview.files import LocalFiles
    from services.v2.knowledge.store import Store
    import uvicorn
    root = ROOT / '.local-data/browser-validation'
    root.mkdir(parents=True, exist_ok=True)
    app = create_app(account_workspace=True, storage=SQLiteStorage(root/'accounts.sqlite'),
                     file_store=LocalFiles(root/'files'), knowledge_store=Store(root/'sources', {}))
    activation_path = root/'activation.txt'
    if not activation_path.exists():
        with activation_path.open('x', encoding='utf-8') as output:
            output.write(app.state.accounts.issue_activation('enterprise'))
    print('Synthetic account validation: http://127.0.0.1:8083; activation in ignored browser-validation directory')
    uvicorn.run(app, host='127.0.0.1', port=8083, proxy_headers=False)
