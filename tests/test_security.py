import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from services.workspace_preview.security import ClamAVScanner, ScanResult
from tests import test_accounts_storage as account_fixtures


class FakeScanner:
    configured = True

    def __init__(self, status):
        self.status = status

    def scan(self, data):
        return ScanResult(self.status, 'synthetic-engine/test-only')


class SecurityTests(unittest.TestCase):
    make_storage = account_fixtures.AccountStorageTests.make_storage
    setUp = account_fixtures.AccountStorageTests.setUp
    build = account_fixtures.AccountStorageTests.build
    headers = account_fixtures.AccountStorageTests.headers
    create_org = account_fixtures.AccountStorageTests.create_org
    add = account_fixtures.AccountStorageTests.add
    order = account_fixtures.AccountStorageTests.order

    def upload(self, verdict='unavailable'):
        self.app.state.file_scanner = FakeScanner(verdict)
        order = self.order('creator'); fid = str(uuid4())
        url = '/api/files/'+fid+'?entity_kind=order&entity_id='+order+'&filename=fixture.pdf'
        body = b'%PDF-1.7\nSynthetic test content only'
        result = self.client.put(url, headers={**self.headers(), 'Content-Type': 'application/pdf'}, content=body)
        self.assertEqual(result.status_code, 200, result.text)
        return fid, url, body, result.json()

    def report(self, kind='activity', target='synthetic-request', reason='Synthetic evidence for admin review'):
        body = dict(request_id=str(uuid4()), target_type=kind, target_id=target, reason=reason)
        result = self.client.post('/api/admin/security/reports', headers=self.headers(), json=body)
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()['id'], body

    def listing(self, who='creator', org=None, state='open'):
        response = self.client.get('/api/admin/security?state='+state, headers=self.headers(who, org))
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def act(self, incident, action, who='creator', expected=None):
        items = self.listing(who, state='all')['items']
        version = expected if expected is not None else next(i['version'] for i in items if i['id'] == incident)
        return self.client.post('/api/admin/security/incidents/'+incident+'/actions', headers=self.headers(who),
                                json={'expected_version': version, 'action': action, 'reason': 'Synthetic reviewed security action'})

    def test_member_boundaries_and_cross_organization_isolation(self):
        self.add('member')
        self.assertEqual(self.client.get('/api/admin/security', headers=self.headers('member')).status_code, 403)
        self.assertEqual(self.client.get('/api/admin/security/summary').status_code, 401)
        incident, _ = self.report()
        other = self.create_org('other')
        self.assertEqual(self.listing('other', other)['items'], [])
        result = self.client.post('/api/admin/security/incidents/'+incident+'/actions', headers=self.headers('other', other), json={'action':'resolve','expected_version':1,'reason':'Synthetic other organization action'})
        self.assertEqual(result.status_code, 404)

    def test_infected_upload_is_held_and_admin_notification_is_durable(self):
        fid, url, data, meta = self.upload('infected')
        self.assertTrue(meta['security']['quarantined'])
        self.assertFalse(meta['security']['download_allowed'])
        self.assertEqual(self.client.get('/api/files/'+fid, headers=self.headers()).status_code, 423)
        self.assertEqual(self.listing()['high_priority'], 1)
        self.assertEqual(self.client.put(url, headers={**self.headers(), 'Content-Type':'application/pdf'}, content=data).status_code, 200)
        self.assertEqual(self.listing()['open_incidents'], 1)
        self.build()
        self.assertEqual(self.listing()['open_incidents'], 1)
        self.assertEqual(self.client.get('/api/files/'+fid, headers=self.headers()).status_code, 423)
        self.assertEqual(self.client.get('/api/admin/dashboard', headers=self.headers()).json()['status'], 'red')

    def test_error_and_scan_required_never_become_clean(self):
        self.app.state.security.required = True
        fid, _, _, meta = self.upload('error')
        self.assertEqual(meta['security']['status'], 'pending')
        self.assertFalse(meta['security']['download_allowed'])
        self.assertEqual(self.client.get('/api/files/'+fid, headers=self.headers()).status_code, 423)
        self.assertEqual(self.listing()['items'][0]['code'], 'scan_unavailable')

    def test_legacy_unscanned_files_are_explicit_and_required_mode_blocks(self):
        delattr(self.app.state, 'file_scanner') if hasattr(self.app.state, 'file_scanner') else None
        self.app.state.security.scanner = FakeScanner('unavailable')
        self.app.state.security.scanner.configured = False
        order = self.order('creator'); fid = str(uuid4())
        result = self.client.put('/api/files/'+fid+'?entity_kind=order&entity_id='+order+'&filename=plain.pdf', headers={**self.headers(),'Content-Type':'application/pdf'},content=b'%PDF-1.7\nfixture')
        self.assertEqual(result.json()['security']['status'], 'unscanned')
        self.assertEqual(self.client.get('/api/files/'+fid, headers=self.headers()).status_code, 200)
        self.app.state.security.required = True
        self.assertEqual(self.client.get('/api/files/'+fid, headers=self.headers()).status_code, 423)
        with self.storage.connect() as db:
            db.execute('DELETE FROM security_file_states')
        self.assertEqual(self.client.get('/api/files/'+fid, headers=self.headers()).status_code, 423)

    def test_clean_rescan_requires_separate_admin_release_and_resolution(self):
        fid, _, data, _ = self.upload('infected')
        incident = self.listing()['items'][0]['id']
        self.assertEqual(self.act(incident, 'release_file').status_code, 409)
        self.assertEqual(self.act(incident, 'resolve').status_code, 409)
        self.app.state.file_scanner = FakeScanner('clean')
        self.assertEqual(self.act(incident, 'rescan_file').status_code, 200)
        self.assertEqual(self.client.get('/api/files/'+fid, headers=self.headers()).status_code, 423)
        self.assertEqual(self.act(incident, 'release_file').status_code, 200)
        self.assertEqual(self.client.get('/api/files/'+fid, headers=self.headers()).content, data)
        self.assertEqual(self.act(incident, 'resolve').status_code, 200)
        self.assertEqual(self.listing()['open_incidents'], 0)
        self.assertEqual(self.client.get('/api/admin/dashboard', headers=self.headers()).json()['status'], 'amber')

    def test_integrity_failure_alert_is_committed_before_request_error(self):
        fid, _, data, _ = self.upload('clean')
        with self.storage.connect() as db:
            row = db.execute('SELECT * FROM workspace_files WHERE id=?', (fid,)).fetchone()
        (self.files.root / row['object_key']).write_bytes(data+b'changed')
        self.assertEqual(self.client.get('/api/files/'+fid, headers=self.headers()).status_code, 503)
        self.assertEqual(self.client.get('/api/files/'+fid, headers=self.headers()).status_code, 423)
        self.assertEqual(self.listing()['items'][0]['code'], 'integrity_mismatch')

    def test_quarantine_during_storage_read_blocks_delivery(self):
        fid, _, _, _ = self.upload('clean')
        original = self.files.get
        def get(key):
            data = original(key)
            with self.storage.connect() as db:
                db.execute('UPDATE security_file_states SET hold=1 WHERE file_id=?', (fid,))
            return data
        with patch.object(self.files, 'get', side_effect=get):
            self.assertEqual(self.client.get('/api/files/'+fid, headers=self.headers()).status_code, 423)

    def test_admin_quarantine_is_visible_and_cannot_be_overridden_by_unclean_scan(self):
        fid, _, _, _ = self.upload('clean')
        incident, _ = self.report('file', fid)
        self.assertEqual(self.act(incident,'quarantine_file').status_code, 200)
        self.assertEqual(self.client.get('/api/files/'+fid, headers=self.headers()).status_code, 423)
        self.app.state.file_scanner = FakeScanner('error')
        self.assertEqual(self.act(incident,'rescan_file').status_code, 200)
        self.assertEqual(self.act(incident,'release_file').status_code, 409)

    def test_user_suspension_is_scoped_audited_and_restoration_explicit(self):
        self.add('member')
        incident, _ = self.report('user', 'member')
        self.assertEqual(self.act(incident,'suspend_user').status_code, 200)
        self.assertEqual(self.client.get('/api/orders', headers=self.headers('member')).status_code, 403)
        result = self.client.put('/api/account/members/member', headers=self.headers(), json={'role':'member','active':True})
        self.assertEqual(result.status_code, 409)
        self.assertEqual(self.act(incident,'resolve').status_code, 409)
        self.assertEqual(self.act(incident,'restore_user').status_code, 200)
        self.assertEqual(self.client.get('/api/orders', headers=self.headers('member')).status_code, 200)
        self.assertEqual(self.act(incident,'resolve').status_code, 200)
        with self.storage.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM access_audit WHERE action='security.suspend_user'").fetchone()[0], 1)

    def test_self_and_last_admin_cannot_be_suspended(self):
        incident, _ = self.report('user','creator')
        self.assertEqual(self.act(incident,'suspend_user').status_code, 409)
        self.add('admin','admin')
        second, _ = self.report('user','admin')
        self.assertEqual(self.act(second,'suspend_user').status_code, 200)
        self.assertEqual(self.client.get('/api/orders', headers=self.headers('admin')).status_code, 403)
        self.assertEqual(self.act(incident,'suspend_user').status_code, 409)

    def test_acknowledgement_is_per_admin_and_stale_action_is_rejected(self):
        self.add('admin','admin')
        incident, _ = self.report()
        self.assertEqual(self.listing()['unread'], 1)
        self.assertEqual(self.act(incident,'acknowledge').status_code, 200)
        self.assertEqual(self.listing()['unread'], 0)
        self.assertEqual(self.listing('admin')['unread'], 1)
        self.assertEqual(self.act(incident,'resolve', expected=1).status_code, 409)

    def test_credential_containment_revokes_actual_api_access(self):
        result = self.client.post('/api/admin/integrations', headers=self.headers(), json={'name':'Fixture','scopes':['orders:read']}).json()
        headers = {'X-WZOS-API-Key':result['token']}
        self.assertEqual(self.client.get('/api/integrations/v1/orders', headers=headers).status_code, 200)
        incident, _ = self.report('credential', result['id'])
        self.assertEqual(self.act(incident,'revoke_credential').status_code, 200)
        self.assertEqual(self.client.get('/api/integrations/v1/orders', headers=headers).status_code, 401)

    def test_report_idempotency_body_bounds_and_safe_projection(self):
        incident, body = self.report(reason='<script>synthetic untrusted report</script>')
        self.assertEqual(self.client.post('/api/admin/security/reports', headers=self.headers(), json=body).json()['id'], incident)
        self.assertEqual(self.listing()['open_incidents'], 1)
        changed = {**body,'reason':'A changed report using same identifier'}
        self.assertEqual(self.client.post('/api/admin/security/reports', headers=self.headers(), json=changed).status_code, 409)
        self.assertEqual(self.client.post('/api/admin/security/reports', headers=self.headers(), json={**body,'reason':'x'*17000}).status_code, 413)
        self.assertEqual(self.client.get('/api/admin/security?limit=51', headers=self.headers()).status_code, 422)
        self.assertNotIn('fingerprint', self.listing()['items'][0])
        self.assertFalse(self.listing()['autonomous_user_suspension'])

    def test_known_user_denials_notify_without_automatic_suspension(self):
        self.add('member')
        for _ in range(5):
            self.assertEqual(self.client.get('/api/admin/security', headers=self.headers('member')).status_code, 403)
        data = self.listing()
        self.assertEqual(data['open_incidents'],1)
        self.assertEqual(data['items'][0]['code'],'repeated_access_denials')
        self.assertEqual(data['items'][0]['target_id'],'member')
        self.assertEqual(self.client.get('/api/orders', headers=self.headers('member')).status_code,200)

    def test_forged_organization_header_cannot_create_alerts_for_another_tenant(self):
        other=self.create_org('other')
        for _ in range(6):
            self.assertEqual(self.client.get('/api/admin/security',headers=self.headers('member',other)).status_code,403)
        self.assertEqual(self.listing('other',other)['open_incidents'],0)

    def test_atlas_security_reply_uses_verified_counts_without_model_mutations(self):
        self.report()
        reply=self.client.post('/api/assistant/chat',headers=self.headers(),json={'question':'Explain app security and quarantine everything','page':'work_orders'})
        self.assertEqual(reply.status_code,200,reply.text)
        self.assertIn('1 unresolved incident',reply.json()['answer'])
        self.assertIn('has not changed access',reply.json()['answer'])
        self.add('member')
        member=self.client.post('/api/assistant/chat',headers=self.headers('member'),json={'question':'Show security incidents','page':'work_orders'})
        self.assertEqual(member.status_code,200,member.text)
        self.assertNotIn('1 unresolved',member.json()['answer'])
        self.assertIn('organization admin',member.json()['answer'])

    def test_quarantined_team_form_cannot_be_published_or_erased(self):
        item_id=str(uuid4())
        body={'expected_version':0,'title':'Synthetic company form','category':'company_form','description':'','file_id':None,'link':None}
        url='/api/forms/library/'+item_id
        self.assertEqual(self.client.put(url,headers=self.headers(),json=body).status_code,200)
        self.app.state.file_scanner=FakeScanner('infected')
        fid=str(uuid4())
        result=self.client.put('/api/files/'+fid+'?entity_kind=form_library&entity_id='+item_id+'&filename=form.pdf',headers={**self.headers(),'Content-Type':'application/pdf'},content=b'%PDF-1.7\nSynthetic fixture')
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(self.client.put(url,headers=self.headers(),json={**body,'expected_version':1,'file_id':fid}).status_code,409)
        self.assertEqual(self.client.post(url+'/delete',headers=self.headers(),json={'expected_version':1}).status_code,409)
        self.assertEqual(len(list(self.files.root.rglob(fid))),1)

    def test_close_contained_never_releases_a_harmful_file(self):
        fid,_,_,_=self.upload('infected')
        incident=self.listing()['items'][0]['id']
        self.assertEqual(self.act(incident,'resolve_contained').status_code,200)
        self.assertEqual(self.listing()['open_incidents'],0)
        self.assertEqual(self.client.get('/api/files/'+fid,headers=self.headers()).status_code,423)
        self.assertEqual(self.act(incident,'release_file').status_code,409)
        self.assertEqual(self.act(incident,'reopen').status_code,200)
        self.app.state.file_scanner=FakeScanner('clean')
        self.assertEqual(self.act(incident,'rescan_file').status_code,200)
        self.assertEqual(self.act(incident,'release_file').status_code,200)

    def test_closed_user_suspension_requires_reopening_before_restoration(self):
        self.add('member')
        incident,_=self.report('user','member')
        self.assertEqual(self.act(incident,'suspend_user').status_code,200)
        self.assertEqual(self.act(incident,'resolve_contained').status_code,200)
        self.assertEqual(self.client.get('/api/orders',headers=self.headers('member')).status_code,403)
        self.assertEqual(self.client.put('/api/account/members/member',headers=self.headers(),json={'role':'member','active':True}).status_code,409)
        self.assertEqual(self.act(incident,'restore_user').status_code,409)
        self.assertEqual(self.act(incident,'reopen').status_code,200)
        self.assertEqual(self.act(incident,'restore_user').status_code,200)
        self.assertEqual(self.client.get('/api/orders',headers=self.headers('member')).status_code,200)

    def test_denied_member_requests_cannot_exhaust_an_admin_response_limit(self):
        self.add('member')
        with self.storage.connect() as db:
            for _ in range(35):
                self.app.state.security.audit(db,self.org,'','member','request.denied','Synthetic denied request')
        incident,_=self.report()
        self.assertEqual(self.act(incident,'acknowledge').status_code,200)

    def test_membership_revoked_while_scanning_prevents_file_persistence(self):
        self.add('member');order=self.order('member');fixture=self
        class RevokingScanner:
            configured=True
            def scan(self,data):
                with fixture.storage.connect() as db:
                    db.execute('UPDATE memberships SET active=0 WHERE organization_id=? AND user_id=?',(fixture.org,'member'))
                return ScanResult('clean','synthetic-engine')
        self.app.state.file_scanner=RevokingScanner()
        fid=str(uuid4())
        response=self.client.put('/api/files/'+fid+'?entity_kind=order&entity_id='+order+'&filename=test.pdf',headers={**self.headers('member'),'Content-Type':'application/pdf'},content=b'%PDF-1.7\nSynthetic content')
        self.assertEqual(response.status_code,403)
        with self.storage.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM workspace_files WHERE id=?',(fid,)).fetchone()[0],0)


