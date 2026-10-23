"""Release checks. Never prints secret values or customer records."""
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

phase, directory = sys.argv[1:]
root = Path(directory)
read = lambda name: json.loads((root / name).read_text())
base = os.getenv('WZOS_RELEASE_BASE', 'us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:238ef05b223064ca0393f6ce99efb7cb392357671b619b4ff18d0e74705f218d')
prior = os.getenv('WZOS_RELEASE_PRIOR', 'wzos-v2-accounts-voice-live-1d2da6b')
tag = 'ui-' + (root/'source-commit.txt').read_text().strip()[:7]
revision = 'wzos-v2-accounts-' + tag
traffic = lambda service: [(t.get('revisionName'), t.get('percent')) for t in service['status']['traffic'] if t.get('percent')]

if phase == 'preflight':
    before = read('before.json')
    assert traffic(before) == [(prior, 100)], 'Unexpected live traffic'
    assert before['spec']['template']['spec']['containers'][0]['image'] == base
    assert before['metadata']['annotations']['run.googleapis.com/ingress'] == 'internal-and-cloud-load-balancing'
    env = {e['name']: e for e in before['spec']['template']['spec']['containers'][0]['env']}
    for flag in ('WZOS_FIELD_VOICE_ENABLED', 'WZOS_FIELD_VOICE_SPEECH_ENABLED'):
        assert env.get(flag, {}).get('value', '0') == '1', 'Preserve the active Voice configuration'
    for flag in ('WZOS_ATLAS_DOT_ENABLED', 'WZOS_ATLAS_DOT_INFERENCE_ENABLED'):
        assert env.get(flag, {}).get('value', '0') != '1', 'DOT activation needs separate source and provider acceptance'
    assert env['WZOS_DATABASE_URL']['valueFrom']['secretKeyRef']['name'] == 'wzos-v2-staging-database-url'
    instances = before['spec']['template']['metadata']['annotations']['run.googleapis.com/cloudsql-instances'].split(',')
    assert len(instances) == 1
    (root / 'sql-instance.txt').write_text(instances[0])
    (root / 'rollback.txt').write_text('gcloud run services update-traffic wzos-v2-accounts --project=enterprise-gemma2 --region=us-central1 --to-revisions=' + prior + '=100 --quiet\n')
elif phase == 'schema':
    schema = read('schema.json')
    assert not schema['conflicts'], 'Incompatible existing columns'
    # Preview-only tables may already be absent; only the disclosed voice table is new.
    allowed = {'preview_orders', 'preview_forms', 'preview_checklists'}
    if os.getenv('WZOS_RELEASE_EMPLOYEE_IMPORT') == '1':
        # Reviewed additive SQL: docs/employee-import-additive.sql.
        allowed |= {'employee_roster', 'employee_import_batches'}
    assert set(schema['missing_tables']) <= allowed, schema['missing_tables']
    assert any(b['status'] == 'SUCCESSFUL' and (datetime.now(timezone.utc) - datetime.fromisoformat(b['startTime'].replace('Z', '+00:00'))).total_seconds() < 86400 for b in read('backups.json')), 'No successful backup within 24 hours'
elif phase == 'build':
    build = read('build.json')
    assert build['status'] == 'SUCCESS'
    images = [i for i in build['results']['images'] if i['name'].endswith(':' + tag)]
    assert len(images) == 1
    (root / 'immutable.txt').write_text(base.split('@')[0] + '@' + images[0]['digest'])
elif phase == 'drift':
    before, now = read('before.json'), read('predeploy.json')
    assert before['spec'] == now['spec'] and traffic(now) == [(prior, 100)], 'Live configuration drift'
elif phase == 'staged':
    before, staged, actual = read('before.json'), read('staged.json'), read('revision.json')
    assert actual['status']['imageDigest'] == (root / 'immutable.txt').read_text()
    assert any(c['type'] == 'Ready' and c['status'] == 'True' for c in actual['status']['conditions'])
    expected = copy.deepcopy(before['spec']['template']['spec'])
    spec = copy.deepcopy(actual['spec'])
    spec['containers'][0]['image'] = expected['containers'][0]['image']
    if 'name' not in expected['containers'][0]:
        spec['containers'][0].pop('name', None)
    assert spec == expected, 'Runtime identity, resources, volumes, flags or secrets changed'
    ignored = {'run.googleapis.com/client-name', 'run.googleapis.com/client-version', 'run.googleapis.com/operation-id', 'serving.knative.dev/creator'}
    annotations = lambda metadata: {k: v for k, v in metadata.get('annotations', {}).items() if k not in ignored}
    assert annotations(actual['metadata']) == annotations(before['spec']['template']['metadata'])
    for key in ('run.googleapis.com/ingress', 'run.googleapis.com/invoker-iam-disabled'):
        assert staged['metadata']['annotations'].get(key) == before['metadata']['annotations'].get(key)
    assert traffic(staged) == [(prior, 100)]
elif phase == 'live':
    static = root / 'source/services/workspace_preview/static'
    for name in ('startup.js', 'app-shell-worker.js', 'workspace-layout.css', 'manifest.webmanifest', 'install-icon-192.png', 'install-icon-512.png', 'install-maskable-192.png', 'install-maskable-512.png', 'mobile-home.js', 'workspace.js', 'workspace.css', 'weather.js', 'weather.css', 'device-setup.js', 'field-voice.js', 'field-voice.css', 'review-workflows.js', 'ask-atlas.js', 'ask-atlas.css', 'dispatch.js', 'navigation.js', 'timeclock.js', 'organization-hub.js', 'install.js', 'account.js', 'forms-hub.js', 'daily-meetings.js'):
        with urllib.request.urlopen('https://app.workzoneos.org/' + name + '?release=ui-20261020', timeout=45) as response:
            assert response.status == 200
            payload=response.read()
            if name == 'app-shell-worker.js':
                assert b'__RELEASE__' not in payload and b'wzos-public-assets-' in payload
            else:
                assert hashlib.sha256(payload).digest() == hashlib.sha256((static / name).read_bytes()).digest(), name + ' mismatch'
    with urllib.request.urlopen('https://app.workzoneos.org/?release=ui-20261020', timeout=45) as response:
        html = response.read().decode()
        assert '/mobile-home.js' in html and '/device-setup.js' in html
        csp = response.headers.get('Content-Security-Policy', '')
        assert "frame-ancestors 'none'" in csp
        for host in ('wzos.daily.co', 'wzos.dailywebrtc.com', 'wzos.dailywebrtc.net'):
            assert 'https://' + host in csp
    for path in ('/api/weather/notices', '/api/account/upgrade', '/api/field-voice/config', '/api/field-voice/drafts', '/api/form-submissions/summary', '/api/atlas/dot/config'):
        try:
            urllib.request.urlopen('https://app.workzoneos.org' + path, timeout=30)
            raise AssertionError('Anonymous access to ' + path)
        except urllib.error.HTTPError as error:
            assert error.code == 401, (path, error.code)
    with urllib.request.urlopen('https://app.workzoneos.org/api/app/version?release=ui-20261020', timeout=30) as response:
        version = json.loads(response.read())
    (root / 'live-version.json').write_text(json.dumps(version))
elif phase == 'traffic':
    assert traffic(read('live.json')) == [(revision, 100)]
else:
    raise ValueError('Unknown phase')
print('UI_RELEASE_' + phase.upper() + '_PASS')
