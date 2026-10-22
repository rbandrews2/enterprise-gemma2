"""Pin two existing aliases on the unchanged WZOS image, with drift/rollback checks.

No secret payload access, image build, new role, schema or application source.
Requires explicit --apply. Private evidence directory must already exist.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

PROJECT = 'enterprise-gemma2'
SERVICE = 'wzos-v2-accounts'
REGION = 'us-central1'
PINS = {'WZOS_DATABASE_URL': 'wzos-v2-staging-database-url',
        'WZOS_AUTH_WEB_API_KEY': 'wzos-v2-staging-auth-web-key'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    root = args.evidence
    assert root.is_dir()
    assert not (root/'pins-plan.json').exists(), 'Use a fresh evidence directory.'
    def call(name, command):
        result = subprocess.run(['gcloud', *command, '--project='+PROJECT, '--quiet', '--format=json'],
                                capture_output=True, text=True, timeout=300)
        (root/(name+'.stderr')).write_text(result.stderr)
        (root/(name+'.exit')).write_text(str(result.returncode))
        if result.returncode:
            raise RuntimeError(name+' failed; inspect private evidence')
        data = json.loads(result.stdout) if result.stdout.strip() else {}
        (root/(name+'.json')).write_text(json.dumps(data, indent=2))
        return data
    def describe(name):
        return call(name, ['run', 'services', 'describe', SERVICE, '--region='+REGION])
    def active(service):
        rows = [x for x in service['status']['traffic'] if x.get('percent', 0)]
        assert len(rows) == 1 and rows[0]['percent'] == 100, 'Unexpected traffic split'
        return rows[0]['revisionName']
    def smoke():
        out = {}
        for path in ('/api/app/version', '/api/identities'):
            request = urllib.request.Request('https://app.workzoneos.org'+path,
                                             headers={'Cache-Control':'no-cache'})
            with urllib.request.urlopen(request, timeout=25) as response:
                assert response.status == 200
                data = json.loads(response.read(1024*1024))
                out[path] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        try:
            urllib.request.urlopen('https://app.workzoneos.org/api/session', timeout=25)
            raise AssertionError('Anonymous workspace access allowed')
        except urllib.error.HTTPError as error:
            assert error.code == 401
            out['anonymous_session_status'] = 401
        return out
    before = describe('pins-before')
    baseline = active(before)
    assert before['status']['latestReadyRevisionName'] == baseline, 'Existing staged revision needs review'
    revision = call('baseline-revision', ['run', 'revisions', 'describe', baseline, '--region='+REGION])
    image = revision['status']['imageDigest']
    assert '@sha256:' in image
    assert len(before['spec']['template']['spec']['containers']) == 1
    env = {e['name']:e for e in before['spec']['template']['spec']['containers'][0]['env']}
    for key, secret in PINS.items():
        assert env[key]['valueFrom']['secretKeyRef'] == {'name':secret, 'key':'latest'}
        versions = call(secret+'-versions', ['secrets', 'versions', 'list', secret])
        assert len(versions) == 1 and versions[0]['name'].endswith('/versions/1')
        assert versions[0]['state'] == 'ENABLED'
    public_before = smoke()
    suffix = 'pins-'+time.strftime('%m%d%H%M%S', time.gmtime())
    candidate = SERVICE+'-'+suffix
    plan = {'baseline':baseline, 'candidate':candidate, 'image':image,
            'pins':{k:{'secret':v,'version':'1'} for k,v in PINS.items()},
            'public_before_hashes':public_before}
    (root/'pins-plan.json').write_text(json.dumps(plan, indent=2))
    print('PIN_PLAN_READY '+json.dumps({'baseline':baseline,'candidate':candidate}), flush=True)
    if not args.apply:
        return
    assert describe('pins-drift')['spec'] == before['spec'], 'Service changed after preflight'
    call('pins-stage', ['run', 'deploy', SERVICE, '--region='+REGION, '--image='+image,
         '--update-secrets='+','.join(k+'='+v+':1' for k,v in PINS.items()),
         '--revision-suffix='+suffix, '--no-traffic'])
    staged = describe('pins-staged')
    assert active(staged) == baseline, 'Staging unexpectedly changed traffic'
    ready = call('candidate-revision', ['run','revisions','describe',candidate,'--region='+REGION])
    assert any(x['type']=='Ready' and x['status']=='True' for x in ready['status']['conditions'])
    assert ready['status']['imageDigest'] == image, 'Image changed'
    expected = copy.deepcopy(before['spec']['template']['spec'])
    expected['containers'][0]['image'] = staged['spec']['template']['spec']['containers'][0]['image']
    for item in expected['containers'][0]['env']:
        if item['name'] in PINS:
            item['valueFrom']['secretKeyRef']['key'] = '1'
    # gcloud may reorder env vars; compare canonical names, preserving every value.
    def canonical(spec):
        value = copy.deepcopy(spec)
        for container in value['containers']:
            container['env'] = sorted(container.get('env', []), key=lambda x:x['name'])
        return value
    assert canonical(staged['spec']['template']['spec']) == canonical(expected), 'Unexpected runtime spec change'
    def annotations(service):
        ignore = {'run.googleapis.com/client-name','run.googleapis.com/client-version',
                  'run.googleapis.com/operation-id','run.googleapis.com/user-image'}
        return {k:v for k,v in service['spec']['template'].get('metadata',{}).get('annotations',{}).items() if k not in ignore}
    assert annotations(staged) == annotations(before), 'Runtime policy/scaling changed'
    policy_keys = ('run.googleapis.com/ingress','run.googleapis.com/invoker-iam-disabled',
                   'run.googleapis.com/custom-audiences','run.googleapis.com/minScale',
                   'run.googleapis.com/maxScale')
    for key in policy_keys:
        assert staged['metadata'].get('annotations', {}).get(key) == before['metadata'].get('annotations', {}).get(key), key
    cutover_attempted = False
    try:
        cutover_attempted = True
        call('pins-cutover', ['run','services','update-traffic',SERVICE,'--region='+REGION,
                            '--to-revisions='+candidate+'=100'])
        after = describe('pins-after')
        assert active(after) == candidate
        assert smoke() == public_before, 'Public version/auth configuration changed'
    except Exception:
        if cutover_attempted:
            call('pins-rollback', ['run','services','update-traffic',SERVICE,'--region='+REGION,
                                 '--to-revisions='+baseline+'=100'])
            assert active(describe('pins-rollback-verified')) == baseline
        raise
    (root/'pins-result.json').write_text(json.dumps({'passed':True, **plan}, indent=2))
    print('RUNTIME_SECRET_PINS_PASS baseline='+baseline+' live='+candidate, flush=True)


if __name__ == '__main__':
    main()
