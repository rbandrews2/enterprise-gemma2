"""Two bounded inference attempts: explicit cancellation and recovery, synthetic only.

Requires active disposable managed-account fixtures. Does not provision or clean up
resources; the operator must use the existing bounded trial/cleanup procedure.
Never interprets application cancellation as proof that GPU generation stopped.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import time
from uuid import uuid4

import httpx
from validate_managed_accounts import gc, ORIGIN, SERVICE
from validate_atlas_grounding_staging import require_token_lifetime


async def run(state, output):
    if state.get('disabled'):
        raise ValueError('Active disposable fixtures required')
    iam = gc('auth', 'print-identity-token')
    require_token_lifetime(iam, 'Operator', minimum=1000)
    for role in ('member', 'admin', 'other'):
        require_token_lifetime(state['users'][role]['idToken'], role, minimum=1000)
    url = gc('run', 'services', 'describe', SERVICE, '--region=us-central1', '--format=value(status.url)')
    with output.open('x', encoding='utf-8') as evidence:
        def record(stage, **values):
            row = {'stage': stage, **values}
            evidence.write(json.dumps(row)+'\n'); evidence.flush(); print(json.dumps(row), flush=True)
        async with httpx.AsyncClient(base_url=url, trust_env=False, follow_redirects=False, timeout=310) as client:
            client.headers.update({'X-Serverless-Authorization': 'Bearer '+iam})
            config = await client.get('/api/identities'); config.raise_for_status()
            header = config.json()['auth_header']
            assert header in ('Authorization', 'X-WZOS-Authorization')
            client.headers.update({header: 'Bearer '+state['users']['member']['idToken'],
                                   'X-WZOS-Organization': state['orgs']['main'], 'Origin': ORIGIN})
            # Denial checks and race handling consume no model requests.
            early = str(uuid4()); path = '/api/assistant/requests/'+early
            r = await client.post(path+'/cancel'); r.raise_for_status()
            for role in ('admin', 'other'):
                denied = await client.post(path+'/cancel', headers={header: 'Bearer '+state['users'][role]['idToken']})
                assert denied.status_code in (403, 404)
                record('cancel_denied_'+role, http_status=denied.status_code)
            pre = await client.post('/api/assistant/chat', json={'question':'Describe uncertainty in a synthetic test.', 'request_id':early})
            assert pre.status_code == 499 and pre.json()['code'] == 'cancelled'
            record('cancel_before_start', http_status=pre.status_code)
            before = await client.get('/api/orders'); before.raise_for_status()
            digest = lambda data: hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
            original = digest(before.json())
            rid = str(uuid4()); path = '/api/assistant/requests/'+rid
            payload = {'question':'Explain uncertainty in a synthetic job with missing site dimensions. Do not invent facts.',
                       'request_id':rid, 'page':'work_orders'}
            pending = asyncio.create_task(client.post('/api/assistant/chat', json=payload))
            try:
                deadline = time.monotonic()+15
                while time.monotonic() < deadline:
                    status = await client.get(path)
                    if status.status_code == 200 and status.json()['state'] == 'running':
                        break
                    if pending.done():
                        raise RuntimeError('Reply completed before cancellation; observation inconclusive')
                    await asyncio.sleep(0.1)
                else:
                    raise RuntimeError('Running request was not observed')
                await asyncio.sleep(0.5)
                start = time.monotonic()
                cancel = await client.post(path+'/cancel'); cancel.raise_for_status()
                assert cancel.json()['state'] in ('cancel_requested', 'cancelled')
                reply = await asyncio.wait_for(asyncio.shield(pending), 10)
                assert reply.status_code == 499 and reply.json()['code'] == 'cancelled'
                status = await client.get(path); status.raise_for_status()
                assert status.json()['state'] == 'cancelled'
                record('explicit_cancel', request_id=rid, http_status=499,
                       seconds=round(time.monotonic()-start,3), provider_stop_verified=False)
                start = time.monotonic()
                recovery = await client.post('/api/assistant/chat', json={**payload,'request_id':str(uuid4())})
                result = recovery.json()
                record('immediate_recovery', http_status=recovery.status_code,
                       seconds=round(time.monotonic()-start,3), model_called=result.get('model_called',False),
                       error_code=result.get('code') if result.get('code') in ('busy','timeout','provider_error') else None)
                assert recovery.status_code == 200 and result['model_called'] and result['actions_performed'] == []
                after = await client.get('/api/orders'); after.raise_for_status()
                assert digest(after.json()) == original
                record('complete', saved_orders_unchanged=True, provider_stop_verified=False, cloud_cross_instance_verified=False)
            finally:
                if not pending.done():
                    # Explicit stop even if the runner fails; never just abandon the client.
                    try:
                        await client.post(path+'/cancel', timeout=10)
                    finally:
                        pending.cancel()
                await asyncio.gather(pending, return_exceptions=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run(json.loads(args.state.read_text()), args.output))
