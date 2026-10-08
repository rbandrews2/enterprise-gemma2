"""Isolated synthetic WZOS integration preview with persistent local file uploads.

No cloud authentication, model calls, external messages or production database.
Run from the candidate checkout: python scripts/start_integration_preview.py
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, choices=range(1024, 65536), default=8083,
                        metavar='PORT')
    args = parser.parse_args()
    if any(os.getenv(k) for k in ('K_SERVICE', 'GAE_ENV', 'NETLIFY')):
        raise SystemExit('Synthetic integration preview is loopback-only')
    os.environ.update(WZOS_WORKSPACE_PREVIEW='1', WZOS_ATLAS_PROVIDER='local',
                      WZOS_ATLAS_LOCAL_MODEL='0', WZOS_ATLAS_CLOUD_ENABLED='0',
                      WZOS_ATLAS_VLLM_ENABLED='0', WZOS_GOOGLE_MAPS_BROWSER_KEY='')
    from services.workspace_preview.app import create_app
    from services.workspace_preview.files import LocalFiles
    from services.workspace_preview.intelligence import LocalIntelligence
    from services.v2.knowledge.store import Store
    import uvicorn
    data = ROOT / '.local-data/integration-preview'
    data.mkdir(parents=True, exist_ok=True)
    app = create_app(data / 'workspace.sqlite', Store(data / 'sources', {}),
                     intelligence=LocalIntelligence(), file_store=LocalFiles(data / 'files'))
    print('Synthetic integration preview: local files persist; live Atlas and cloud services are disabled.')
    uvicorn.run(app, host='127.0.0.1', port=args.port, proxy_headers=False)


if __name__ == '__main__':
    main()
