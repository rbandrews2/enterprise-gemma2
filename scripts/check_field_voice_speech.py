"""Four synthetic multi-sentence Speech checks; no Gemma, DB, storage or sends."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import re
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
PATTERNS={
    'traffic-devices':{'fifty':r'\b(?:50|fifty)\b','drums':r'\bdrums?\b','four':r'\b(?:4|four)\b','arrow_boards':r'\barrow\s*boards?\b'},
    'explicit-no-incident':{'forty':r'\b(?:40|forty)\b','cones':r'\bcones?\b','negation':r'\bno\b','incidents':r'\bincidents?\b'},
    'two-incidents':{'car':r'\bcar\b','cone':r'\bcones?\b','truck':r'\btruck\b','breakdown':r'\bbroke\s+down\b'},
    'ambiguous-time':{'around_nine':r'\baround\s+(?:9|nine)\b','morning':r'\bmorning\b','evening':r'\bevening\b'},
}

def cues(case,text):
    return {name:bool(re.search(pattern,text,re.I)) for name,pattern in PATTERNS[case].items()}

async def run(audio_root):
    assert os.getenv('CLOUD_RUN_JOB')=='wzos-field-voice-speech-pilot'
    assert os.getenv('WZOS_FIELD_VOICE_SPEECH_MODEL')=='long'
    assert os.getenv('WZOS_FIELD_VOICE_SPEECH_ENABLED')=='1'
    assert not any(os.getenv(k) for k in ('K_SERVICE','WZOS_DATABASE_URL','WZOS_FILES_BUCKET','WZOS_FIELD_VOICE_MODEL_URL'))
    from services.workspace_preview.field_voice_transport import Speech
    speech=Speech(); checks=[]
    for case in PATTERNS:
        started=time.monotonic();audio=(audio_root/(case+'.wav')).read_bytes()
        try:
            text=await speech.transcribe(audio)
            found=cues(case,text)
            checks.append({'case':case,'status':'PASS' if all(found.values()) else 'FAIL','cues':found,'seconds':round(time.monotonic()-started,2)})
            del text
        finally:
            del audio
    result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL',
        'synthetic_only':True,'transcription_model':'long','speech_requests':4,
        'model_requests':0,'sms_sent':0,'raw_audio_or_transcript_logged':False,'checks':checks}
    print(json.dumps(result),flush=True)
    return result['status']=='PASS'

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--audio-root',type=Path,required=True);args=parser.parse_args()
    try:
        if not asyncio.run(run(args.audio_root)):raise SystemExit(1)
    except Exception as error:
        print(json.dumps({'status':'FAIL','error_type':type(error).__name__}),flush=True)
        raise SystemExit(1)
