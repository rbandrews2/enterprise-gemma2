"""Verify saved candidate metadata without exposing private configuration."""
import copy
import json
from pathlib import Path

IMAGE = 'us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:fc87869680a0c6948d4116225ddf7ae22de6a659d0264e31351a251367465f06'
REVISION = 'wzos-v2-accounts-hub-5a3ac86'


def main():
    p = Path.home() / 'wzos-hub-rollout-20261014'
    before = json.loads((p / 'at-deploy-service.json').read_text())
    after = json.loads((p / 'candidate-service.json').read_text())
    revision = json.loads((p / 'candidate-revision.json').read_text())
    bs = copy.deepcopy(before['spec']['template']['spec'])
    ns = copy.deepcopy(after['spec']['template']['spec'])
    assert ns['containers'][0]['image'] == IMAGE
    ns['containers'][0]['image'] = bs['containers'][0]['image']
    assert ns == bs, 'Unexpected runtime configuration change'
    ignored = {'run.googleapis.com/client-name', 'run.googleapis.com/client-version', 'run.googleapis.com/operation-id'}
    def annotations(s):
        return {k: v for k, v in s['spec']['template']['metadata'].get('annotations', {}).items() if k not in ignored}
    assert annotations(before) == annotations(after), 'Template annotation drift'
    for key in ('run.googleapis.com/ingress', 'run.googleapis.com/invoker-iam-disabled'):
        assert before['metadata'].get('annotations', {}).get(key) == after['metadata'].get('annotations', {}).get(key), key
    assert after['status']['latestCreatedRevisionName'] == REVISION
    assert after['status']['latestReadyRevisionName'] == REVISION
    assert revision['metadata']['name'] == REVISION and revision['status']['imageDigest'] == IMAGE
    conditions = {c['type']: c for c in revision['status']['conditions']}
    assert conditions['Ready']['status'] == 'True' and conditions['Ready'].get('reason') != 'Retired'
    assert [(t.get('revisionName'), t.get('percent')) for t in after['status']['traffic'] if t.get('percent')] == [('wzos-v2-accounts-daily-748f382', 100)]
    old_tags = {t['tag']: t['revisionName'] for t in before['status']['traffic'] if t.get('tag')}
    new_tags = {t['tag']: t['revisionName'] for t in after['status']['traffic'] if t.get('tag')}
    assert all(new_tags.get(k) == v for k, v in old_tags.items())
    assert new_tags['hub-5a3ac86'] == REVISION
    print('HUB_CANDIDATE_READY_CONFIGURATION_PRESERVED_NO_TRAFFIC')


if __name__ == '__main__':
    main()
