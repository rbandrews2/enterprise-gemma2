"""Disposable in-process app harness; no listener or customer persistence.

Mocked mode checks orchestration only. Live mode is restricted to the reviewed
Cloud Run job and uses Google metadata plus the production VLLM adapter. Source
passages are explicitly synthetic: success cannot establish agency applicability.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
JOB = 'wzos-atlas-app-workflow'


def require(value, name):
    if not value:
        raise RuntimeError(name)


def run(mode):
    require(not any(os.getenv(k) for k in ('K_SERVICE', 'GAE_ENV', 'NETLIFY',
                'WZOS_DATABASE_URL', 'WZOS_FILES_BUCKET', 'FIREBASE_AUTH_EMULATOR_HOST')),
            'Refuse hosted service or external persistence configuration')
    require((mode == 'live' and os.getenv('CLOUD_RUN_JOB') == JOB)
            or (mode == 'mocked' and not os.getenv('CLOUD_RUN_JOB')),
            'Use the dedicated job for live mode; local only for mocked mode')
    import httpx
    from fastapi.testclient import TestClient
    from services.workspace_preview.app import create_app
    from services.workspace_preview.cloud_intelligence import metadata_identity_token
    from services.workspace_preview.files import LocalFiles
    from services.workspace_preview.storage import SQLiteStorage
    from services.workspace_preview.vllm_intelligence import VLLMIntelligence
    from services.v2.knowledge.models import Source
    from services.v2.knowledge.store import Store

    calls, identities, contexts, results = [], [], [], []

    async def identity(audience):
        identities.append(audience)
        if mode == 'mocked':
            return 'synthetic.google.token'
        # The production helper requires K_SERVICE. Scope that environment marker
        # only to its metadata request; app initialization remains job-only.
        with patch.dict(os.environ, {'K_SERVICE': JOB}):
            return await metadata_identity_token(audience)

    def inference(request):
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {
            'content': 'Synthetic unreviewed references only. Ask an admin; Atlas performs no actions.'}}],
            'usage': {'prompt_tokens': 1, 'completion_tokens': 1}})

    class Engine(VLLMIntelligence):
        async def reply(self, payload, context):
            require(len(calls) < 2, 'Model request budget exhausted')
            calls.append(payload.page)
            contexts.append(context)
            return await super().reply(payload, context)

    settings = {'WZOS_ACCOUNT_WORKSPACE': '1', 'WZOS_ATLAS_VLLM_ENABLED': '1'}
    if mode == 'mocked':
        settings['WZOS_ATLAS_VLLM_URL'] = 'https://synthetic-atlas.run.app'
    with patch.dict(os.environ, settings), tempfile.TemporaryDirectory(prefix='wzos-atlas-app-') as directory:
        root = Path(directory)
        item = Source(id='synthetic-atlas-reference', agency='VDOT',
            title='SYNTHETIC pipeline fixture, not an official publication',
            url='https://www.vdot.virginia.gov/test',
            publication_page='https://www.vdot.virginia.gov/test', kind='html', jurisdiction='VA',
            links_verified_on='2026-10-18', applicability_note='Synthetic test only; no field applicability.')
        store = Store(root/'sources', {item.id: item})
        data = b'<html><body><main><h1 id="safety">Synthetic flagger safety reference</h1><p>Fixture only: verify governing authority, site measurements and qualified review. Never invent flagger coordinates.</p></main></body></html>'
        with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(
                200, content=data, headers={'content-type': 'text/html'}))) as transport:
            ingestion = store.ingest(item.id, transport)
            require(ingestion.get('status') == 'extracted', 'Synthetic reference ingestion')
            revision = ingestion['revision']
        store.rebuild()
        engine = Engine(token_provider=identity,
                        transport=httpx.MockTransport(inference) if mode == 'mocked' else None)
        claims = {name: {'uid': name, 'email': name+'@example.test', 'email_verified': True}
                  for name in ('admin', 'member', 'other', 'core')}
        app = create_app(root/'unused.sqlite', store, intelligence=engine,
            account_workspace=True, storage=SQLiteStorage(root/'test.sqlite'),
            verifier=lambda token: claims[token], file_store=LocalFiles(root/'files'))
        with TestClient(app) as client:
            def headers(who, org=''):
                return {'Authorization': 'Bearer '+who, 'X-WZOS-Organization': org}

            def organization(who, edition):
                response = client.post('/api/account/organizations', headers=headers(who), json={
                    'name': 'Synthetic Atlas '+who,
                    'activation_code': app.state.accounts.issue_activation(edition)})
                require(response.status_code == 200, 'Organization setup')
                return response.json()['id']

            org = organization('admin', 'enterprise')
            other = organization('other', 'enterprise')
            core = organization('core', 'core')
            invitation = client.post('/api/account/invitations', headers=headers('admin', org),
                json={'email': 'member@example.test', 'role': 'member'})
            require(invitation.status_code == 200, 'Member invitation')
            require(client.post('/api/account/join', headers=headers('member'),
                json={'token': invitation.json()['token']}).status_code == 200, 'Member join')
            job = client.post('/api/orders', headers=headers('member', org), json={
                'request_id': str(uuid4()), 'title': 'Synthetic Atlas reference review',
                'work_type': 'underground_utility', 'address': 'Synthetic site, not a real address',
                'locality': 'Norfolk'})
            require(job.status_code == 201, 'Saved job setup')
            saved = job.json()
            payload = {'page': 'report', 'order_id': saved['id'], 'expected_version': saved['version'],
                'question': 'Review synthetic flagger safety references for this saved job; identify missing site evidence and do not invent coordinates.'}
            for name, actor, organization_id, body, expected in [
                ('stale_version', 'member', org, {**payload, 'expected_version': 99}, 409),
                ('cross_tenant', 'other', other, payload, 404),
                ('core_report', 'core', core, payload, 403),
            ]:
                response = client.post('/api/assistant/chat', headers=headers(actor, organization_id), json=body)
                require(response.status_code == expected, name)
                results.append({'check': name, 'status': response.status_code})
            require(not calls, 'Denied requests must not reach model')
            for body in (payload, {'page': 'messages', 'question': 'Explain notification delivery uncertainty and what actions I am permitted to take as a member.'}):
                before = time.monotonic()
                response = client.post('/api/assistant/chat', headers=headers('member', org), json=body)
                require(response.status_code == 200, 'App model response')
                reply = response.json()
                require(reply['model_called'] and reply['response_kind'] == 'model', 'Real model path')
                require(reply['actions_performed'] == [] and not reply['approved_for_field_use'], 'No autonomous actions or field approval')
                if body['page'] == 'report':
                    require(reply['order_version'] == saved['version'], 'Current saved job version')
                    require(reply['reference_basis']['candidate_count'] > 0, 'Retrieved candidate references')
                    require(not reply['reference_basis']['applicability_verified'], 'Unverified applicability retained')
                    require(any(c['revision'] == revision and c['review_status'] == 'unreviewed'
                                for c in reply['citations']), 'Revision and review provenance retained')
                    require(contexts[-1]['saved_job']['id'] == saved['id'], 'Saved job reaches adapter')
                    require(contexts[-1]['candidate_references'][0]['revision'] == revision, 'Passage reaches adapter')
                results.append({'check': body['page'], 'seconds': round(time.monotonic()-before, 3),
                    'answer': reply['answer'], 'synthetic': True, 'review_status': 'needs_human_review'})
            require(len(calls) == len(identities) == 2, 'Exactly two inference and identity requests')
            require(len(set(identities)) == 1 and identities[0] == engine.origin, 'Canonical audience matches target')
        return {'mode': mode, 'identity': 'Google metadata' if mode == 'live' else 'mocked',
                'model_requests': len(calls), 'synthetic_sources_only': True, 'checks': results}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('mocked', 'live'), required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.mode), indent=2))
