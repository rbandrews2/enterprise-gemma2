"""Operator-only, idempotent application of the four scoped staging policies.

No channel is created or notification sent. Existing policy channels are preserved.
Run --apply only with authorized gcloud; default prints the reviewed definitions.
"""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PROJECT = 'enterprise-gemma2'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    policies = json.loads((ROOT / 'ops/monitoring/staging-policies.json').read_text())
    if not args.apply:
        print(json.dumps(policies, indent=2)); return
    import requests
    token = subprocess.check_output(['gcloud', 'auth', 'print-access-token'], text=True).strip()
    session = requests.Session()
    session.headers['Authorization'] = 'Bearer ' + token
    base = 'https://monitoring.googleapis.com/v3/projects/' + PROJECT
    def request(method, url, **kwargs):
        response = session.request(method, url, timeout=30, **kwargs)
        if not response.ok:
            raise RuntimeError(f'Monitoring request failed ({response.status_code}): {response.text}')
        return response.json()
    existing = []
    page = ''
    while True:
        response = request('GET', base + '/alertPolicies', params={'pageToken': page})
        existing.extend(response.get('alertPolicies', []))
        page = response.get('nextPageToken')
        if not page: break
    for policy in policies:
        matches = [p for p in existing if p['displayName'] == policy['displayName']]
        if len(matches) > 1: raise RuntimeError('Duplicate policy names; review manually')
        if matches:
            old = matches[0]
            if old.get('userLabels', {}).get('wzos_scope') != 'restricted-staging':
                raise RuntimeError('Refusing to replace a policy not owned by this workflow')
            policy['name'] = old['name']
            policy['notificationChannels'] = old.get('notificationChannels', [])
            result = request('PATCH', 'https://monitoring.googleapis.com/v3/' + old['name'], json=policy)
        else:
            result = request('POST', base + '/alertPolicies', json=policy)
        saved = request('GET', 'https://monitoring.googleapis.com/v3/' + result['name'])
        assert saved['conditions'][0]['conditionThreshold']['filter'] == policy['conditions'][0]['conditionThreshold']['filter']
        print(saved['name'], saved['displayName'], 'enabled=', saved['enabled'], 'channels=', len(saved.get('notificationChannels', [])))


if __name__ == '__main__':
    main()
