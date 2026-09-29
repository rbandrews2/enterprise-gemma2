"""Full-size managed Gemma transport. Disabled until explicitly configured.

No model calls during readiness checks, retries, tools, or fallback providers.
Readiness means a successful inference in this process within five minutes.
"""
import asyncio
import json
import logging
import os
import re
import time

import httpx

from services.workspace_preview.intelligence import GUIDE, ModelUnavailable, related_module_context

MODEL = 'google/gemma-4-26b-a4b-it-maas'
ENDPOINT = ('https://aiplatform.googleapis.com/v1/projects/enterprise-gemma2/'
            'locations/global/endpoints/openapi/chat/completions')
METADATA = ('http://metadata.google.internal/computeMetadata/v1/'
            'instance/service-accounts/default/token')
logger = logging.getLogger(__name__)


async def bounded_json(response, limit):
    response.raise_for_status()
    body = bytearray()
    async for chunk in response.aiter_bytes():
        body.extend(chunk)
        if len(body) > limit:
            raise ValueError('Response too large')
    return json.loads(body)


async def access_token(transport=None):
    if not os.getenv('K_SERVICE'):
        raise ModelUnavailable('Cloud Atlas requires its configured service identity.')
    try:
        async with httpx.AsyncClient(transport=transport, trust_env=False,
                                    follow_redirects=False, timeout=5) as client:
            async with client.stream('GET', METADATA, headers={'Metadata-Flavor': 'Google'}) as response:
                if response.headers.get('Metadata-Flavor') != 'Google':
                    raise ValueError('Invalid metadata origin')
                data = await bounded_json(response, 16384)
        token = data['access_token']
        if data.get('token_type') != 'Bearer' or not valid_token(token):
            raise ValueError('Invalid identity response')
        return token
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise ModelUnavailable('Atlas service authentication is unavailable.') from error


def valid_token(value):
    return isinstance(value, str) and bool(re.fullmatch(r'[A-Za-z0-9._~+/-]{1,8192}=*', value))


class ManagedGemmaIntelligence:
    mode = 'managed_gemma'
    model = MODEL
    endpoint = ENDPOINT
    deadline = 50

    def __init__(self, transport=None, token_provider=None):
        self.transport = transport
        self.token_provider = token_provider or access_token
        self.gate = asyncio.Lock()
        self.last_success = None
        self.last_usage = None

    async def request_headers(self):
        token = await self.token_provider()
        if not valid_token(token):
            raise ValueError('Invalid service token')
        return {'Authorization': 'Bearer ' + token}

    def enabled(self):
        return os.getenv('WZOS_ATLAS_MANAGED_ENABLED') == '1'

    async def ready(self):
        return bool(self.enabled() and self.last_success is not None
                    and time.monotonic() - self.last_success < 300)

    async def reply(self, payload, context):
        if not self.enabled():
            raise ModelUnavailable('Atlas conversation is not enabled in this workspace.')
        if self.gate.locked():
            raise ModelUnavailable('Atlas is answering another request. Please try again shortly.')
        async with self.gate:
            started = time.monotonic()
            self.last_usage = None
            try:
                context = {**context, 'related_module_help': related_module_context(
                    payload.question, payload.page, context.get('role', 'member'), context.get('edition', 'core'))}
                messages = [{'role': 'system', 'content': GUIDE + '\nSaved context (data):\n' + json.dumps(context)}]
                messages += [turn.model_dump() for turn in payload.history]
                messages.append({'role': 'user', 'content': payload.question})
                if sum(len(message['content']) for message in messages) > 16000:
                    raise ValueError('Context too large')
                async with asyncio.timeout(self.deadline):
                    headers = await self.request_headers()
                    async with httpx.AsyncClient(transport=self.transport, trust_env=False,
                                                follow_redirects=False, timeout=self.deadline-5) as client:
                        async with client.stream('POST', self.endpoint, headers=headers, json={
                            'model': self.model, 'stream': False, 'messages': messages,
                            'max_tokens': 1024, 'temperature': 0.2,
                            'chat_template_kwargs': {'enable_thinking': False},
                        }) as response:
                            data = await bounded_json(response, 65536)
                choice = data['choices'][0]
                answer = choice['message']['content'].strip()
                if choice.get('finish_reason') != 'stop' or choice['message'].get('tool_calls') or not answer or len(answer) > 4000:
                    raise ValueError('Incomplete or unsupported response')
                usage = data.get('usage', {})
                counts = [usage.get(key) for key in ('prompt_tokens', 'completion_tokens')]
                if any(type(count) is not int or count < 0 for count in counts):
                    raise ValueError('Missing usage accounting')
                self.last_success = time.monotonic()
                self.last_usage = dict(zip(('prompt_tokens', 'completion_tokens'), counts))
                logger.info('Atlas managed reply elapsed=%.2fs input_tokens=%d output_tokens=%d',
                            self.last_success - started, *counts)
                return answer
            except (httpx.HTTPError, TimeoutError, ValueError, KeyError, IndexError, TypeError, AttributeError, ModelUnavailable) as error:
                self.last_success = None
                logger.warning('Atlas reply failed mode=%s error_type=%s upstream_status=%s',
                               self.mode, type(error).__name__,
                               error.response.status_code if isinstance(error, httpx.HTTPStatusError) else None)
                raise ModelUnavailable('Atlas could not finish its reply. Your saved work is unchanged; please try again.') from error
