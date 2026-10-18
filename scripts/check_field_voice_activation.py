"""Read-only activation checks. No user recordings, provider calls or credentials in output."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

phase, directory = sys.argv[1:]
root = Path(directory)
read = lambda name: json.loads((root/name).read_text())
traffic = lambda service: [(t.get('revisionName'), t.get('percent')) for t in service['status']['traffic'] if t.get('percent')]
tag = (root/'source-commit.txt').read_text().strip()[:7]
prior = [('wzos-v2-accounts-mobile-c944173',100)]
if phase == 'pilot':
    value = read('pilot-result.json')
    assert value['status']=='PASS' and value['mode']=='live' and value['synthetic_only']
    assert value['speech_requests']==10 and 8<=value['model_requests']<=10
    assert value['sms_sent']==0 and value['raw_audio_or_transcript_logged'] is False
elif phase == 'baseline':
    before, actual = read('app-before.json'), read('activation-before.json')
    assert before['spec']==actual['spec'] and traffic(actual)==prior, 'Review live configuration drift'
    env={e['name']:e.get('value') for e in actual['spec']['template']['spec']['containers'][0]['env']}
    assert env.get('WZOS_ATLAS_VLLM_ENABLED','0')=='0', 'Ordinary chat must remain unchanged'
elif phase == 'model':
    s,iam=read('hosting-ready.json'),read('hosting-iam.json')
    assert any(c['type']=='Ready' and c['status']=='True' for c in s['status']['conditions'])
    spec=s['spec']['template']['spec'];c=spec['containers'][0];annotations=s['spec']['template']['metadata']['annotations']
    assert s['metadata']['labels']['wzos-pilot']==(root/'hosting-nonce.txt').read_text().strip()
    assert spec['serviceAccountName']=='wzos-atlas-inference@enterprise-gemma2.iam.gserviceaccount.com'
    assert c['image'].endswith('@sha256:3fbc0e08c46e7736145c9effbcc8839682c80b15b413335146f4428fc3523c8a')
    assert c['resources']['limits']=={'cpu':'20','memory':'80Gi','nvidia.com/gpu':'1'}
    assert '--no-enable-log-requests' in c['args'] and not any(e.get('valueFrom') for e in c.get('env',[]))
    assert annotations['autoscaling.knative.dev/maxScale']=='1'
    assert annotations.get('autoscaling.knative.dev/minScale','0')=='0'
    members={m for b in iam.get('bindings',[]) if b['role']=='roles/run.invoker' for m in b.get('members',[])}
    assert members=={'serviceAccount:wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com'}
    assert not any(m in ('allUsers','allAuthenticatedUsers') for b in iam.get('bindings',[]) for m in b.get('members',[]))
    (root/'hosting-url.txt').write_text(s['status']['url'])
elif phase == 'cleanup-owner':
    s=read('hosting-cleanup-before.json')
    assert s['metadata']['labels']['wzos-pilot']==(root/'hosting-nonce.txt').read_text().strip()
    assert s['spec']['template']['spec']['serviceAccountName']=='wzos-atlas-inference@enterprise-gemma2.iam.gserviceaccount.com'
elif phase == 'cleanup-absent':
    assert read('hosting-cleanup-after.json')==[]
elif phase == 'staged':
    before,staged=read('activation-before.json'),read('voice-staged.json')
    ignored={'run.googleapis.com/client-name','run.googleapis.com/client-version','run.googleapis.com/operation-id','serving.knative.dev/creator'}
    annotation=lambda metadata:{k:v for k,v in metadata.get('annotations',{}).items() if k not in ignored}
    for mode,value in [('hold','0'),('live','1')]:
        r=read('voice-'+mode+'-revision.json');expected=copy.deepcopy(before['spec']['template']['spec']);actual=copy.deepcopy(r['spec'])
        assert any(c['type']=='Ready' and c['status']=='True' for c in r['status']['conditions'])
        assert r['status']['imageDigest']==(root/'app-image.txt').read_text().strip()
        actual['containers'][0]['image']=expected['containers'][0]['image']
        if 'name' not in expected['containers'][0]:actual['containers'][0].pop('name',None)
        old={e['name']:e for e in expected['containers'][0].pop('env')}
        env={e['name']:e for e in actual['containers'][0].pop('env')}
        for key in ('WZOS_FIELD_VOICE_ENABLED','WZOS_FIELD_VOICE_SPEECH_ENABLED','WZOS_FIELD_VOICE_MODEL_ENABLED'):
            old.pop(key,None);assert env.pop(key)=={'name':key,'value':value}
        key='WZOS_FIELD_VOICE_MODEL_URL';old.pop(key,None)
        assert env.pop(key)=={'name':key,'value':(root/'hosting-url.txt').read_text().strip()}
        assert env==old and actual==expected, 'Runtime or existing secret/configuration change'
        assert annotation(r['metadata'])==annotation(before['spec']['template']['metadata'])
    assert traffic(staged)==prior
    for key in ('run.googleapis.com/ingress','run.googleapis.com/invoker-iam-disabled'):
        assert staged['metadata']['annotations'].get(key)==before['metadata']['annotations'].get(key)
elif phase == 'public':
    static=root/'source/services/workspace_preview/static'
    for name in ('field-voice.js','field-voice.css','device-setup.js','mobile-home.js','workspace.css','workspace.js','organization-hub.js','weather.js','install.js'):
        with urllib.request.urlopen('https://app.workzoneos.org/'+name+'?voice='+tag,timeout=45) as response:
            assert response.status==200 and hashlib.sha256(response.read()).digest()==hashlib.sha256((static/name).read_bytes()).digest(), name+' mismatch'
    for path in ('/api/field-voice/config','/api/field-voice/jobs','/api/field-voice/drafts','/api/weather/notices','/api/account/upgrade'):
        try:
            urllib.request.urlopen('https://app.workzoneos.org'+path,timeout=30)
            raise AssertionError('Anonymous data exposed')
        except urllib.error.HTTPError as error:assert error.code==401
    with urllib.request.urlopen('https://app.workzoneos.org/api/app/version?voice='+tag,timeout=30) as response:
        (root/'voice-version.json').write_bytes(response.read())
elif phase == 'traffic':
    assert traffic(read('voice-live.json'))==[('wzos-v2-accounts-voice-live-'+tag,100)]
else:
    raise ValueError('Unknown phase')
print('FIELD_VOICE_ACTIVATION_'+phase.upper()+'_PASS')
