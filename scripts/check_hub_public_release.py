"""Read-only hub release check; no users, credentials, messages or media created."""
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.request

SOURCE = '5a3ac868085685a5e71169ceac21fa618cc405e9'


def fetch(url, origin=None):
    headers = {'Cache-Control': 'no-cache'}
    if origin:
        headers['Origin'] = origin
    req = urllib.request.Request(url, headers=headers)
    try:
        response = urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        return response.status, response.headers, response.read(4 * 1024 * 1024)


def main():
    evidence = Path.home() / 'wzos-hub-rollout-20261014'
    before = json.loads((evidence / 'before-service.json').read_text())
    base = 'https://app.workzoneos.org'
    code, headers, body = fetch(base + '/')
    assert code == 200 and b'/organization-hub.js' in body
    assert 'frame-src https://wzos.daily.co' in headers['Content-Security-Policy']
    assert 'microphone=(self "https://wzos.daily.co")' in headers['Permissions-Policy']
    assert headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'
    assert headers['X-Frame-Options'] == 'DENY'
    assert headers['Cross-Origin-Resource-Policy'] == 'same-origin'
    for filename in ('organization-hub.js', 'workspace.js', 'workspace.css',
                     'daily-meetings.js', 'modules.js'):
        expected = subprocess.check_output([
            'git', 'show', SOURCE + ':services/workspace_preview/static/' + filename])
        status, _, content = fetch(base + '/' + filename)
        assert status == 200 and hashlib.sha256(content).digest() == hashlib.sha256(expected).digest(), filename
    for path in ('/api/admin/dashboard', '/api/admin/integrations',
                 '/api/integrations/v1/orders', '/api/integrations/v1/schedule',
                 '/api/meetings/config', '/api/account'):
        assert fetch(base + path)[0] == 401, path
    assert fetch(base + '/api/admin/dashboard', 'https://untrusted.example')[0] == 403
    direct = before['status']['url']
    assert direct.startswith('https://') and direct.endswith('.run.app')
    assert fetch(direct + '/')[0] == 404
    print('HUB_PUBLIC_GATE_PASS: exact assets, protected APIs, origin, headers, Daily policy, direct ingress')


if __name__ == '__main__':
    main()
