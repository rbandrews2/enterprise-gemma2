"""Read-only Atlas acceptance using existing synthetic managed-account fixtures.

Run in authorized Cloud Shell after validate_managed_accounts.py prepare. Never
prints fixture tokens, calls a model, changes attendance or sends messages.
"""
import argparse
import json
from pathlib import Path
import requests
from validate_managed_accounts import gc, ORIGIN, SERVICE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', required=True, type=Path)
    args = parser.parse_args()
    state = json.loads(args.state.read_text())
    if state.get('disabled'):
        raise SystemExit('Fixtures are disabled; prepare a fresh synthetic test set')
    url = gc('run', 'services', 'describe', SERVICE, '--region=us-central1', '--format=value(status.url)')
    iam = gc('auth', 'print-identity-token')
    with requests.Session() as client:
        client.trust_env = False
        config = client.get(url+'/api/identities', headers={'X-Serverless-Authorization':'Bearer '+iam}, timeout=40)
        config.raise_for_status()
        auth_header = config.json()['auth_header']
        assert auth_header in ('Authorization', 'X-WZOS-Authorization')

        def call(path, role='member', payload=None, expected=200):
            headers = {'X-Serverless-Authorization':'Bearer '+iam,
                       auth_header:'Bearer '+state['users'][role]['idToken'],
                       'X-WZOS-Organization':state['orgs']['main'], 'Origin':ORIGIN}
            response = client.request('POST' if payload else 'GET', url+path,
                                      headers=headers, json=payload, timeout=40)
            assert response.status_code == expected, f'{path}: expected {expected}, got {response.status_code}'
            return response.json()

        for role in ('admin', 'member'):
            assert call('/api/session', role)['role'] == role
        call('/api/assistant/status', 'other', expected=403)
        call('/api/assistant/status', 'unverified', expected=403)
        status = call('/api/assistant/status')
        assert status['workspace_guides_ready'] and status['actions_enabled'] is False
        assert status['ready'] is False, 'This validation expects inference disabled'
        scenarios = [
            ('work_orders', 'How do I save a work order?', 'work_orders'),
            ('time_clock', 'Am I clocked in?', 'clock_status'),
            ('forms', 'How do I record a vehicle defect?', 'forms'),
            ('schedule', 'Can I assign employees to the schedule?', 'schedule'),
            ('training', 'Does completion issue a certificate?', 'training'),
            ('messages', 'Can I send SMS messages?', 'messages'),
            ('navigation', 'How do I open directions for a saved job?', 'navigation'),
            ('report', 'Can Atlas give flagger positions?', 'placement_capability'),
        ]
        for page, question, topic in scenarios:
            body = call('/api/assistant/chat', payload={'page':page, 'question':question})
            assert body['response_kind'] == 'workspace_guide' and body['model_called'] is False
            assert body['guidance_topic'] == topic and body['actions_performed'] == []
            assert body['approved_for_field_use'] is False
            if page != 'time_clock':
                assert body['time_basis'] is None
            if page == 'schedule':
                assert 'Ask an admin' in body['answer']
            print('PASS verified guidance:', page)
        print('PASS: deployed admin/member roles, tenant/email boundaries, eight Atlas guides; inference remains disabled')


if __name__ == '__main__':
    main()
