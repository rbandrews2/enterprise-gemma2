"""Private self-hosted full-size Gemma. No credentials or URLs from user input."""
import os
import re

from services.workspace_preview.cloud_intelligence import metadata_identity_token, service_url
from services.workspace_preview.intelligence import ModelUnavailable
from services.workspace_preview.managed_intelligence import ManagedGemmaIntelligence


class VLLMIntelligence(ManagedGemmaIntelligence):
    mode = 'private_vllm'
    model = 'google/gemma-4-31B-it'
    # Allows cold startup; the calling Cloud Run application must use >= 300s.
    deadline = 290

    def __init__(self, transport=None, token_provider=None):
        super().__init__(transport, token_provider or metadata_identity_token)
        self.origin = service_url(os.getenv('WZOS_ATLAS_VLLM_URL', ''))
        self.endpoint = self.origin + '/v1/chat/completions'

    def enabled(self):
        return os.getenv('WZOS_ATLAS_VLLM_ENABLED') == '1'

    async def request_headers(self):
        token = await self.token_provider(self.origin)
        if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', token):
            raise ModelUnavailable('Atlas service authentication is unavailable.')
        return {'Authorization': 'Bearer ' + token}
