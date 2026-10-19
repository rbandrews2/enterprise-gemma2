"""Explicitly approved semantic pilot after one isolated lexical ASR mismatch.

Does not turn a failed Speech result into PASS or relax any report assertions.
No provider calls in check/self-check modes; run delegates to guarded pilot.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

EXPECTED={
    'traffic-devices':{'arrow_boards':False,'drums':True,'fifty':True,'four':True},
    'explicit-no-incident':{'cones':True,'forty':True,'incidents':True,'negation':True},
    'two-incidents':{'breakdown':True,'car':True,'cone':True,'truck':True},
    'ambiguous-time':{'around_nine':True,'evening':True,'morning':True},
}
IMAGE='us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-field-voice-pilot@sha256:86c814b8ea752894e9293d63235f987ae5f0339979a51edf5c6fbe13e83afaab'

def validate(result):
    assert result['status']=='FAIL' and result['synthetic_only'] is True
    assert result['transcription_model']=='long' and result['speech_requests']==4
    assert result['model_requests']==result['sms_sent']==0
    assert result['raw_audio_or_transcript_logged'] is False
    checks=result['checks']; assert len(checks)==4
    assert {c['case'] for c in checks}==set(EXPECTED)
    for check in checks:
        assert check['cues']==EXPECTED[check['case']], 'Additional recognition failure requires review'
        assert all(type(v) is bool for v in check['cues'].values())
        assert check['status']==('FAIL' if check['case']=='traffic-devices' else 'PASS')

def self_check():
    good={'status':'FAIL','synthetic_only':True,'transcription_model':'long',
          'speech_requests':4,'model_requests':0,'sms_sent':0,'raw_audio_or_transcript_logged':False,
          'checks':[{'case':case,'cues':copy.deepcopy(cues),
                     'status':'FAIL' if case=='traffic-devices' else 'PASS'} for case,cues in EXPECTED.items()]}
    validate(good)
    mutations=[lambda x:x['checks'][0]['cues'].update(fifty=False),
               lambda x:x['checks'][1]['cues'].update(negation=False),
               lambda x:x.update(status='PASS'),lambda x:x.update(model_requests=1)]
    for mutate in mutations:
        bad=copy.deepcopy(good);mutate(bad)
        try:validate(bad)
        except AssertionError:pass
        else:raise AssertionError('Unexpected failure classification accepted')
    print('SEMANTIC_REVIEW_GUARD_PASS cases=5 provider_calls=0')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['check','run','self-check'])
    parser.add_argument('root',type=Path,nargs='?');args=parser.parse_args()
    if args.mode=='self-check':self_check();raise SystemExit(0)
    root=args.root.resolve()
    validate(json.loads((root/'speech-result.json').read_text()))
    assert (root/'speech-pilot.exit').read_text().strip()=='1'
    assert (root/'speech-cleanup.verified').read_text().strip()=='0'
    assert (root/'job-image.txt').read_text().strip()==IMAGE
    assert (root/'speech-model.txt').read_text().strip()=='long'
    subprocess.run([sys.executable,str(root/'check_runtime.py'),str(root)],check=True)
    print('ISOLATED_LEXICAL_MISMATCH_VERIFIED_FULL_REPORT_ASSERTIONS_UNCHANGED',flush=True)
    if args.mode=='run':
        assert (root/'semantic-pilot-approved').is_file()
        with (root/'semantic-pilot.started').open('x') as handle:
            handle.write(datetime.now(timezone.utc).isoformat()+'\n')
        raise SystemExit(subprocess.run(['bash',str(root/'run_pilot.sh'),'run',str(root)]).returncode)
