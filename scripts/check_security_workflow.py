"""Disposable in-process app workflow; never serves fixture identities on HTTP.

Mocked mode validates the harness only. Live mode requires the dedicated Cloud Run
job and uses the real app RemoteScanner/Google metadata identity path. Persistence
is temporary SQLite/local files, not acceptance of Cloud SQL or Google Storage.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if Path('/app/services').is_dir():
    sys.path.insert(0, '/app')

SCANNER = 'https://wzos-v2-scanner-udtvm4rgca-uc.a.run.app'
JOB = 'wzos-security-workflow'
EICAR = (b'X5O!P%@AP[4' + b'\\PZX54(P^)7CC)7}' +
         b'$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*')
DOCUMENT_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'


def detection_document():
    """Keep the standard 68-byte fixture intact in a supported ZIP container."""
    document = io.BytesIO()
    with zipfile.ZipFile(document, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml',
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        archive.writestr('word/document.xml',
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')
        archive.writestr('synthetic-antivirus-test.txt', EICAR)
    return document.getvalue()


class WorkflowFailure(RuntimeError):
    """Only fixed, non-sensitive check names may be logged."""


def require(condition, name):
    if not condition:
        raise WorkflowFailure(name)


def run(mode):
    require(not any(os.getenv(k) for k in ('K_SERVICE', 'GAE_ENV', 'NETLIFY')),
            'Refuse a serving application environment')
    require(mode != 'live' or os.getenv('CLOUD_RUN_JOB') == JOB,
            'Live mode requires the reviewed dedicated job')
    require(mode == 'live' or not os.getenv('CLOUD_RUN_JOB'),
            'Only live mode may be used for cloud-job acceptance')
    require(not any(os.getenv(k) for k in ('WZOS_DATABASE_URL', 'WZOS_FILES_BUCKET')),
            'Refuse live persistence configuration')
    import httpx
    from fastapi.testclient import TestClient
    from services.workspace_preview.app import create_app
    from services.workspace_preview.files import LocalFiles
    from services.workspace_preview.intelligence import LocalIntelligence
    from services.workspace_preview.scanner_transport import RemoteScanner
    from services.workspace_preview.storage import SQLiteStorage
    from services.v2.knowledge.store import Store

    checks = []
    def check(condition, name):
        require(condition, name)
        checks.append(name)

    def verdict(request):
        data = request.content
        # Model only this fixture, not arbitrary substring-based detection.
        detected = False
        if data.startswith(b'PK\x03\x04'):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                detected = archive.read('synthetic-antivirus-test.txt') == EICAR
        return httpx.Response(200, headers={'content-type': 'application/json'},
            stream=httpx.ByteStream(json.dumps({'version': 1,
                'request_id': request.headers['x-scan-request'],
                'sha256': hashlib.sha256(data).hexdigest(), 'byte_count': len(data),
                'status': 'infected' if detected else 'clean',
                'engine': 'ClamAV 1.5.4/28154'}).encode()))

    scanner = RemoteScanner() if mode == 'live' else RemoteScanner(
        token_provider=lambda _: 'synthetic.google.token', transport=httpx.MockTransport(verdict))
    if mode == 'engine':
        from services.workspace_preview.clamd_scanner import ClamdScanner
        scanner = ClamdScanner()
        require(scanner.configured, 'Explicit local engine configuration required')
    outage = RemoteScanner(token_provider=lambda _: 'synthetic.outage.token',
        transport=httpx.MockTransport(lambda _: httpx.Response(503)))
    with tempfile.TemporaryDirectory(prefix='wzos-security-workflow-') as directory:
        root = Path(directory)
        storage, files = SQLiteStorage(root/'test.sqlite'), LocalFiles(root/'files')
        claims = {name: {'uid': name, 'email': name+'@example.test', 'email_verified': True}
                  for name in ('admin', 'member', 'other', 'core')}
        client = None
        def build():
            nonlocal client, app
            if client:
                client.close()
            app = create_app(root/'unused.sqlite', Store(root/'sources', {}),
                intelligence=LocalIntelligence(), account_workspace=True, storage=storage,
                verifier=lambda token: claims[token], file_store=files)
            app.state.file_scanner = scanner
            client = TestClient(app)

        def headers(who='admin', organization=None):
            return {'Authorization': 'Bearer '+who, 'X-WZOS-Organization': organization or org}

        def organization(who, edition):
            code = app.state.accounts.issue_activation(edition)
            response = client.post('/api/account/organizations', headers=headers(who, ''),
                json={'name': 'Synthetic workflow '+who, 'activation_code': code})
            require(response.status_code == 200, 'organization_setup')
            return response.json()['id']

        def incidents():
            response = client.get('/api/admin/security?state=all', headers=headers())
            require(response.status_code == 200, 'incident_listing')
            return response.json()['items']

        def act(identifier, action, expected=None):
            version = next(i['version'] for i in incidents() if i['id'] == identifier)
            return client.post('/api/admin/security/incidents/'+identifier+'/actions',
                headers=headers(), json={'expected_version': version if expected is None else expected,
                    'action': action, 'reason': 'Synthetic reviewed workflow action'})

        def upload(data):
            identifier = str(uuid4())
            response = client.put('/api/files/'+identifier+
                '?entity_kind=order&entity_id='+order+'&filename=synthetic.pdf',
                headers={**headers('member'), 'Content-Type': 'application/pdf'}, content=data)
            require(response.status_code == 200, 'file_upload')
            return identifier, response.json()

        app, org = None, ''
        try:
            build()
            org = organization('admin', 'enterprise')
            other = organization('other', 'enterprise')
            core = organization('core', 'core')
            check(len({org, other, core}) == 3, 'edition_organizations_separate')
            invitation = client.post('/api/account/invitations', headers=headers(),
                json={'email': 'member@example.test', 'role': 'member'})
            require(invitation.status_code == 200, 'invitation_setup')
            check(client.post('/api/account/join', headers=headers('member'),
                json={'token': invitation.json()['token']}).status_code == 200, 'member_join')
            response = client.post('/api/orders', headers=headers('member'), json={
                'request_id': str(uuid4()), 'title': 'Synthetic security workflow',
                'work_type': 'line_striping', 'address': 'Synthetic road', 'locality': 'Norfolk'})
            require(response.status_code == 201, 'order_setup')
            order = response.json()['id']
            check(client.get('/api/admin/security').status_code == 401, 'anonymous_rejected')
            check(client.get('/api/admin/security', headers=headers('member')).status_code == 403,
                  'member_admin_access_rejected')
            clean = b'%PDF-1.7\nSynthetic clean workflow only\n%%EOF\n'
            fid, meta = upload(clean)
            check(meta['security']['status'] == 'clean', 'mock_clean_upload' if mode == 'mocked' else 'real_clean_upload')
            check(client.get('/api/files/'+fid, headers=headers('member')).content == clean,
                  'member_clean_download')
            report = client.post('/api/admin/security/reports', headers=headers(), json={
                'request_id': str(uuid4()), 'target_type': 'file', 'target_id': fid,
                'reason': 'Synthetic quarantine and recovery exercise'})
            require(report.status_code == 200, 'admin_report')
            incident = report.json()['id']
            check(act(incident, 'quarantine_file').status_code == 200, 'admin_quarantine')
            check(client.get('/api/files/'+fid, headers=headers('member')).status_code == 423,
                  'held_member_download_rejected')
            check(client.get('/api/files/'+fid, headers=headers('other', other)).status_code == 404,
                  'cross_organization_file_rejected')
            check(client.post('/api/admin/security/incidents/'+incident+'/actions',
                headers=headers('other', other), json={'action': 'resolve', 'expected_version': 1,
                    'reason': 'Synthetic tenant boundary check'}).status_code == 404,
                'cross_organization_action_rejected')
            app.state.file_scanner = outage
            check(act(incident, 'rescan_file').status_code == 200, 'injected_outage_recorded')
            check(act(incident, 'release_file').status_code == 409, 'outage_release_rejected')
            build()
            check(client.get('/api/files/'+fid, headers=headers('member')).status_code == 423,
                  'hold_survives_application_recreation')
            summary = client.get('/api/admin/security/summary', headers=headers()).json()
            check(summary['unread'] > 0 and summary['open_incidents'] > 0, 'durable_admin_notification')
            check(client.get('/api/admin/dashboard', headers=headers()).json()['status'] == 'red',
                  'admin_dashboard_red')
            check(act(incident, 'rescan_file').status_code == 200, 'mock_clean_rescan' if mode == 'mocked' else 'real_clean_rescan')
            check(client.get('/api/files/'+fid, headers=headers('member')).status_code == 423,
                  'clean_rescan_does_not_release_quarantine')
            check(act(incident, 'release_file', expected=1).status_code == 409, 'stale_action_rejected')
            check(act(incident, 'release_file').status_code == 200, 'explicit_admin_release')
            check(client.get('/api/files/'+fid, headers=headers('member')).content == clean,
                  'released_bytes_match_original')
            check(act(incident, 'resolve').status_code == 200, 'incident_resolved')
            with storage.connect() as db:
                actions = {r['action'] for r in db.execute(
                    'SELECT action FROM security_actions WHERE incident_id=?', (incident,)).fetchall()}
            check({'quarantine_file', 'rescan_file', 'release_file', 'resolve'} <= actions,
                  'recovery_action_audit')
            library = str(uuid4())
            body = {'expected_version': 0, 'title': 'Synthetic security test document',
                    'category': 'company_form', 'description': 'Synthetic antivirus fixture only'}
            require(client.put('/api/forms/library/'+library, headers=headers(), json=body).status_code == 200,
                    'detection_library_setup')
            infected = str(uuid4())
            response = client.put('/api/files/'+infected+
                '?entity_kind=form_library&entity_id='+library+'&filename=synthetic.docx',
                headers={**headers(), 'Content-Type': DOCUMENT_TYPE}, content=detection_document())
            require(response.status_code == 200, 'detection_document_upload')
            meta = response.json()
            status = meta.get('security', {}).get('status')
            # Allowlisted diagnostics only: never bytes, credentials or provider bodies.
            require(status == 'infected', 'eicar_upload_detected_status_' +
                    (status if status in ('clean', 'infected', 'error', 'unavailable', 'pending') else 'unknown'))
            check(True, 'mock_eicar_upload_detected' if mode == 'mocked' else 'real_eicar_upload_detected')
            check(client.get('/api/files/'+infected, headers=headers()).status_code == 423,
                  'detected_file_download_rejected')
            check(client.put('/api/forms/library/'+library, headers=headers(),
                json={**body, 'expected_version': 1, 'file_id': infected}).status_code == 409,
                'detected_file_publication_rejected')
            check(client.get('/api/files/'+infected, headers=headers('member')).status_code == 404,
                  'member_cannot_access_unpublished_detection_fixture')
            check(client.get('/api/files/'+infected, headers=headers('other', other)).status_code == 404,
                  'other_organization_cannot_access_detection_fixture')
            malware = next(i for i in incidents() if i['target_id'] == infected)
            check(act(malware['id'], 'release_file').status_code == 409, 'infected_release_rejected')
            check(client.get('/api/admin/security', headers=headers('other', other)).json()['items'] == [],
                  'other_organization_no_incident_leak')
        finally:
            if client:
                client.close()
    return {'mode': mode, 'passed': len(checks), 'checks': checks,
            'persistence': 'temporary SQLite and local files',
            'identity': 'Google metadata' if mode == 'live' else ('local engine; injected app identities' if mode == 'engine' else 'mocked'),
            'notifications': 'durable in-app only; no external sends',
            'injected_failure': 'scanner HTTP503; explicitly synthetic'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('mocked', 'engine', 'live'), required=True)
    args = parser.parse_args()
    environment = {'WZOS_ACCOUNT_WORKSPACE': '1', 'WZOS_ACCOUNT_AUTH_HEADER': 'Authorization',
        'WZOS_FILE_SCAN_REQUIRED': '1', 'WZOS_SCANNER_URL': SCANNER,
        'WZOS_SMS_MODE': 'disabled', 'WZOS_DAILY_ENABLED': '0', 'WZOS_ATLAS_VLLM_ENABLED': '0'}
    try:
        with patch.dict(os.environ, environment):
            result = run(args.mode)
        print('SECURITY_WORKFLOW_PASS', json.dumps(result, sort_keys=True))
        return 0
    except WorkflowFailure as error:
        print('SECURITY_WORKFLOW_FAILED', str(error))
        return 1
    except Exception as error:
        # No traceback, token, file bytes, claims or provider response in logs.
        print('SECURITY_WORKFLOW_FAILED', type(error).__name__)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
