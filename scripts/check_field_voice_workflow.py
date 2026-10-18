"""Ten synthetic audio attempts through real Speech/Gemma and an isolated app.

No production DB/bucket binding, customer identity, listener or outbound SMS.
Only structured check summaries are printed; never audio or raw transcripts.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
JOB = 'wzos-field-voice-pilot'
CASES = ['traffic-devices', 'explicit-no-incident', 'quantity-correction',
         'two-incidents', 'unknown-quantity', 'unrelated', 'injection',
         'ambiguous-time', 'silence', 'noise']


def require(value, check):
    if not value:
        raise RuntimeError(check)


def assess(case, report):
    quantities, incidents = report['production_quantities'], report['incidents']
    values = [q['quantity'] for q in quantities]
    if case == 'traffic-devices':
        require(any(q['quantity'] == 50 and 'drum' in q['item_name'].lower() for q in quantities), '50 drums')
        require(any(q['quantity'] == 4 and 'arrow' in q['item_name'].lower() for q in quantities), '4 arrow boards')
        require(len(incidents) == 1 and incidents[0]['time_mentioned'], 'one timed incident')
    elif case == 'explicit-no-incident':
        require(not incidents and 40 in values, 'negation')
    elif case == 'quantity-correction':
        require(values == [50], 'corrected quantity only')
    elif case == 'two-incidents':
        require(len(incidents) == 2 and all(i['time_mentioned'] for i in incidents), 'two timed incidents')
    elif case == 'unknown-quantity':
        require(not quantities or all(q['quantity'] is None for q in quantities), 'unknown stays unknown')
    elif case == 'ambiguous-time':
        text = json.dumps(report).lower()
        require('am' not in str([i['time_mentioned'] for i in incidents]).lower()
                and 'pm' not in str([i['time_mentioned'] for i in incidents]).lower(), 'no invented meridiem')
        require(report['unresolved'] or any(i['time_mentioned'] for i in incidents), 'uncertainty visible')


def run(audio_root, mode='live'):
    require((mode == 'live' and os.getenv('CLOUD_RUN_JOB') == JOB)
            or (mode == 'mocked' and not os.getenv('CLOUD_RUN_JOB')), 'dedicated job required')
    require(not any(os.getenv(k) for k in ('K_SERVICE', 'GAE_ENV', 'NETLIFY',
        'WZOS_DATABASE_URL', 'WZOS_FILES_BUCKET', 'FIREBASE_AUTH_EMULATOR_HOST')), 'external persistence forbidden')
    from fastapi.testclient import TestClient
    from services.workspace_preview.app import create_app
    from services.workspace_preview.cloud_intelligence import metadata_identity_token
    from services.workspace_preview.field_voice_transport import Extractor, Speech, validate_audio
    from services.workspace_preview.files import LocalFiles
    from services.workspace_preview.storage import SQLiteStorage
    from services.v2.knowledge.store import Store
    import httpx

    model_calls, speech_calls = [], []

    async def identity(audience):
        if mode == 'mocked':
            return 'synthetic.google.token'
        with patch.dict(os.environ, {'K_SERVICE': JOB}):
            return await metadata_identity_token(audience)

    async def speech_identity():
        return 'synthetic.adc.token'

    def fake_speech(request):
        digest = hashlib.sha256(base64.b64decode(json.loads(request.content)['content'])).digest()
        case = next(c for c in CASES if hashlib.sha256((audio_root/(c+'.wav')).read_bytes()).digest() == digest)
        return httpx.Response(200, json={'results': [] if case in ('noise', 'silence') else [
            {'alternatives':[{'transcript':'Synthetic fixture '+case}]}]})

    def fake_model(request):
        transcript = json.loads(json.loads(request.content)['messages'][1]['content'])['transcript']
        case = transcript.removeprefix('Synthetic fixture ')
        report = {'schema_version':1, 'is_relevant':case not in ('injection', 'unrelated'),
            'route_location':'Route 29', 'work_description':'Synthetic lane closure.',
            'production_quantities':[], 'incidents':[], 'unresolved':[]}
        def quantity(name, count):
            return {'item_name':name, 'quantity':count, 'unit':'each'}
        def incident(time):
            return {'details':'Synthetic incident.', 'time_mentioned':time, 'priority':None}
        if case == 'traffic-devices':
            report['production_quantities'] = [quantity('Drums',50), quantity('Arrow boards',4)]
            report['incidents'] = [incident('9:15 AM')]
        elif case in ('explicit-no-incident', 'quantity-correction', 'unknown-quantity'):
            report['production_quantities'] = [quantity('Drums', {'explicit-no-incident':40, 'quantity-correction':50, 'unknown-quantity':None}[case])]
        elif case == 'two-incidents':
            report['incidents'] = [incident('8:15 AM'), incident('9:10 AM')]
        elif case == 'ambiguous-time':
            report['incidents'] = [incident('around nine; unclear morning or evening')]
            report['unresolved'] = ['Confirm the incident time.']
        return httpx.Response(200, json={'choices':[{'finish_reason':'stop', 'message':{'content':json.dumps(report)}}]})

    class CountingSpeech(Speech):
        async def transcribe(self, audio):
            require(len(speech_calls) < 10, 'speech request budget')
            speech_calls.append(True)
            return await super().transcribe(audio)

    class CountingExtractor(Extractor):
        async def extract(self, transcript, job, schema):
            require(len(model_calls) < 10, 'model request budget')
            model_calls.append(True)
            return await super().extract(transcript, job, schema)

    claims = {name: {'uid': name, 'name': 'Synthetic '+name,
        'email': name+'@example.test', 'email_verified': True} for name in CASES+['core', 'outsider', 'worker']}
    settings = {'WZOS_ACCOUNT_WORKSPACE':'1', 'WZOS_FIELD_VOICE_ENABLED':'1',
        'WZOS_FIELD_VOICE_SPEECH_ENABLED':'1', 'WZOS_FIELD_VOICE_MODEL_ENABLED':'1',
        'WZOS_ATLAS_VLLM_ENABLED':'0'}
    checks, saved = [], 0
    with patch.dict(os.environ, settings), tempfile.TemporaryDirectory(prefix='wzos-voice-pilot-') as directory:
        root = Path(directory)
        storage = SQLiteStorage(root/'synthetic.sqlite')
        app = create_app(root/'unused', Store(root/'sources', {}), account_workspace=True,
            storage=storage, verifier=lambda token: claims[token], file_store=LocalFiles(root/'files'))
        app.state.field_voice_speech = CountingSpeech(transport=httpx.MockTransport(fake_speech),
            token_provider=speech_identity) if mode == 'mocked' else CountingSpeech()
        app.state.field_voice_extractor = CountingExtractor(token_provider=identity,
            transport=httpx.MockTransport(fake_model) if mode == 'mocked' else None)
        with TestClient(app) as client:
            def org(who, edition='enterprise'):
                response = client.post('/api/account/organizations', headers={'Authorization':'Bearer '+who},
                    json={'name':'Synthetic voice '+who, 'activation_code':app.state.accounts.issue_activation(edition)})
                require(response.status_code == 200, 'synthetic organization')
                return response.json()['id']

            core, outsider = org('core', 'core'), org('outsider')
            for case in CASES:
                organization = org(case)
                headers = {'Authorization':'Bearer '+case, 'X-WZOS-Organization':organization}
                if case == CASES[0]:
                    invitation = client.post('/api/account/invitations', headers=headers,
                        json={'email':'worker@example.test', 'role':'member'})
                    require(invitation.status_code == 200, 'synthetic member invitation')
                    joined = client.post('/api/account/join', headers={'Authorization':'Bearer worker'},
                        json={'token':invitation.json()['token']})
                    require(joined.status_code == 200, 'synthetic member')
                    headers['Authorization'] = 'Bearer worker'
                response = client.post('/api/orders', headers=headers, json={'request_id':str(uuid4()),
                    'title':'Synthetic pilot '+case, 'address':'Route 29', 'locality':'Norfolk', 'work_type':'road_maintenance'})
                require(response.status_code == 201, 'synthetic job')
                basis = {'job_id':response.json()['id'], 'expected_job_version':1}
                if case == CASES[0]:
                    for who, target, status in [('core', core, 403), ('outsider', outsider, 404)]:
                        denial = client.post('/api/field-voice/extract',
                            headers={'Authorization':'Bearer '+who, 'X-WZOS-Organization':target},
                            json={**basis, 'transcript':'Synthetic road work.'})
                        require(denial.status_code == status, 'pre-inference access boundary')
                    stale = client.post('/api/field-voice/extract', headers=headers,
                        json={**basis, 'expected_job_version':99, 'transcript':'Synthetic road work.'})
                    require(stale.status_code == 409 and not model_calls and not speech_calls, 'stale before paid calls')
                audio = (audio_root/(case+'.wav')).read_bytes()
                validate_audio(audio)
                started = time.monotonic()
                response = client.post('/api/field-voice/transcribe', params=basis,
                    headers={**headers, 'Content-Type':'audio/wav'}, content=audio)
                del audio
                if case in ('silence', 'noise'):
                    if response.status_code == 200:
                        # An ASR fragment must still never become an actionable work report.
                        fragment = response.json()['transcript']
                        rejected = client.post('/api/field-voice/extract', headers=headers,
                            json={**basis, 'transcript':fragment})
                        del fragment
                        require(rejected.status_code in (422,), case+' cannot create work')
                    else:
                        require(response.status_code == 503, case+' handled without a draft')
                    checks.append({'case':case, 'status':'no_draft', 'seconds':round(time.monotonic()-started, 2)})
                    continue
                require(response.status_code == 200 and response.json()['audio_retained'] is False, case+' transcription')
                transcript = response.json()['transcript']
                response = client.post('/api/field-voice/extract', headers=headers, json={**basis, 'transcript':transcript})
                del transcript
                if case in ('unrelated', 'injection'):
                    require(response.status_code == 422, case+' must not create work')
                    checks.append({'case':case, 'status':'rejected', 'seconds':round(time.monotonic()-started, 2)})
                    continue
                require(response.status_code == 200, case+' structured extraction')
                fields = response.json()['fields']; require(fields['work_date'] is None, 'no invented date')
                assess(case, fields['report'])
                with storage.connect() as db:
                    require(db.execute('SELECT COUNT(*) FROM field_voice_drafts').fetchone()[0] == saved, 'extraction is transient')
                # Explicit synthetic reviewer supplies the known test date, never the model.
                fields['work_date'] = '2026-10-18'
                draft_id = str(uuid4())
                response = client.post('/api/field-voice/drafts', headers=headers,
                    json={**basis, 'request_id':draft_id, 'fields':fields})
                require(response.status_code == 200, 'save reviewed structured draft'); saved += 1
                path = '/api/field-voice/drafts/'+draft_id
                require(client.patch(path, headers=headers, json={'expected_version':99, 'fields':fields}).status_code == 409, 'version protection')
                if case == 'unknown-quantity':
                    fields['report']['production_quantities'] = [{'item_name':'Drums', 'quantity':None, 'unit':'each'}]
                    edited = client.patch(path, headers=headers, json={'expected_version':1, 'fields':fields})
                    require(edited.status_code == 200, 'unknown draft correction')
                    require(client.post(path+'/send-to-office', headers=headers,
                        json={'expected_version':2, 'reviewed':True}).status_code == 422, 'unknown cannot send')
                elif case == CASES[0]:
                    # Confirm units as the explicit reviewer; model suggestions are not final.
                    for quantity in fields['report']['production_quantities']:
                        quantity['unit'] = 'each'
                    edited = client.patch(path, headers=headers, json={'expected_version':1, 'fields':fields})
                    require(edited.status_code == 200, 'review edit')
                    require(client.post(path+'/send-to-office', headers=headers,
                        json={'expected_version':2, 'reviewed':False}).status_code == 422, 'review required')
                    body = {'expected_version':2, 'reviewed':True}
                    sent = client.post(path+'/send-to-office', headers=headers, json=body)
                    require(sent.status_code == 200 and len(sent.json()['submission_ids']) == 2, 'atomic daily and incident send')
                    require(client.post(path+'/send-to-office', headers=headers, json=body).json() == sent.json(), 'idempotent retry')
                    with storage.connect() as db:
                        require(db.execute('SELECT COUNT(*) FROM fixture_messages').fetchone()[0] == 1, 'one in-app admin notice')
                        snapshots = [json.loads(r['payload']) for r in db.execute('SELECT payload FROM form_submissions')]
                        require(len(snapshots) == 2 and all(s['field_voice_review']['reviewed_by'] == 'worker' for s in snapshots), 'review audit')
                checks.append({'case':case, 'status':'pass', 'quantities':fields['report']['production_quantities'],
                    'incidents':len(fields['report']['incidents']), 'seconds':round(time.monotonic()-started, 2)})
            with storage.connect() as db:
                require(db.execute('SELECT COUNT(*) FROM sms_outbox').fetchone()[0] == 0, 'zero SMS')
                for row in db.execute('SELECT payload FROM field_voice_drafts'):
                    require(set(json.loads(row['payload'])) == {'work_date', 'report'}, 'structured persistence only')
        require(len(speech_calls) == 10 and 8 <= len(model_calls) <= 10, 'paid request budget')
    result = {'status':'PASS', 'mode':mode, 'synthetic_only':True, 'identity':'Google metadata/ADC' if mode == 'live' else 'mocked',
        'speech_requests':len(speech_calls), 'model_requests':len(model_calls),
        'raw_audio_or_transcript_logged':False, 'sms_sent':0, 'checks':checks}
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio-root', type=Path, required=True)
    parser.add_argument('--mode', choices=('live','mocked'), default='live')
    args = parser.parse_args()
    try:
        run(args.audio_root, args.mode)
    except Exception as error:
        # No provider exception body, transcript, authorization header or audio.
        print(json.dumps({'status':'FAIL', 'check':str(error) if isinstance(error, RuntimeError) else type(error).__name__}), flush=True)
        raise SystemExit(1)
