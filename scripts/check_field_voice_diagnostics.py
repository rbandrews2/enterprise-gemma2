"""No-network acceptance of diagnostic continuation without weakening failures."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch
import check_field_voice_workflow as workflow

original=workflow.assess
def forced(case, report):
    if case=='traffic-devices':
        raise RuntimeError('Synthetic forced mismatch')
    return original(case,report)

output=io.StringIO()
with patch.object(workflow,'assess',forced),redirect_stdout(output):
    assert workflow.run(Path(sys.argv[1]),'mocked') is False
result=json.loads(output.getvalue())
assert result['status']=='FAIL' and len(result['checks'])==10
assert result['speech_requests']==10 and result['model_requests']==8 and result['sms_sent']==0
failed=[c for c in result['checks'] if c['status']=='FAIL']
assert len(failed)==1 and failed[0]['check']=='Synthetic forced mismatch'
assert failed[0]['extraction']['quantities'][0]['quantity']==50
assert all(isinstance(v,bool) for v in failed[0]['speech_cues'].values())
assert result['raw_audio_or_transcript_logged'] is False
print('FIELD_VOICE_DIAGNOSTIC_CONTINUATION_PASS checks=10 paid_provider_calls=0')
