"""Read-only public asset/access checks. Does not join a meeting or request media."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid
import httpx


def main():
    root=Path.home()/'wzos-daily-20261014'
    before=json.loads((root/'before-service.json').read_text())
    direct=before['status']['url']
    assert direct.startswith('https://') and direct.endswith('.run.app')
    base='https://app.workzoneos.org'
    assets={'/modules.js':'services/workspace_preview/static/modules.js',
            '/daily-meetings.js':'services/workspace_preview/static/daily-meetings.js',
            '/daily-sdk.js':'services/workspace_preview/static/vendor/daily-iframe.js',
            '/workspace.css':'services/workspace_preview/static/workspace.css'}
    for attempt in range(3):
        try:
            with httpx.Client(timeout=20,follow_redirects=False,trust_env=False) as client:
                response=client.get(base+'/');assert response.status_code==200
                assert '/daily-meetings.js' in response.text and 'WZOS embedded meeting' in response.text
                assert 'frame-src https://wzos.daily.co' in response.headers['content-security-policy']
                assert 'microphone=(self "https://wzos.daily.co")' in response.headers['permissions-policy']
                for url,path in assets.items():
                    expected=subprocess.check_output(['git','show','748f38253dc980fab60e99392bda63341f9a8591:'+path])
                    served=client.get(base+url);assert served.status_code==200
                    assert hashlib.sha256(served.content).digest()==hashlib.sha256(expected).digest()
                meeting=str(uuid.uuid4())
                assert client.get(base+'/api/meetings/config').status_code==401
                for action in ('prepare','join'):
                    assert client.post(base+'/api/meetings/'+meeting+'/'+action).status_code==401
                assert client.get(base+'/api/meetings/config',headers={'Origin':'https://untrusted.example'}).status_code==403
                assert client.get(direct+'/').status_code==404
            print('DAILY_PUBLIC_GATE_PASS: exact assets, frame policy, protected meeting APIs, origin and direct-ingress boundaries')
            return 0
        except Exception:
            if attempt<2:time.sleep(4)
    print('DAILY_PUBLIC_GATE_FAIL: inspect privately; no response or credentials printed')
    return 1


if __name__=='__main__':raise SystemExit(main())
