"""One saved synthetic job and one cited model reply in restricted staging.

Uses disposable managed-account fixtures. No customer delivery or field approval.
Save evidence outside Git; disable the fixture organization after the session.
"""
import argparse
import base64
import math
import json
from pathlib import Path
import time
from uuid import uuid4
import requests
try:
    from .validate_managed_accounts import gc, ORIGIN, SERVICE
except ImportError:
    from validate_managed_accounts import gc, ORIGIN, SERVICE


def require_token_lifetime(token, label, minimum=420):
    """Expiry preflight only; Google still verifies signature and authorization."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError()
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=' * (-len(parts[1]) % 4)))
        expiry = payload['exp']
        if isinstance(expiry, bool) or not isinstance(expiry, (int, float)) or not math.isfinite(expiry):
            raise ValueError()
    except (ValueError, KeyError, TypeError, AttributeError):
        raise RuntimeError(f'{label}: invalid token expiry; refresh sign-in before testing') from None
    if expiry - time.time() < minimum:
        raise RuntimeError(f'{label}: insufficient token lifetime; refresh sign-in before testing')


def record_check(evidence, stage, response, expected):
    # Never persist headers, credentials, or provider error bodies.
    evidence.write(json.dumps({'stage':stage, 'status':response.status_code,
                               'passed':response.status_code == expected}) + '\n')
    evidence.flush()
    if response.status_code != expected:
        raise RuntimeError(f'{stage}: HTTP {response.status_code}; expected {expected}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    state = json.loads(args.state.read_text())
    if state.get('disabled') or args.output.exists():
        raise SystemExit('Active synthetic fixtures and a new evidence file required')
    url = gc('run','services','describe',SERVICE,'--region=us-central1','--format=value(status.url)')
    iam = gc('auth','print-identity-token')
    require_token_lifetime(iam, 'Cloud Run operator')
    for role in ('member', 'other'):
        require_token_lifetime(state['users'][role]['idToken'], 'Synthetic '+role)
    with requests.Session() as client, args.output.open('x',encoding='utf-8') as evidence:
        client.trust_env = False
        config = client.get(url+'/api/identities',headers={'X-Serverless-Authorization':'Bearer '+iam},timeout=30)
        record_check(evidence, 'private_app_access', config, 200)
        header = config.json()['auth_header']
        assert header in ('Authorization','X-WZOS-Authorization')
        client.headers.update({'X-Serverless-Authorization':'Bearer '+iam,
            header:'Bearer '+state['users']['member']['idToken'],
            'X-WZOS-Organization':state['orgs']['main'],'Origin':ORIGIN})
        job = client.post(url+'/api/orders',json={'request_id':str(uuid4()),
            'title':'Synthetic Norfolk utility reference review','work_type':'underground_utility',
            'address':'Synthetic Norfolk site - no measured location','locality':'Norfolk',
            'notes':'Synthetic test only. No verified road ownership, geometry or permits.'},timeout=30)
        record_check(evidence, 'saved_job', job, 201)
        job = job.json()
        payload = {'order_id':job['id'],'expected_version':job['version'],'page':'report',
                   'question':'Review the saved utility job using the supplied VDOT and FHWA candidate references. Identify missing evidence and avoid invented placement dimensions.'}
        stale = client.post(url+'/api/assistant/chat',json={**payload,'expected_version':99},timeout=30)
        record_check(evidence, 'stale_version_denial', stale, 409)
        other = client.post(url+'/api/assistant/chat',headers={header:'Bearer '+state['users']['other']['idToken']},json=payload,timeout=30)
        record_check(evidence, 'cross_tenant_denial', other, 403)
        iam = gc('auth','print-identity-token')
        require_token_lifetime(iam, 'Cloud Run operator')
        require_token_lifetime(state['users']['member']['idToken'], 'Synthetic member')
        client.headers['X-Serverless-Authorization'] = 'Bearer '+iam
        before = time.monotonic()
        reply = client.post(url+'/api/assistant/chat',json=payload,timeout=310)
        record_check(evidence, 'cited_model_reply', reply, 200)
        body = reply.json()
        assert body['model_called'] and body['response_kind']=='model'
        assert body['order_version']==job['version'] and body['checklist_basis']['status']=='not_saved'
        assert body['reference_basis']['library_status']=='available'
        assert body['reference_basis']['candidate_count']==len(body['citations'])>0
        assert not body['reference_basis']['applicability_verified']
        assert not body['approved_for_field_use'] and body['actions_performed']==[]
        for citation in body['citations']:
            assert len(citation['revision'])==64 and citation['url'].startswith('https://')
            assert citation.get('page') or citation.get('section')
            assert citation['review_status'] in ('unreviewed','extraction_checked','applicability_reviewed')
        row={'synthetic':True,'job_id':job['id'],'question':payload['question'],
             'response':body,'elapsed_seconds':round(time.monotonic()-before,3),
             'review_status':'needs_human_review'}
        evidence.write(json.dumps(row)+'\n')
        print('PASS saved-job scope, stale/tenant denial, cited private inference;',len(body['citations']),'passages;',row['elapsed_seconds'],'seconds')


if __name__ == '__main__':
    main()
