"""Opt-in private Cloud Run Ollama adapter, prepared locally; not provisioned.

Uses the runtime's short-lived Google service identity. No browser token,
service-account key download, redirects, proxies or alternate fallback provider.
"""
import os
import re
import httpx
from services.workspace_preview.intelligence import LocalIntelligence, ModelUnavailable

METADATA_IDENTITY = ('http://metadata.google.internal/computeMetadata/v1/'
                     'instance/service-accounts/default/identity')


def service_url(value):
    # Operator config only. Canonical run.app service origin is also the audience.
    # Custom domains, traffic tags, paths, credentials, queries and ports are not supported.
    if not isinstance(value,str) or not re.fullmatch(r'https://[a-z0-9-]+(?:\.[a-z0-9-]+)*\.run\.app/?',value):
        raise ValueError('Atlas requires a canonical HTTPS Cloud Run service origin')
    origin=value.rstrip('/')
    if '---' in origin:
        raise ValueError('Use the canonical service origin, not a traffic-tag URL')
    return origin


async def metadata_identity_token(audience, transport=None):
    if not os.getenv('K_SERVICE'):
        raise ModelUnavailable('Cloud Atlas requires its configured service identity.')
    try:
        async with httpx.AsyncClient(transport=transport,trust_env=False,follow_redirects=False,timeout=5) as client:
            async with client.stream('GET', METADATA_IDENTITY,params={'audience':audience},
                                     headers={'Metadata-Flavor':'Google'}) as response:
                response.raise_for_status()
                if response.headers.get('Metadata-Flavor') != 'Google':
                    raise ValueError('Unexpected identity response')
                body=bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body)>16384:
                        raise ValueError('Oversized identity response')
        token=body.decode('ascii').strip()
        # Shape check only: the receiving Cloud Run IAM layer verifies the token.
        if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',token):
            raise ValueError('Invalid identity response')
        return token
    except (httpx.HTTPError,ValueError,UnicodeError) as error:
        raise ModelUnavailable('Atlas could not authenticate to its configured service.') from error


class CloudRunIntelligence(LocalIntelligence):
    mode='cloud_run'

    def __init__(self, transport=None, token_provider=None):
        if os.getenv('WZOS_ATLAS_CLOUD_ENABLED') != '1':
            raise ValueError('Cloud Atlas requires explicit operator enablement')
        super().__init__(transport)
        self.url=service_url(os.getenv('WZOS_ATLAS_CLOUD_RUN_URL',''))
        self.token_provider=token_provider or metadata_identity_token

    def enabled(self):
        return os.getenv('WZOS_ATLAS_CLOUD_ENABLED') == '1'

    async def request_headers(self):
        token=await self.token_provider(self.url)
        if not isinstance(token,str) or not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',token):
            raise ModelUnavailable('Atlas could not authenticate to its configured service.')
        return {'Authorization':'Bearer '+token}
