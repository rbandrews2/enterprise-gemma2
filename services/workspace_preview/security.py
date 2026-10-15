"""Evidence-driven Atlas Security. Models have no mutation or scanner authority."""
import hashlib
import json
import os
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from uuid import UUID, NAMESPACE_URL, uuid4, uuid5

from fastapi import HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

DDL = (
    'CREATE TABLE IF NOT EXISTS security_incidents (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,code TEXT NOT NULL,severity TEXT NOT NULL,target_type TEXT NOT NULL,target_id TEXT NOT NULL,fingerprint TEXT NOT NULL,status TEXT NOT NULL,containment TEXT NOT NULL,version INTEGER NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL)',
    'CREATE INDEX IF NOT EXISTS security_incidents_org_status ON security_incidents(organization_id,status,updated_at)',
    'CREATE TABLE IF NOT EXISTS security_actions (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,incident_id TEXT NOT NULL,actor_id TEXT NOT NULL,action TEXT NOT NULL,reason TEXT NOT NULL,occurred_at TEXT NOT NULL)',
    'CREATE INDEX IF NOT EXISTS security_actions_org_actor_time ON security_actions(organization_id,actor_id,occurred_at)',
    'CREATE INDEX IF NOT EXISTS security_actions_incident ON security_actions(organization_id,incident_id,occurred_at)',
    'CREATE TABLE IF NOT EXISTS security_file_states (organization_id TEXT NOT NULL,file_id TEXT NOT NULL,sha256 TEXT NOT NULL,status TEXT NOT NULL,hold INTEGER NOT NULL,scanner TEXT NOT NULL,scanned_at TEXT,PRIMARY KEY(organization_id,file_id))',
    'CREATE TABLE IF NOT EXISTS security_alert_reads (organization_id TEXT NOT NULL,user_id TEXT NOT NULL,incident_id TEXT NOT NULL,version INTEGER NOT NULL,PRIMARY KEY(organization_id,user_id,incident_id))',
)
TITLES = {
    'malware_detected': 'Scanner detected suspicious file content',
    'scan_unavailable': 'File scanning could not be completed',
    'integrity_mismatch': 'Stored file failed its integrity check',
    'admin_report': 'Administrator reported a security concern',
    'repeated_access_denials': 'Repeated denied requests need review',
}


def now():
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ScanResult:
    status: str
    engine: str = ''


class ClamAVScanner:
    """Optional operator-installed engine; never execute submitted file names."""
    slots = threading.BoundedSemaphore(1)

    def __init__(self):
        self.path = os.getenv('WZOS_CLAMSCAN_PATH', '').strip()
        self.configured = bool(self.path)

    def scan(self, data):
        if not self.configured:
            return ScanResult('unavailable')
        if not Path(self.path).is_absolute() or len(data) > 10 * 1024 * 1024:
            return ScanResult('error')
        if not self.slots.acquire(blocking=False):
            return ScanResult('error')
        try:
            from .archive_policy import zip_complete
            if not zip_complete(data):
                return ScanResult('error')
            version = subprocess.run([self.path, '--version'], capture_output=True, timeout=5, check=False)
            text = version.stdout.decode('ascii', errors='replace').strip()
            parts = text.split('/')
            if version.returncode or len(parts) != 3 or not parts[0].startswith('ClamAV '):
                return ScanResult('error')
            signature_date = datetime.strptime(parts[2], '%a %b %d %H:%M:%S %Y')
            age = datetime.now() - signature_date
            if not timedelta(0) <= age <= timedelta(hours=24):
                return ScanResult('error')
            result = subprocess.run([self.path, '--no-summary', '--stdout', '--alert-exceeds-max=yes',
                                     '--alert-encrypted=yes', '--alert-macros=yes', '--max-scantime=15000',
                                     '--max-filesize=10M', '--max-scansize=50M', '--max-files=1000',
                                     '--max-recursion=10', '-'], input=data,
                                    capture_output=True, timeout=20, check=False)
            engine = '/'.join(parts[:2])[:100]
            return ScanResult({0: 'clean', 1: 'infected'}.get(result.returncode, 'error'), engine)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return ScanResult('error')
        finally:
            self.slots.release()


