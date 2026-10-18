"""Focused no-network check for the synthetic harness readiness guard."""
import asyncio
import base64
import json
from check_field_voice_workflow import private_model_ready
import httpx

ORIGIN='https://synthetic-atlas.run.app'

async def token(origin):
    body={'aud':origin,'sub':'synthetic','email':'wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com'}
    return 'synthetic.'+base64.urlsafe_b64encode(json.dumps(body).encode()).decode().rstrip('=')+'.signature'

async def check(statuses, expected=None):
    calls=[]
    def handle(request):
        assert request.url.path=='/health' and request.method=='GET'
        calls.append(True)
        return httpx.Response(statuses[min(len(calls)-1,len(statuses)-1)])
    try:
        result=await private_model_ready(ORIGIN,token,httpx.MockTransport(handle),attempts=3,pause=0)
        assert result==expected
    except RuntimeError:
        assert expected is None
    return len(calls)

async def main():
    assert await check([200],1)==1
    assert await check([403,403,200],3)==3
    assert await check([403])==3
    assert await check([401])==1
    assert await check([302])==1
    async def wrong(origin):return await token('https://other.run.app')
    try:
        await private_model_ready(ORIGIN,wrong)
        raise AssertionError('Wrong audience accepted')
    except RuntimeError as error:
        assert str(error)=='metadata token routing mismatch'
    print('FIELD_VOICE_READINESS_GUARD_PASS checks=6 provider_calls=0')

asyncio.run(main())
