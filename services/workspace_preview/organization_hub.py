"""Admin landing page and deliberately narrow, read-only integration API.

Service/account signals are operator evidence, never inferred from login success.
Integration credentials do not authenticate browser sessions or authorize writes.
"""
import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import JSONResponse
from typing import Literal

DDL = (
    'CREATE TABLE IF NOT EXISTS hub_notes (organization_id TEXT NOT NULL,id TEXT NOT NULL,author_id TEXT NOT NULL,body TEXT NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(organization_id,id))',
    'CREATE TABLE IF NOT EXISTS hub_preferences (organization_id TEXT PRIMARY KEY,version INTEGER NOT NULL,hidden_modules TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS hub_status_checks (organization_id TEXT NOT NULL,kind TEXT NOT NULL,status TEXT NOT NULL,explanation TEXT NOT NULL,source TEXT NOT NULL,checked_at TEXT NOT NULL,expires_at TEXT NOT NULL,PRIMARY KEY(organization_id,kind))',
    'CREATE TABLE IF NOT EXISTS integration_credentials (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,creator_id TEXT NOT NULL,name TEXT NOT NULL,token_hash TEXT NOT NULL UNIQUE,scopes TEXT NOT NULL,created_at TEXT NOT NULL,expires_at TEXT NOT NULL,revoked_at TEXT)',
    'CREATE TABLE IF NOT EXISTS integration_usage (organization_id TEXT NOT NULL,minute TEXT NOT NULL,requests INTEGER NOT NULL,PRIMARY KEY(organization_id,minute))',
    'CREATE TABLE IF NOT EXISTS hub_audit (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,actor_id TEXT NOT NULL,action TEXT NOT NULL,target_id TEXT NOT NULL,occurred_at TEXT NOT NULL)',
    'CREATE INDEX IF NOT EXISTS hub_audit_org_action_time ON hub_audit(organization_id,action,occurred_at)',
)

MODULES = (
    ('orders', 'Work orders', '▤', 'jobs-nav', False),
    ('assignments', 'My jobs', '▥', 'assignments-nav', True),
    ('report', 'Work Zone Report', '◈', 'report-nav', True),
    ('atlas', 'Atlas assistant', '✦', 'atlas-nav', False),
    ('forms', 'Forms hub', '▧', 'forms-nav', False),
    ('clock', 'Time Tracker', '⚡', 'clock-nav', False),
    ('schedule', 'Schedule management', '▦', 'schedule-nav', False),
    ('navigation', 'Navigation', '⌖', 'navigation-nav', False),
    ('messages', 'Messaging / dispatch', '✉', 'messages-nav', False),
    ('meetings', 'Video meetings', '▣', 'meetings-nav', False),
    ('training', 'Video training', '▷', 'training-nav', False),
)
MODULE_IDS = {item[0] for item in MODULES}


