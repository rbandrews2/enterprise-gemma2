"""Verified identity plus database-owned organization membership and entitlement.

No password storage, email-only membership lookup, client-selected role or
automatic administrator grants. Administrators are organization-scoped, not site admins.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4
from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class FirebaseVerifier:
    def __init__(self, project):
        import firebase_admin
        self.app = firebase_admin.initialize_app(options={'projectId': project}, name='wzos-' + str(uuid4()))

    def __call__(self, token):
        from firebase_admin import auth
        return auth.verify_id_token(token, app=self.app, check_revoked=True)


class NewOrganization(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=120)
    activation_code: str = Field(min_length=32, max_length=128)


class Invitation(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    email: str = Field(min_length=3, max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    role: Literal['admin', 'member'] = 'member'


class Join(BaseModel):
    model_config = ConfigDict(extra='forbid')
    token: str = Field(min_length=32, max_length=128)


class MembershipChange(BaseModel):
    model_config = ConfigDict(extra='forbid')
    role: Literal['admin', 'member']
    active: bool


class Accounts:
    def __init__(self, connect, verify):
        self.connect, self.verify = connect, verify
        with connect() as db:
            for sql in (
                'CREATE TABLE IF NOT EXISTS accounts (id TEXT PRIMARY KEY,email TEXT NOT NULL,name TEXT NOT NULL)',
                "CREATE TABLE IF NOT EXISTS organizations (id TEXT PRIMARY KEY,name TEXT NOT NULL,edition TEXT NOT NULL CHECK(edition IN ('core','enterprise')),active INTEGER NOT NULL)",
                "CREATE TABLE IF NOT EXISTS memberships (organization_id TEXT NOT NULL,user_id TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('admin','member')),active INTEGER NOT NULL,PRIMARY KEY(organization_id,user_id))",
                'CREATE TABLE IF NOT EXISTS activation_codes (hash TEXT PRIMARY KEY,edition TEXT NOT NULL,expires_at TEXT NOT NULL,used_by TEXT,organization_id TEXT)',
                'CREATE TABLE IF NOT EXISTS invitations (hash TEXT PRIMARY KEY,organization_id TEXT NOT NULL,email TEXT NOT NULL,role TEXT NOT NULL,expires_at TEXT NOT NULL,accepted_by TEXT)',
                'CREATE TABLE IF NOT EXISTS access_audit (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,actor_id TEXT NOT NULL,action TEXT NOT NULL,target_id TEXT NOT NULL,occurred_at TEXT NOT NULL)',
            ):
                db.execute(sql)
            # Compatibility migration: preserve existing membership IDs and activity.
            # Legacy CHECK constraints permit admin; fresh databases use two roles.
            db.execute("UPDATE memberships SET role='admin' WHERE role='owner'")

    def identity(self, request):
        cached = getattr(request.state, 'verified_identity', None)
        if cached:
            return cached
        header = request.headers.get('authorization', '')
        if not header.startswith('Bearer ') or len(header) > 8192:
            raise HTTPException(401, 'Sign in to continue')
        try:
            claims = self.verify(header[7:])
        except Exception:
            raise HTTPException(401, 'Session expired or could not be verified') from None
        if not claims.get('uid') or not claims.get('email') or claims.get('email_verified') is not True:
            raise HTTPException(403, 'Verify your email before accessing WZOS')
        person = {'id': claims['uid'], 'email': claims['email'].lower(),
                  'name': str(claims.get('name') or claims['email'])[:200]}
        with self.connect() as db:
            db.execute('INSERT INTO accounts VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET email=excluded.email,name=excluded.name',
                       (person['id'], person['email'], person['name']))
        request.state.verified_identity = person
        return person

    def actor(self, request):
        user = self.identity(request)
        org = request.headers.get('X-WZOS-Organization', '')
        with self.connect() as db:
            row = db.execute('SELECT m.role,o.id,o.name,o.edition FROM memberships m JOIN organizations o ON o.id=m.organization_id WHERE m.user_id=? AND o.id=? AND m.active=1 AND o.active=1', (user['id'], org)).fetchone()
        if not row:
            raise HTTPException(403, 'Active organization membership required')
        return {**user, 'membership_role': row['role'],
                'role': 'admin' if row['role'] == 'admin' else 'general',
                'organization_id': row['id'], 'organization': row['name'], 'edition': row['edition']}

    def roster(self, selected):
        with self.connect() as db:
            rows = db.execute('SELECT a.id,a.name,m.role FROM accounts a JOIN memberships m ON a.id=m.user_id WHERE m.organization_id=? AND m.active=1', (selected['organization_id'],)).fetchall()
        return {r['id']: {'id':r['id'],'name':r['name'],'role':'admin' if r['role'] == 'admin' else 'general','organization_id':selected['organization_id']} for r in rows}

    def audit(self, db, org, actor, action, target):
        db.execute('INSERT INTO access_audit VALUES (?,?,?,?,?,?)', (str(uuid4()),org,actor,action,target,now()))

    def issue_activation(self, edition, hours=168):
        if edition not in ('core', 'enterprise') or not 1 <= hours <= 168:
            raise ValueError('Invalid activation settings')
        token = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute('INSERT INTO activation_codes VALUES (?,?,?,?,?)', (digest(token),edition,(datetime.now(timezone.utc)+timedelta(hours=hours)).isoformat(),None,None))
        return token

    def register(self, app):
        @app.get('/api/account/members')
        def members(request: Request):
            selected=self.actor(request)
            if selected['role']!='admin': raise HTTPException(403,'Administrator access required')
            with self.connect() as db:
                rows=db.execute('SELECT a.id,a.name,a.email,m.role,m.active FROM accounts a JOIN memberships m ON a.id=m.user_id WHERE m.organization_id=? ORDER BY a.name,a.id LIMIT 100',(selected['organization_id'],)).fetchall()
            return {'items':[dict(r) for r in rows], 'can_change_access':selected['membership_role']=='admin'}

        @app.get('/api/account')
        def account(request: Request):
            user = self.identity(request)
            with self.connect() as db:
                rows=db.execute('SELECT o.id,o.name,o.edition,m.role FROM memberships m JOIN organizations o ON o.id=m.organization_id WHERE m.user_id=? AND m.active=1 AND o.active=1', (user['id'],)).fetchall()
            return {**user, 'organizations':[dict(r) for r in rows]}

        @app.post('/api/account/organizations')
        def create(body: NewOrganization, request: Request):
            user=self.identity(request)
            with self.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                code=db.execute('SELECT * FROM activation_codes WHERE hash=?', (digest(body.activation_code),)).fetchone()
                if not code or code['expires_at'] < now():
                    raise HTTPException(403, 'Activation code is invalid or expired')
                if code['used_by']:
                    if code['used_by'] == user['id']:
                        return {'id':code['organization_id']}
                    raise HTTPException(403, 'Activation code is unavailable')
                org=str(uuid4())
                db.execute('INSERT INTO organizations VALUES (?,?,?,1)', (org,body.name,code['edition']))
                db.execute("INSERT INTO memberships VALUES (?,?,'admin',1)", (org,user['id']))
                db.execute('UPDATE activation_codes SET used_by=?,organization_id=? WHERE hash=?', (user['id'],org,digest(body.activation_code)))
                self.audit(db,org,user['id'],'organization_created',user['id'])
            return {'id':org}

        @app.post('/api/account/invitations')
        def invite(body: Invitation, request: Request):
            selected=self.actor(request)
            if selected['role'] != 'admin':
                raise HTTPException(403,'Administrator access required')
            token=secrets.token_urlsafe(32)
            with self.connect() as db:
                db.execute('INSERT INTO invitations VALUES (?,?,?,?,?,NULL)', (digest(token),selected['organization_id'],body.email.lower(),body.role,(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()))
                self.audit(db,selected['organization_id'],selected['id'],'invitation_created',digest(token))
            return {'token':token,'expires_in_days':7,'delivery_sent':False}

        @app.post('/api/account/join')
        def join(body: Join, request: Request):
            user=self.identity(request)
            with self.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                invitation=db.execute('SELECT i.* FROM invitations i JOIN organizations o ON o.id=i.organization_id WHERE i.hash=? AND o.active=1', (digest(body.token),)).fetchone()
                if not invitation or invitation['email'] != user['email'] or invitation['expires_at'] < now() or invitation['accepted_by'] not in (None,user['id']):
                    raise HTTPException(403,'Invitation is unavailable for this verified account')
                # Existing membership is never reactivated or promoted by an invitation.
                db.execute('INSERT INTO memberships VALUES (?,?,?,1) ON CONFLICT DO NOTHING', (invitation['organization_id'],user['id'],invitation['role']))
                db.execute('UPDATE invitations SET accepted_by=? WHERE hash=?', (user['id'],digest(body.token)))
                self.audit(db,invitation['organization_id'],user['id'],'invitation_accepted',user['id'])
            return {'id':invitation['organization_id']}

        @app.put('/api/account/members/{user_id}')
        def change(user_id: str, body: MembershipChange, request: Request):
            selected=self.actor(request)
            with self.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                current=db.execute("SELECT role FROM memberships WHERE organization_id=? AND user_id=? AND active=1",(selected['organization_id'],selected['id'])).fetchone()
                if not current or current['role']!='admin':
                    raise HTTPException(403,'Only an active organization admin can change access')
                target=db.execute('SELECT * FROM memberships WHERE organization_id=? AND user_id=?',(selected['organization_id'],user_id)).fetchone()
                if not target: raise HTTPException(404,'Member not found')
                count=db.execute("SELECT COUNT(*) FROM memberships WHERE organization_id=? AND role='admin' AND active=1",(selected['organization_id'],)).fetchone()[0]
                if target['role']=='admin' and target['active'] and count==1 and (body.role!='admin' or not body.active):
                    raise HTTPException(409,'Keep at least one active admin')
                db.execute('UPDATE memberships SET role=?,active=? WHERE organization_id=? AND user_id=?',(body.role,int(body.active),selected['organization_id'],user_id))
                self.audit(db,selected['organization_id'],selected['id'],'membership_'+body.role+('_enabled' if body.active else '_disabled'),user_id)
            return {'updated':True}
