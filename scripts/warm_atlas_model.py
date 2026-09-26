"""Preload an installed local Atlas model before browser tests; no generated answer."""
import argparse
import os
from pathlib import Path
import sys
import time
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.workspace_preview.intelligence import ALLOWED_MODELS, URL


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=sorted(ALLOWED_MODELS), required=True)
    args = parser.parse_args()
    if any(os.getenv(k) for k in ('K_SERVICE','GAE_ENV','NETLIFY')):
        raise SystemExit('Local evaluation only')
    started = time.monotonic()
    with httpx.Client(trust_env=False, timeout=180) as client:
        response = client.post(URL+'/api/generate', json={
            'model':args.model,'prompt':'','stream':False,'keep_alive':'15m',
            'options':{'num_ctx':8192,'num_thread':2},
        })
        response.raise_for_status()
        if not response.json().get('done'):
            raise SystemExit('Model preload did not complete')
    print(f'Installed model loaded in {time.monotonic()-started:.2f}s; answer quality is not validated.')


if __name__ == '__main__':
    main()
