"""Public checks for the training/footer overlay; no customer data or sends."""
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

root = Path(sys.argv[1])
commit = (root / 'source-commit.txt').read_text().strip()
origin = 'https://app.workzoneos.org'
static = root / 'source/services/workspace_preview/static'
for name in ('team-modules.js', 'training-content.js', 'workspace-layout.css',
             'account.js', 'workspace.js', 'workspace.css'):
    with urllib.request.urlopen(origin + '/' + name + '?release=' + commit[:12], timeout=45) as response:
        assert response.status == 200
        assert hashlib.sha256(response.read()).digest() == hashlib.sha256((static / name).read_bytes()).digest(), name
with urllib.request.urlopen(origin + '/?release=' + commit[:12], timeout=45) as response:
    html = response.read().decode()
    assert "frame-ancestors 'none'" in response.headers.get('Content-Security-Policy', '')
    for text in ('global-footer', '© 2026 WZOS. All rights reserved.',
                 'Property of Molecular Project Development LLC.', 'tel:+18446857207'):
        assert text in html, text
    marker = re.search(r'<meta name="wzos-release" content="([a-f0-9]{24})">', html)
    assert marker, 'Missing update marker'
for path in ('/api/training-course-videos', '/api/training', '/api/field-voice/config'):
    try:
        urllib.request.urlopen(origin + path, timeout=30)
        raise AssertionError('Anonymous access: ' + path)
    except urllib.error.HTTPError as error:
        assert error.code == 401, (path, error.code)
request = urllib.request.Request(origin + '/api/training-course-videos/pmt',
    data=b'{"expected_version":0,"media":null}', method='PUT', headers={'Content-Type':'application/json'})
try:
    urllib.request.urlopen(request, timeout=30)
    raise AssertionError('Anonymous catalog link update allowed')
except urllib.error.HTTPError as error:
    assert error.code == 401, error.code
with urllib.request.urlopen(origin + '/api/app/version?release=' + commit[:12], timeout=30) as response:
    version = json.load(response)
assert version['version'] == marker[1], 'Update API and shell disagree'
(root / 'live-version.json').write_text(json.dumps(version))
print('TRAINING_FOOTER_PUBLIC_PASS')
