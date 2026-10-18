"""Extract immutable image identities only from a successful reviewed Cloud Build."""
import json
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
build = json.loads((root / 'build.json').read_text())
assert build['status'] == 'SUCCESS', build['status']
prefix = 'us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/'
tag = (root / 'source-commit.txt').read_text().strip()[:7]
expected = {
    prefix + 'wzos-v2-accounts:field-voice-' + tag: 'app-image.txt',
    prefix + 'wzos-v2-field-voice-pilot:' + tag: 'job-image.txt',
}
images = build['results']['images']
assert len(images) == 2
for image in images:
    assert image['name'] in expected
    digest = image['digest']
    assert re.fullmatch(r'sha256:[a-f0-9]{64}', digest)
    value = image['name'].rsplit(':', 1)[0] + '@' + digest
    (root / expected.pop(image['name'])).write_text(value + '\n')
    print(value)
assert not expected
print('FIELD_VOICE_BUILD_IMAGES_VERIFIED')