class Report(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    request_id: UUID
    target_type: Literal['file', 'user', 'activity', 'credential']
    target_id: str = Field(min_length=1, max_length=128)
    reason: str = Field(min_length=8, max_length=500)


class Action(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    expected_version: int = Field(ge=1, strict=True)
    action: Literal['acknowledge', 'resolve', 'resolve_contained', 'reopen', 'quarantine_file', 'rescan_file', 'release_file',
                    'suspend_user', 'restore_user', 'revoke_credential']
    reason: str = Field(min_length=8, max_length=500)


def configured_scanner():
    if os.getenv('WZOS_SCANNER_URL', '').strip():
        from .scanner_transport import RemoteScanner
        return RemoteScanner()
    if os.getenv('WZOS_CLAMD_SOCKET', '').strip() or os.getenv('WZOS_CLAMD_CONFIG', '').strip():
        from .clamd_scanner import ClamdScanner
        return ClamdScanner()
    return ClamAVScanner()


class Security:
    def __init__(self, app, connect, actor, accounts=None, file_store=None):
        self.app, self.connect, self.actor = app, connect, actor
        self.accounts, self.file_store = accounts, file_store
        self.required = os.getenv('WZOS_FILE_SCAN_REQUIRED', '0') == '1'
        self.scanner = configured_scanner()
        with connect() as db:
            for statement in DDL:
                db.execute(statement)

    def scan(self, data):
        scanner = getattr(self.app.state, 'file_scanner', self.scanner)
        try:
            result = scanner.scan(data)
            if not isinstance(result, ScanResult) or result.status not in ('clean', 'infected', 'unavailable', 'error') or (result.status == 'clean' and not result.engine):
                return ScanResult('error')
            return result
        except Exception:
            return ScanResult('error')

    def admin(self, request, db=None):
        user = self.actor(request)
        if user['role'] != 'admin':
            raise HTTPException(403, 'Administrator access required')
        if self.accounts and db is not None:
            current = db.execute("SELECT m.role FROM memberships m JOIN organizations o ON o.id=m.organization_id WHERE m.organization_id=? AND m.user_id=? AND m.active=1 AND o.active=1", (user['organization_id'], user['id'])).fetchone()
            if not current or current['role'] != 'admin':
                raise HTTPException(403, 'Active administrator access required')
        return user

    def audit(self, db, org, incident_id, actor_id, action, reason):
        db.execute('INSERT INTO security_actions VALUES (?,?,?,?,?,?,?)',
                   (str(uuid4()), org, incident_id, actor_id, action, reason, now()))

    def limit(self, db, org, actor_id):
        since = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        if db.execute("SELECT COUNT(*) FROM security_actions WHERE organization_id=? AND actor_id=? AND action!='request.denied' AND occurred_at>?", (org, actor_id, since)).fetchone()[0] >= 30:
            raise HTTPException(429, 'Too many security changes. Retry in one minute.')

    def incident(self, db, org, code, target_type, target_id, fingerprint='', containment='none', actor_id='atlas-security', reason='Server evidence recorded', identifier=None):
        key = identifier or str(uuid5(NAMESPACE_URL, json.dumps([org, code, target_type, target_id, fingerprint])))
        previous = db.execute('SELECT * FROM security_incidents WHERE id=?', (key,)).fetchone()
        if not previous:
            stamp = now()
            severity = 'high' if code in ('malware_detected', 'integrity_mismatch') else 'medium'
            db.execute('INSERT INTO security_incidents VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                       (key, org, code, severity, target_type, target_id, fingerprint, 'open', containment, 1, stamp, stamp))
            self.audit(db, org, key, actor_id, 'incident.created', reason)
        elif previous['status'] == 'resolved':
            db.execute("UPDATE security_incidents SET status='open',containment=?,version=version+1,updated_at=? WHERE id=?", (containment, now(), key))
            self.audit(db, org, key, actor_id, 'incident.reopened', reason)
        # Incident rows themselves are durable organization-admin notifications.
        return key

    def record_denial(self, user, status):
        """Known active actors only. Never attribute an unverified header to a tenant."""
        org = user['organization_id']
        since = (datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            count = db.execute("SELECT COUNT(*) FROM security_actions WHERE organization_id=? AND actor_id=? AND action='request.denied' AND occurred_at>?", (org, user['id'], since)).fetchone()[0]
            if count < 5:
                self.audit(db, org, '', user['id'], 'request.denied', 'Authenticated application request denied: HTTP '+str(status))
                count += 1
            if count >= 5:
                self.incident(db, org, 'repeated_access_denials', 'user', user['id'],
                              datetime.now(timezone.utc).strftime('%Y-%m-%dT%H'),
                              reason='At least five authenticated HTTP 403/429 responses within one minute. This may be a workflow error; it is not proof of an attack.')

    def file_status(self, db, org, file_id):
        row = db.execute('SELECT * FROM security_file_states WHERE organization_id=? AND file_id=?', (org, str(file_id))).fetchone()
        status = row['status'] if row else ('pending' if self.required else 'unscanned')
        held = bool(row and row['hold'])
        allowed = not held and status not in ('pending', 'infected') and (not self.required or status == 'clean')
        return {'status': status, 'quarantined': held, 'download_allowed': allowed,
                'scanner': row['scanner'] if row else '', 'scanned_at': row['scanned_at'] if row else None}

    def record_scan(self, db, row, result, *, preserve_hold=True):
        org, fid = row['organization_id'], row['id']
        previous = db.execute('SELECT hold FROM security_file_states WHERE organization_id=? AND file_id=?', (org, fid)).fetchone()
        configured = bool(getattr(getattr(self.app.state, 'file_scanner', self.scanner), 'configured', True))
        status = result.status
        if status == 'unavailable':
            status = 'pending' if self.required or configured else 'unscanned'
        if status == 'error':
            status = 'pending'
        hold = int(bool(result.status == 'infected' or (preserve_hold and previous and previous['hold'])))
        scanned = now() if result.status in ('clean', 'infected') else None
        db.execute('INSERT INTO security_file_states VALUES (?,?,?,?,?,?,?) ON CONFLICT(organization_id,file_id) DO UPDATE SET sha256=excluded.sha256,status=excluded.status,hold=excluded.hold,scanner=excluded.scanner,scanned_at=excluded.scanned_at',
                   (org, fid, row['sha256'], status, hold, result.engine[:100], scanned))
        if result.status == 'infected' or status == 'pending':
            self.incident(db, org, 'malware_detected' if result.status == 'infected' else 'scan_unavailable',
                          'file', fid, row['sha256'], 'file_held')

    def integrity_failure(self, row):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT INTO security_file_states VALUES (?,?,?,?,?,?,?) ON CONFLICT(organization_id,file_id) DO UPDATE SET status=excluded.status,hold=1,scanned_at=NULL',
                       (row['organization_id'], row['id'], row['sha256'], 'pending', 1, '', None))
            self.incident(db, row['organization_id'], 'integrity_mismatch', 'file', row['id'], row['sha256'], 'file_held')

    def summary(self, user):
        with self.connect() as db:
            org = user['organization_id']
            count = db.execute("SELECT COUNT(*) FROM security_incidents WHERE organization_id=? AND status!='resolved'", (org,)).fetchone()[0]
            high = db.execute("SELECT COUNT(*) FROM security_incidents WHERE organization_id=? AND status!='resolved' AND severity='high'", (org,)).fetchone()[0]
            unread = db.execute("SELECT COUNT(*) FROM security_incidents i LEFT JOIN security_alert_reads r ON r.incident_id=i.id AND r.organization_id=i.organization_id AND r.user_id=? WHERE i.organization_id=? AND i.status!='resolved' AND (r.version IS NULL OR r.version<i.version)", (user['id'], org)).fetchone()[0]
        return {'open_incidents': count, 'high_priority': high, 'unread': unread,
                'file_scan_required': self.required, 'scanner_configured': self.scanner.configured,
                'coverage': 'File checks, repeated denied requests from known active users, and admin reports. Device and network threat monitoring are not connected.',
                'external_notifications_enabled': False, 'autonomous_user_suspension': False}

    @staticmethod
    def suspended(db, org, user_id):
        return bool(db.execute("SELECT id FROM security_incidents WHERE organization_id=? AND target_type='user' AND target_id=? AND containment='user_suspended'", (org, user_id)).fetchone())

    def register(self):
        app = self.app

        @app.get('/api/admin/security/summary')
        def summary(request: Request):
            return self.summary(self.admin(request))

        @app.get('/api/admin/security')
        def incidents(request: Request, offset: int = Query(0, ge=0, le=10000), limit: int = Query(25, ge=1, le=50), state: Literal['open', 'resolved', 'all'] = 'open'):
            user = self.admin(request)
            condition = " AND status='resolved'" if state == 'resolved' else " AND status!='resolved'" if state == 'open' else ''
            with self.connect() as db:
                rows = db.execute('SELECT * FROM security_incidents WHERE organization_id=?' + condition + ' ORDER BY updated_at DESC,id LIMIT ? OFFSET ?', (user['organization_id'], limit, offset)).fetchall()
                items = []
                for row in rows:
                    actions = db.execute('SELECT actor_id,action,reason,occurred_at FROM security_actions WHERE organization_id=? AND incident_id=? ORDER BY occurred_at DESC,id DESC LIMIT 20', (user['organization_id'], row['id'])).fetchall()
                    item = {k: row[k] for k in ('id', 'code', 'severity', 'target_type', 'target_id', 'status', 'containment', 'version', 'created_at', 'updated_at')}
                    item.update(title=TITLES[row['code']], actions=[dict(a) for a in actions])
                    if row['target_type'] == 'file':
                        item['file_security'] = self.file_status(db, user['organization_id'], row['target_id'])
                    items.append(item)
            return {**self.summary(user), 'items': items, 'limit': limit, 'offset': offset}

        @app.post('/api/admin/security/reports')
        def report(body: Report, request: Request):
            user = self.admin(request)
            with self.connect() as db:
                db.execute('BEGIN IMMEDIATE'); self.admin(request, db); self.limit(db, user['organization_id'], user['id'])
                org = user['organization_id']
                table, column = {'file': ('workspace_files', 'id'), 'user': ('memberships', 'user_id'), 'credential': ('integration_credentials', 'id')}.get(body.target_type, (None, None))
                if body.target_type == 'file' and self.file_store is None:
                    raise HTTPException(409, 'File storage is not configured')
                if body.target_type == 'user' and self.accounts is None:
                    raise HTTPException(409, 'User suspension requires account workspace')
                if table and not db.execute(f'SELECT {column} FROM {table} WHERE organization_id=? AND {column}=?', (org, body.target_id)).fetchone():
                    raise HTTPException(404, 'Security target not found')
                fingerprint = str(body.request_id)
                key = str(uuid5(NAMESPACE_URL, json.dumps([org, 'admin_report', fingerprint])))
                previous = db.execute('SELECT * FROM security_incidents WHERE id=?', (key,)).fetchone()
                if previous:
                    reason = db.execute("SELECT reason FROM security_actions WHERE incident_id=? AND action='incident.created'", (key,)).fetchone()
                    if not reason or reason['reason'] != body.reason or previous['target_type'] != body.target_type or previous['target_id'] != body.target_id:
                        raise HTTPException(409, 'Report retry changed; use a new request identifier')
                else:
                    self.incident(db, org, 'admin_report', body.target_type, body.target_id, fingerprint,
                                  actor_id=user['id'], reason=body.reason, identifier=key)
            return {'id': key}

        @app.post('/api/admin/security/incidents/{incident_id}/actions')
        def action(incident_id: UUID, body: Action, request: Request):
            user = self.admin(request); org = user['organization_id']; scan_result = None
            if body.action in ('rescan_file', 'release_file'):
                with self.connect() as db:
                    self.limit(db, org, user['id'])
                    original = db.execute('SELECT * FROM security_incidents WHERE id=? AND organization_id=?', (str(incident_id), org)).fetchone()
                    file_row = db.execute('SELECT * FROM workspace_files WHERE id=? AND organization_id=?', (original['target_id'], org)).fetchone() if original and original['target_type'] == 'file' and self.file_store else None
                if not file_row:
                    raise HTTPException(404, 'File incident not found')
                if original['version'] != body.expected_version or original['status'] == 'resolved':
                    raise HTTPException(409, 'Incident changed or is resolved. Refresh before acting.')
                try:
                    data = self.file_store.get(file_row['object_key'])
                except Exception:
                    raise HTTPException(503, 'Preserved file unavailable') from None
                if hashlib.sha256(data).hexdigest() != file_row['sha256']:
                    self.integrity_failure(file_row)
                    raise HTTPException(409, 'File integrity failed; quarantine retained')
                if body.action == 'rescan_file':
                    scan_result = self.scan(data)
            with self.connect() as db:
                db.execute('BEGIN IMMEDIATE'); self.admin(request, db); self.limit(db, org, user['id'])
                row = db.execute('SELECT * FROM security_incidents WHERE id=? AND organization_id=?', (str(incident_id), org)).fetchone()
                if not row:
                    raise HTTPException(404, 'Security incident not found')
                if row['version'] != body.expected_version or (row['status'] == 'resolved' and body.action != 'reopen'):
                    raise HTTPException(409, 'Incident changed or is resolved. Refresh before acting.')
                status, containment = row['status'], row['containment']
                if body.action in ('quarantine_file', 'rescan_file', 'release_file'):
                    file = db.execute('SELECT * FROM workspace_files WHERE id=? AND organization_id=?', (row['target_id'], org)).fetchone() if row['target_type'] == 'file' and self.file_store else None
                    if not file:
                        raise HTTPException(404, 'File not found')
                    if body.action == 'quarantine_file':
                        from .forms_hub import file_id_retired
                        if file_id_retired(db, org, file['id']):
                            raise HTTPException(409, 'This file was already queued for deletion; it cannot be quarantined')
                    if body.action == 'rescan_file':
                        self.record_scan(db, file, scan_result)
                    elif body.action == 'quarantine_file':
                        db.execute('INSERT INTO security_file_states VALUES (?,?,?,?,?,?,?) ON CONFLICT(organization_id,file_id) DO UPDATE SET hold=1', (org, file['id'], file['sha256'], 'unscanned', 1, '', None))
                    else:
                        review = db.execute('SELECT * FROM security_file_states WHERE organization_id=? AND file_id=?', (org, file['id'])).fetchone()
                        if not review or review['status'] != 'clean' or not review['scanner'] or review['sha256'] != file['sha256'] or not review['scanned_at'] or not datetime.now(timezone.utc)-timedelta(hours=24) <= datetime.fromisoformat(review['scanned_at']) <= datetime.now(timezone.utc):
                            raise HTTPException(409, 'A recent clean scan of this exact file is required')
                        db.execute('UPDATE security_file_states SET hold=0 WHERE organization_id=? AND file_id=?', (org, file['id']))
                    containment = 'file_held' if not self.file_status(db, org, file['id'])['download_allowed'] else 'none'
                elif body.action in ('suspend_user', 'restore_user'):
                    if row['target_type'] != 'user' or not self.accounts:
                        raise HTTPException(409, 'An account user incident is required')
                    target = db.execute('SELECT * FROM memberships WHERE organization_id=? AND user_id=?', (org, row['target_id'])).fetchone()
                    if not target:
                        raise HTTPException(404, 'Member not found')
                    if body.action == 'suspend_user':
                        others = db.execute("SELECT COUNT(*) FROM memberships WHERE organization_id=? AND role='admin' AND active=1 AND user_id!=?", (org, row['target_id'])).fetchone()[0]
                        if row['target_id'] == user['id'] or not others or not target['active']:
                            raise HTTPException(409, 'Keep another active admin; only active users can be suspended')
                        db.execute('UPDATE memberships SET active=0 WHERE organization_id=? AND user_id=?', (org, row['target_id']))
                        containment = 'user_suspended'
                    else:
                        if containment != 'user_suspended':
                            raise HTTPException(409, 'This incident did not suspend that user')
                        self.accounts.licensing.require_capacity(db, org)
                        db.execute('UPDATE memberships SET active=1 WHERE organization_id=? AND user_id=?', (org, row['target_id']))
                        containment = 'none'
                    self.accounts.audit(db, org, user['id'], 'security.'+body.action, row['target_id'])
                elif body.action == 'revoke_credential':
                    if row['target_type'] != 'credential':
                        raise HTTPException(409, 'An integration credential incident is required')
                    db.execute('UPDATE integration_credentials SET revoked_at=? WHERE id=? AND organization_id=?', (now(), row['target_id'], org))
                    containment = 'credential_revoked'
                elif body.action == 'resolve':
                    if containment == 'user_suspended':
                        raise HTTPException(409, 'Review and restore the suspended user before resolving')
                    if row['target_type'] == 'file' and not self.file_status(db, org, row['target_id'])['download_allowed']:
                        raise HTTPException(409, 'File remains held; investigate and release after a clean scan')
                    status = 'resolved'
                elif body.action == 'resolve_contained':
                    if row['target_type'] == 'file':
                        if self.file_status(db, org, row['target_id'])['download_allowed']:
                            raise HTTPException(409, 'The file is not contained')
                    elif row['target_type'] == 'user':
                        member = db.execute('SELECT active FROM memberships WHERE organization_id=? AND user_id=?', (org, row['target_id'])).fetchone() if self.accounts else None
                        if containment != 'user_suspended' or not member or member['active']:
                            raise HTTPException(409, 'The user is not contained by this incident')
                    elif containment != 'credential_revoked':
                        raise HTTPException(409, 'Contain the affected resource before closing it as contained')
                    status = 'resolved'
                elif body.action == 'reopen':
                    if row['status'] != 'resolved':
                        raise HTTPException(409, 'Only a closed incident can be reopened')
                    status = 'open'
                elif body.action == 'acknowledge':
                    status = 'acknowledged'
                version = row['version'] + 1
                db.execute('UPDATE security_incidents SET status=?,containment=?,version=?,updated_at=? WHERE id=? AND organization_id=?', (status, containment, version, now(), row['id'], org))
                self.audit(db, org, row['id'], user['id'], body.action, body.reason)
                db.execute('INSERT INTO security_alert_reads VALUES (?,?,?,?) ON CONFLICT(organization_id,user_id,incident_id) DO UPDATE SET version=excluded.version', (org, user['id'], row['id'], version))
            return {'id': str(incident_id), 'version': version, 'status': status, 'containment': containment}
