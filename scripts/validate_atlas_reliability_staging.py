"""Bounded real-app concurrency and client-disconnect observations (synthetic only).
Run after cited saved-job acceptance with the same active disposable fixtures.
Client cancellation is an observation, not proof that GPU generation stopped.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import httpx
from uuid import uuid4
try:
    from .validate_managed_accounts import gc, ORIGIN, SERVICE
    from .validate_atlas_grounding_staging import require_token_lifetime
except ImportError:
    from validate_managed_accounts import gc, ORIGIN, SERVICE
    from validate_atlas_grounding_staging import require_token_lifetime

def valid_concurrent_outcome(rows):
    return (len(rows) == 2 and any(r['http_status'] == 200 for r in rows)
            and all((r['http_status'] == 200 and r['model_called'] is True)
                    or (r['http_status'] == 503 and r['error_code'] == 'busy'
                        and r['model_called'] is False) for r in rows))


async def run(state, seed, output, concurrency_only=False):
    if state.get('disabled') or not seed.get('synthetic'):
        raise ValueError('Active synthetic fixture and synthetic saved-job evidence required')
    iam = gc('auth', 'print-identity-token')
    require_token_lifetime(iam, 'Operator', minimum=1000)
    member = state['users']['member']['idToken']
    require_token_lifetime(member, 'Synthetic member', minimum=1000)
    url = gc('run','services','describe',SERVICE,'--region=us-central1','--format=value(status.url)')
    with output.open('x',encoding='utf-8') as evidence:
        def record(row):
            evidence.write(json.dumps(row)+'\n'); evidence.flush(); print(json.dumps(row),flush=True)
        async with httpx.AsyncClient(base_url=url,trust_env=False,follow_redirects=False,timeout=310) as client:
            config = await client.get('/api/identities',headers={'X-Serverless-Authorization':'Bearer '+iam})
            config.raise_for_status()
            header = config.json()['auth_header']
            if header not in ('Authorization','X-WZOS-Authorization'): raise ValueError('Unexpected auth header')
            client.headers.update({'X-Serverless-Authorization':'Bearer '+iam,header:'Bearer '+member,
                                   'X-WZOS-Organization':state['orgs']['main'],'Origin':ORIGIN})
            payload = {'order_id':seed['job_id'],'expected_version':seed['response']['order_version'],
                       'page':'report','question':seed['question']}
            async def request(label):
                start = time.monotonic()
                identity = {'stage':label,'request_id':str(uuid4()),
                            'started_at':datetime.now(timezone.utc).isoformat()}
                try:
                    reply = await client.post('/api/assistant/chat',json={**payload,'request_id':identity['request_id']})
                    body = reply.json()
                    if not isinstance(body,dict):
                        raise ValueError('Expected response object')
                    row = {**identity,'http_status':reply.status_code,'seconds':round(time.monotonic()-start,3),
                           'model_called':body.get('model_called',False),
                           'error_code':body.get('code') if body.get('code') in ('busy','disabled','timeout','provider_error','unavailable') else None,
                           'correlation_id':body.get('correlation_id') if isinstance(body.get('correlation_id'),str) and len(body['correlation_id'])==32 and all(c in '0123456789abcdef' for c in body['correlation_id']) else None}
                    if reply.status_code == 200:
                        if (body.get('model_called') is not True
                                or body.get('approved_for_field_use') is not False
                                or body.get('actions_performed') != []):
                            raise ValueError('Invalid successful response contract')
                    record(row)
                    return row
                except asyncio.CancelledError:
                    record({**identity,'client_cancelled':True,'provider_cancellation_verified':False})
                    raise
                except (httpx.HTTPError,ValueError) as error:
                    record({**identity,'seconds':round(time.monotonic()-start,3),'error_type':type(error).__name__})
                    raise
            # Preserve both bounded outcomes even if one transport/contract fails.
            # gather's default early exception can otherwise cancel the peer when
            # the runner closes, obscuring the evidence for the concurrent pair.
            statuses = await asyncio.gather(request('concurrent_a'),request('concurrent_b'),return_exceptions=True)
            if any(isinstance(row,BaseException) for row in statuses):
                raise RuntimeError('Concurrent request failed; inspect sanitized evidence')
            if not valid_concurrent_outcome(statuses):
                raise RuntimeError('Unexpected concurrent outcome; inspect sanitized evidence and cloud logs')
            if concurrency_only:
                record({'stage':'complete','scope':'two_requests_only','sustained_capacity_verified':False})
                return
            pending = asyncio.create_task(request('client_disconnect'))
            await asyncio.sleep(0.25)
            if pending.done():
                await pending
                record({'stage':'disconnect_observation','inconclusive':'response completed before cancellation'})
            else:
                pending.cancel()
                try: await pending
                except asyncio.CancelledError: pass
            await asyncio.sleep(3)
            if (await request('after_disconnect'))['http_status'] != 200:
                raise RuntimeError('Post-disconnect recovery not accepted; no automatic retries')
            record({'stage':'complete','cold_start_verified':False,'provider_cancellation_verified':False})

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state',type=Path,required=True);p.add_argument('--seed',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--concurrency-only',action='store_true');a=p.parse_args()
    seed=json.loads(a.seed.read_text().splitlines()[-1])
    asyncio.run(run(json.loads(a.state.read_text()),seed,a.output,a.concurrency_only))
