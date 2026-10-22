"""Public verification limited to the affected form/weather assets, release marker and auth shell."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

root = Path(sys.argv[1])
commit = (root / 'source-commit.txt').read_text().strip()
origin = 'https://app.workzoneos.org'
for name in ('forms-hub.js', 'forms-hub.css', 'review-workflows.js', 'field-voice.js', 'weather.js', 'weather.css'):
    with urllib.request.urlopen(origin + '/' + name + '?design=' + commit[:12], timeout=45) as response:
        assert response.status == 200
        expected = root / 'source/services/workspace_preview/static' / name
        assert hashlib.sha256(response.read()).digest() == hashlib.sha256(expected.read_bytes()).digest(), name
with urllib.request.urlopen(origin + '/?design=' + commit[:12], timeout=45) as response:
    assert response.status == 200
    assert "frame-ancestors 'none'" in response.headers.get('Content-Security-Policy', '')
with urllib.request.urlopen(origin + '/api/app/version?design=' + commit[:12], timeout=30) as response:
    version = json.load(response)
(root / 'live-version.json').write_text(json.dumps(version))
print('FORMS_WEATHER_PUBLIC_ASSETS_PASS')