class HubRequestLimit:
    """Bound actual incoming bytes, including bodies without Content-Length."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or not scope['path'].startswith(('/api/admin/', '/api/integrations/')):
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            size += len(message.get('body', b''))
            if size > 16384:
                return await JSONResponse({'detail': 'Request exceeds 16 KiB'}, status_code=413)(scope, receive, send)
            chunks.append(message)
            if not message.get('more_body', False):
                break
        async def replay():
            return chunks.pop(0) if chunks else await receive()
        await self.app(scope, replay, send)


class Note(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    request_id: UUID
    text: str = Field(min_length=1, max_length=500)


class Preferences(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_version: int = Field(ge=0, strict=True)
    hidden_modules: list[str] = Field(max_length=20)


class Credential(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=80)
    scopes: list[Literal['orders:read', 'schedule:read']] = Field(min_length=1, max_length=2)
    expires_in_days: int = Field(default=30, ge=1, le=90, strict=True)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def register(app, connect, actor, *, accounts=False, roster=None):
    app.add_middleware(HubRequestLimit)
    with connect() as db:
        for sql in DDL:
            db.execute(sql)

    def admin(request):
        user = actor(request)
        if user['role'] != 'admin':
            raise HTTPException(403, 'Administrator access required')
        return user

    def audit(db, user, action, target):
        db.execute('INSERT INTO hub_audit VALUES (?,?,?,?,?,?)',
                   (str(uuid4()), user['organization_id'], user['id'], action, target, stamp()))

    def mutation_limit(db, user, action):
        since = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        count = db.execute('SELECT COUNT(*) FROM hub_audit WHERE organization_id=? AND action=? AND occurred_at>?', (user['organization_id'], action, since)).fetchone()[0]
        if count >= 30:
            raise HTTPException(429, 'Too many changes. Retry in one minute.', headers={'Retry-After': '60'})

    @app.get('/api/admin/dashboard')
    def dashboard(request: Request):
        user = admin(request)
        with connect() as db:
            pref = db.execute('SELECT * FROM hub_preferences WHERE organization_id=?', (user['organization_id'],)).fetchone()
            observed = {r['kind']: dict(r) for r in db.execute('SELECT * FROM hub_status_checks WHERE organization_id=?', (user['organization_id'],)).fetchall()}
            notes = db.execute('SELECT id,author_id,body,created_at FROM hub_notes WHERE organization_id=? ORDER BY created_at DESC,id DESC LIMIT 50', (user['organization_id'],)).fetchall()
        hidden = json.loads(pref['hidden_modules']) if pref else []
        checks = []
        for kind, label in [('service', 'WZOS service'), ('account', 'Account standing'), ('security', 'Security signals')]:
            check = observed.get(kind)
            try:
                valid = (check and check['status'] in ('ok', 'problem') and check['source'].strip()
                         and check['explanation'].strip()
                         and datetime.fromisoformat(check['checked_at']) <= datetime.now(timezone.utc)
                         < datetime.fromisoformat(check['expires_at']))
            except (ValueError, TypeError):
                valid = False
            checks.append({'kind': kind, 'label': label, 'status': check['status'] if valid else 'unknown',
                           'explanation': check['explanation'] if valid else 'No current verified check available.',
                           'checked_at': check['checked_at'] if valid else None,
                           'source': check['source'] if valid else None})
        status = 'red' if any(c['status'] == 'problem' for c in checks) else 'green' if all(c['status'] == 'ok' for c in checks) else 'amber'
        people = roster(user) if roster else {}
        return {'organization': user['organization'], 'edition': user['edition'], 'status': status,
                'checks': checks, 'preferences_version': pref['version'] if pref else 0,
                'modules': [{'id': key, 'label': 'Messaging' if key == 'messages' and user['edition'] == 'core' else label, 'icon': icon, 'nav_id': nav, 'visible': key not in hidden}
                            for key, label, icon, nav, enterprise in MODULES if not enterprise or user['edition'] == 'enterprise'],
                'notes': [{**dict(r), 'author_name': people.get(r['author_id'], {}).get('name', 'Organization admin')} for r in notes], 'notes_limit': 50}

    @app.put('/api/admin/dashboard/preferences')
    def preferences(body: Preferences, request: Request):
        user = admin(request)
        if len(set(body.hidden_modules)) != len(body.hidden_modules) or not set(body.hidden_modules) <= MODULE_IDS:
            raise HTTPException(422, 'Choose unique existing modules')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current = db.execute('SELECT version FROM hub_preferences WHERE organization_id=?', (user['organization_id'],)).fetchone()
            version = current['version'] if current else 0
            if version != body.expected_version:
                raise HTTPException(409, 'Dashboard preferences changed. Reload before saving.')
            db.execute('INSERT INTO hub_preferences VALUES (?,?,?) ON CONFLICT(organization_id) DO UPDATE SET version=excluded.version,hidden_modules=excluded.hidden_modules',
                       (user['organization_id'], version + 1, json.dumps(body.hidden_modules)))
            audit(db, user, 'dashboard.preferences', user['organization_id'])
        return {'version': version + 1}

    @app.post('/api/admin/dashboard/notes')
    def note(body: Note, request: Request):
        user = admin(request)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT * FROM hub_notes WHERE organization_id=? AND id=?', (user['organization_id'], str(body.request_id))).fetchone()
            if old:
                if old['author_id'] != user['id'] or old['body'] != body.text:
                    raise HTTPException(409, 'Note retry identifier conflict')
                return {'id': old['id']}
            count = db.execute('SELECT COUNT(*) FROM hub_notes WHERE organization_id=?', (user['organization_id'],)).fetchone()[0]
            if count >= 500:
                raise HTTPException(409, 'Remove older notes before adding more')
            mutation_limit(db, user, 'dashboard.note.create')
            db.execute('INSERT INTO hub_notes VALUES (?,?,?,?,?)', (user['organization_id'], str(body.request_id), user['id'], body.text, stamp()))
            audit(db, user, 'dashboard.note.create', str(body.request_id))
        return {'id': str(body.request_id)}

    @app.delete('/api/admin/dashboard/notes/{note_id}')
    def remove_note(note_id: UUID, request: Request):
        user = admin(request)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM hub_notes WHERE organization_id=? AND id=?', (user['organization_id'], str(note_id)))
            audit(db, user, 'dashboard.note.delete', str(note_id))
        return {'removed': True}

    @app.get('/api/admin/integrations')
    def credentials(request: Request):
        user = admin(request)
        with connect() as db:
            rows = db.execute('SELECT id,name,scopes,created_at,expires_at,revoked_at FROM integration_credentials WHERE organization_id=? ORDER BY created_at DESC LIMIT 100', (user['organization_id'],)).fetchall()
        return {'items': [{**dict(r), 'scopes': json.loads(r['scopes'])} for r in rows], 'supported_scopes': ['orders:read', 'schedule:read']}

    @app.post('/api/admin/integrations')
    def create_credential(body: Credential, request: Request):
        user = admin(request)
        token = 'wzos_' + secrets.token_urlsafe(32)
        identifier, created = str(uuid4()), stamp()
        expires = (datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)).isoformat()
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            count = db.execute('SELECT COUNT(*) FROM integration_credentials WHERE organization_id=? AND revoked_at IS NULL AND expires_at>?', (user['organization_id'], created)).fetchone()[0]
            if count >= 10:
                raise HTTPException(409, 'Revoke an existing credential before creating another')
            mutation_limit(db, user, 'integration.create')
            db.execute('INSERT INTO integration_credentials VALUES (?,?,?,?,?,?,?,?,?)', (identifier, user['organization_id'], user['id'], body.name,
                       hashlib.sha256(token.encode()).hexdigest(), json.dumps(sorted(set(body.scopes))), created, expires, None))
            audit(db, user, 'integration.create', identifier)
        return {'id': identifier, 'token': token, 'expires_at': expires, 'warning': 'Shown once. Store in your integration secret manager.'}

    @app.delete('/api/admin/integrations/{credential_id}')
    def revoke(credential_id: UUID, request: Request):
        user = admin(request)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT id FROM integration_credentials WHERE organization_id=? AND id=?', (user['organization_id'], str(credential_id))).fetchone()
            if not row:
                raise HTTPException(404, 'Credential not found')
            db.execute('UPDATE integration_credentials SET revoked_at=? WHERE organization_id=? AND id=?', (stamp(), user['organization_id'], str(credential_id)))
            audit(db, user, 'integration.revoke', str(credential_id))
        return {'revoked': True}

    def integration(request, scope):
        token = request.headers.get('X-WZOS-API-Key', '')
        if not token.startswith('wzos_') or not 40 <= len(token) <= 128:
            raise HTTPException(401, 'Valid integration credential required')
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with connect() as db:
            # Reject unknown credentials before taking the shared write lock used
            # for revocation/rate counters. Recheck under that lock to avoid races.
            lookup = 'SELECT * FROM integration_credentials WHERE token_hash=? AND revoked_at IS NULL AND expires_at>?'
            if not db.execute(lookup, (token_hash, stamp())).fetchone():
                raise HTTPException(401, 'Credential expired or revoked')
            db.execute('BEGIN IMMEDIATE')
            row = db.execute(lookup, (token_hash, stamp())).fetchone()
            if not row:
                raise HTTPException(401, 'Credential expired or revoked')
            if accounts:
                active = db.execute("SELECT m.user_id FROM memberships m JOIN organizations o ON o.id=m.organization_id WHERE m.organization_id=? AND m.user_id=? AND m.role='admin' AND m.active=1 AND o.active=1", (row['organization_id'], row['creator_id'])).fetchone()
                if not active:
                    raise HTTPException(401, 'Credential administrator is no longer active')
            if scope not in json.loads(row['scopes']):
                raise HTTPException(403, 'Credential does not grant this scope')
            minute = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M')
            db.execute('DELETE FROM integration_usage WHERE minute<?', ((datetime.now(timezone.utc)-timedelta(minutes=2)).strftime('%Y-%m-%dT%H:%M'),))
            usage = db.execute('SELECT requests FROM integration_usage WHERE organization_id=? AND minute=?', (row['organization_id'], minute)).fetchone()
            if usage and usage[0] >= 60:
                raise HTTPException(429, 'Integration request limit reached', headers={'Retry-After': '60'})
            db.execute('INSERT INTO integration_usage VALUES (?,?,1) ON CONFLICT(organization_id,minute) DO UPDATE SET requests=integration_usage.requests+1', (row['organization_id'], minute))
            audit(db, {'organization_id': row['organization_id'], 'id': row['id']}, 'integration.' + scope, row['id'])
            return row['organization_id']

    @app.get('/api/integrations/v1/orders')
    def orders(request: Request, limit: int = Query(25, ge=1, le=50), offset: int = Query(0, ge=0, le=10000)):
        org = integration(request, 'orders:read')
        with connect() as db:
            rows = db.execute('SELECT id,version,payload,updated_at FROM preview_orders WHERE organization_id=? ORDER BY updated_at DESC,id LIMIT ? OFFSET ?', (org, limit, offset)).fetchall()
        return {'items': [{'id': r['id'], 'version': r['version'], 'updated_at': r['updated_at'], **{k: json.loads(r['payload']).get(k) for k in ('title', 'address', 'work_type', 'work_date')}} for r in rows], 'limit': limit, 'offset': offset}

    @app.get('/api/integrations/v1/schedule')
    def schedule(request: Request, limit: int = Query(25, ge=1, le=50), offset: int = Query(0, ge=0, le=10000)):
        org = integration(request, 'schedule:read')
        with connect() as db:
            rows = db.execute("SELECT id,version,payload,updated_at FROM module_records WHERE organization_id=? AND kind='schedule' ORDER BY updated_at DESC,id LIMIT ? OFFSET ?", (org, limit, offset)).fetchall()
        return {'items': [{'id': r['id'], 'version': r['version'], 'updated_at': r['updated_at'], **{k: json.loads(r['payload']).get(k) for k in ('title', 'location', 'start', 'end', 'status')}} for r in rows], 'limit': limit, 'offset': offset}