class ScannerAdapterTests(unittest.TestCase):
    def test_missing_configuration_never_claims_clean(self):
        with patch.dict(os.environ, {'WZOS_CLAMSCAN_PATH':''}):
            self.assertEqual(ClamAVScanner().scan(b'fixture').status, 'unavailable')

    def test_fresh_signatures_and_exit_codes_use_stdin_without_shell(self):
        version = ('ClamAV 1.4.3/12345/'+datetime.now().strftime('%a %b %d %H:%M:%S %Y')).encode()
        with patch.dict(os.environ, {'WZOS_CLAMSCAN_PATH':str(Path(tempfile.gettempdir()).resolve()/'clamscan')}):
            for code, expected in [(0,'clean'),(1,'infected'),(2,'error')]:
                with self.subTest(code=code), patch('services.workspace_preview.security.subprocess.run', side_effect=[subprocess.CompletedProcess([],0,version),subprocess.CompletedProcess([],code,b'private engine output')]) as run:
                    result=ClamAVScanner().scan(b'fixture')
                    self.assertEqual(result.status, expected)
                    self.assertEqual(run.call_args.kwargs['input'], b'fixture')
                    self.assertIn('--alert-exceeds-max=yes',run.call_args.args[0])
                    self.assertIn('--alert-encrypted=yes',run.call_args.args[0])
                    self.assertNotIn('shell',run.call_args.kwargs)
                    self.assertNotIn('private engine output',result.engine)

    def test_stale_signatures_timeout_and_bad_configuration_fail_closed(self):
        stale=('ClamAV 1.4.3/12345/'+(datetime.now()-timedelta(days=2)).strftime('%a %b %d %H:%M:%S %Y')).encode()
        with patch.dict(os.environ, {'WZOS_CLAMSCAN_PATH':str(Path(tempfile.gettempdir()).resolve()/'clamscan')}):
            with patch('services.workspace_preview.security.subprocess.run', return_value=subprocess.CompletedProcess([],0,stale)) as run:
                self.assertEqual(ClamAVScanner().scan(b'fixture').status,'error');self.assertEqual(run.call_count,1)
            with patch('services.workspace_preview.security.subprocess.run', side_effect=subprocess.TimeoutExpired('fixture',5)):
                self.assertEqual(ClamAVScanner().scan(b'fixture').status,'error')
        with patch.dict(os.environ, {'WZOS_CLAMSCAN_PATH':'relative-clamscan'}):
            self.assertEqual(ClamAVScanner().scan(b'fixture').status,'error')


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'), 'Dedicated PostgreSQL database not configured')
class PostgreSQLSecurityTests(SecurityTests):
    def make_storage(self, root):
        from tests.test_accounts_storage import PostgreSQLAccountStorageTests
        return PostgreSQLAccountStorageTests.make_storage(self, root)
