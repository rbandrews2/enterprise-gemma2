"""Readiness-only disposable job: no recordings, inference or persistence."""
import asyncio
import json
import os
import sys
from unittest.mock import patch

sys.path.insert(0, '/app/scripts')
from check_field_voice_workflow import private_model_ready
from services.workspace_preview.cloud_intelligence import metadata_identity_token, service_url

assert os.getenv('CLOUD_RUN_JOB') == 'wzos-field-voice-ready'
assert not any(os.getenv(k) for k in ('K_SERVICE','WZOS_DATABASE_URL','WZOS_FILES_BUCKET'))

async def identity(audience):
    with patch.dict(os.environ, {'K_SERVICE':'wzos-field-voice-ready'}):
        return await metadata_identity_token(audience)

try:
    count=asyncio.run(private_model_ready(service_url(os.environ['WZOS_FIELD_VOICE_MODEL_URL']),identity))
    print(json.dumps({'status':'PASS','model_readiness_checks':count,'speech_requests':0,'model_requests':0}),flush=True)
except Exception as error:
    print(json.dumps({'status':'FAIL','check':str(error) if isinstance(error,RuntimeError) else type(error).__name__}),flush=True)
    raise SystemExit(1)
