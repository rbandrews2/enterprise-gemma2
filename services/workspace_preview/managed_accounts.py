"""Organization-managed Google identities. Passwords are never persisted here."""
import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from starlette.responses import JSONResponse

DDL = (
    'CREATE TABLE IF NOT EXISTS managed_accounts (user_id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,username TEXT NOT NULL UNIQUE,email TEXT NOT NULL UNIQUE,created_by TEXT NOT NULL,request_id TEXT NOT NULL,fingerprint TEXT NOT NULL,state TEXT NOT NULL,password_changed INTEGER NOT NULL,created_at TEXT NOT NULL,UNIQUE(organization_id,request_id))',
    'CREATE TABLE IF NOT EXISTS organization_creation_grants (id TEXT PRIMARY KEY,email TEXT NOT NULL,edition TEXT NOT NULL,seat_limit INTEGER NOT NULL,expires_at TEXT NOT NULL,organization_id TEXT,used_by TEXT)',
    'CREATE TABLE IF NOT EXISTS managed_login_limits (key TEXT PRIMARY KEY,window_start INTEGER NOT NULL,attempts INTEGER NOT NULL)',
)


class CreateAccount(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: UUID
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=254, pattern=r'^[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+$')
    username: str = Field(min_length=3, max_length=40, pattern=r'^[A-Za-z0-9][A-Za-z0-9._-]*$')
    password: SecretStr
    role: Literal['admin', 'member'] = 'member'


class SignIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    username: str = Field(min_length=1, max_length=254)
    password: SecretStr


class ChangePassword(BaseModel):
    model_config = ConfigDict(extra='forbid')
    password: SecretStr


def password_value(secret):
    value = secret.get_secret_value()
    if not 12 <= len(value) <= 128 or not value.strip() or '\x00' in value:
        raise HTTPException(422, 'Use a password between 12 and 128 characters.')
    return value


def stamp():
    return datetime.now(timezone.utc).isoformat()


def issue_organization_grant(accounts, email, edition, seats, hours=168):
    """Operator-only helper, never exposed as a customer API."""
    accounts.licensing.validate(seats, email)
    if edition not in ('core', 'enterprise') or not 1 <= hours <= 168:
        raise ValueError('Invalid grant settings')
    grant_id = str(uuid4())
    with accounts.connect() as db:
        db.execute('INSERT INTO organization_creation_grants VALUES (?,?,?,?,?,NULL,NULL)',
                   (grant_id, email.lower(), edition, seats, (datetime.now(timezone.utc)+timedelta(hours=hours)).isoformat()))
    return grant_id


def password_sign_in(email, password):
    # The existing browser-restricted API key remains restricted. Use the same
    # approved app origin; never return the directory mapping to the browser.
    key = os.getenv('WZOS_AUTH_WEB_API_KEY', '')
    if not key:
        raise HTTPException(503, 'Username sign-in is not configured yet.')
    try:
        response = httpx.post('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword',
                              params={'key': key}, headers={'Referer': 'https://app.workzoneos.org/'},
                              json={'email': email, 'password': password, 'returnSecureToken': True}, timeout=15)
        data = response.json()
    except Exception:
        raise HTTPException(503, 'Sign-in is temporarily unavailable.') from None
    if response.status_code != 200:
        raise HTTPException(401, 'Incorrect password or username.')
    return {k: data[k] for k in ('idToken', 'refreshToken', 'expiresIn', 'localId')}


def register(app, accounts):
    previous_validation = app.exception_handlers.get(RequestValidationError, request_validation_exception_handler)

    @app.exception_handler(RequestValidationError)
    async def private_validation(request, error):
        if request.url.path.startswith('/api/account/managed/'):
            # Pydantic normally echoes submitted input, including passwords.
            return JSONResponse({'detail': 'Check the required account fields.'}, status_code=422,
                                headers={'Cache-Control': 'no-store'})
        return await previous_validation(request, error)

    def admin(request):
        user = accounts.actor(request)
        if user['role'] != 'admin':
            raise HTTPException(403, 'Administrator access required')
        if not all(hasattr(accounts.verify, name) for name in ('create_managed', 'enable_managed', 'get_managed', 'change_managed_password')):
            raise HTTPException(503, 'Managed account setup is unavailable.')
        return user

    def lock_admin(db, actor):
        # Lock the organization for capacity and membership changes on PostgreSQL
        # and SQLite alike. Every creation rechecks the caller under that lock.
        db.execute('UPDATE organizations SET active=active WHERE id=?', (actor['organization_id'],))
        row = db.execute('SELECT m.role FROM memberships m JOIN organizations o ON o.id=m.organization_id WHERE m.organization_id=? AND m.user_id=? AND m.active=1 AND o.active=1',
                         (actor['organization_id'], actor['id'])).fetchone()
        if not row or row['role'] != 'admin':
            raise HTTPException(403, 'Administrator access required')

    @app.post('/api/account/managed/accounts')
    def create(body: CreateAccount, request: Request):
        actor = admin(request)
        password = password_value(body.password)
        email, username = body.email.strip().lower(), body.username.lower()
        fingerprint = hashlib.sha256(json.dumps([body.name.strip(), email, username, body.role]).encode()).hexdigest()
        with accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            lock_admin(db, actor)
            existing = db.execute('SELECT * FROM managed_accounts WHERE organization_id=? AND request_id=?',
                                  (actor['organization_id'], str(body.request_id))).fetchone()
            if existing:
                if existing['created_by'] != actor['id'] or existing['fingerprint'] != fingerprint:
                    raise HTTPException(409, 'This request belongs to different account details.')
                uid = existing['user_id']
                if existing['state'] == 'ready':
                    return {'id': uid, 'username': username, 'role': body.role, 'created': True, 'invitation_required': False}
            else:
                if db.execute('SELECT 1 FROM managed_accounts WHERE username=? OR email=?', (username,email)).fetchone() or db.execute('SELECT 1 FROM accounts WHERE lower(email)=?', (email,)).fetchone():
                    raise HTTPException(409, 'That username or email is already registered. Use an invitation for an existing account.')
                accounts.licensing.require_capacity(db, actor['organization_id'])
                uid = 'wzos-' + str(uuid4())
                # Provider refuses duplicate emails; never update another identity.
                try:
                    accounts.verify.create_managed(uid, email, password, body.name.strip())
                except Exception:
                    raise HTTPException(409, 'Account could not be created. Check whether the email is already registered, or contact WZOS support.') from None
                db.execute('INSERT INTO accounts VALUES (?,?,?)', (uid,email,body.name.strip()))
                db.execute('INSERT INTO memberships VALUES (?,?,?,1)', (actor['organization_id'],uid,body.role))
                db.execute('INSERT INTO managed_accounts VALUES (?,?,?,?,?,?,?,?,0,?)',
                           (uid,actor['organization_id'],username,email,actor['id'],str(body.request_id),fingerprint,'pending',stamp()))
                accounts.audit(db,actor['organization_id'],actor['id'],'managed_account_created',uid)
        # A provider identity remains disabled if the DB transaction fails.
        # Retry of the same request only enables this reserved identity.
        with accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            lock_admin(db, actor)
            target = db.execute('SELECT active FROM memberships WHERE organization_id=? AND user_id=?', (actor['organization_id'],uid)).fetchone()
            if not target or not target['active']:
                raise HTTPException(409, 'Account setup was disabled by an administrator.')
            try:
                provider_user = accounts.verify.get_managed(uid)
                if provider_user.email.lower() != email:
                    raise ValueError('Identity mismatch')
                accounts.verify.enable_managed(uid)
            except Exception:
                raise HTTPException(503, 'Account is reserved but sign-in setup is incomplete. Retry the same request.') from None
            db.execute("UPDATE managed_accounts SET state='ready' WHERE user_id=?", (uid,))
        return {'id': uid, 'username': username, 'role': body.role, 'created': True, 'invitation_required': False}

    from . import bulk_managed
    bulk_managed.register(app, accounts, admin, create, CreateAccount, password_value)

    @app.post('/api/account/managed/sign-in')
    def sign_in(body: SignIn, request: Request):
        username = body.username.lower().strip()
        # Shared database limits work across Cloud Run instances. Do not persist
        # identifiers or addresses in this throttle table, only one-way digests.
        window = int(time.time()) // 900
        peer = request.client.host if request.client else 'unknown'
        keys = [(hashlib.sha256(('peer:'+peer).encode()).hexdigest(), 100),
                (hashlib.sha256(('user:'+username).encode()).hexdigest(), 10)]
        limited = False
        with accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM managed_login_limits WHERE window_start<?', (window-1,))
            for key, maximum in keys:
                db.execute('INSERT INTO managed_login_limits VALUES (?,?,1) ON CONFLICT(key) DO UPDATE SET attempts=CASE WHEN managed_login_limits.window_start=excluded.window_start THEN managed_login_limits.attempts+1 ELSE 1 END,window_start=excluded.window_start', (key,window))
                count=db.execute('SELECT attempts FROM managed_login_limits WHERE key=?',(key,)).fetchone()[0]
                limited |= count > maximum
                if limited:
                    break
            row = db.execute("SELECT a.* FROM managed_accounts a JOIN memberships m ON m.user_id=a.user_id AND m.organization_id=a.organization_id JOIN organizations o ON o.id=m.organization_id WHERE a.username=? AND a.state='ready' AND m.active=1 AND o.active=1", (username,)).fetchone()
        if limited:
            raise HTTPException(429, 'Too many sign-in attempts. Try again in 15 minutes.')
        if not row or not 1 <= len(body.password.get_secret_value()) <= 128:
            raise HTTPException(401, 'Incorrect password or username.')
        data = password_sign_in(row['email'], body.password.get_secret_value())
        if data.pop('localId') != row['user_id']:
            raise HTTPException(401, 'Incorrect password or username.')
        return JSONResponse(data, headers={'Cache-Control':'no-store'})

    @app.post('/api/account/managed/password')
    def change_password(body: ChangePassword, request: Request):
        user = accounts.identity(request)
        value = password_value(body.password)
        with accounts.connect() as db:
            row = db.execute("SELECT * FROM managed_accounts WHERE user_id=? AND state='ready'",(user['id'],)).fetchone()
            if not row:
                raise HTTPException(403, 'Use your account password recovery options.')
            try:
                accounts.verify.change_managed_password(user['id'], value)
            except Exception:
                raise HTTPException(503, 'Password could not be changed. Try again.') from None
            db.execute('UPDATE managed_accounts SET password_changed=1 WHERE user_id=?',(user['id'],))
            db.execute('DELETE FROM browser_sessions WHERE user_id=?',(user['id'],))
            accounts.audit(db,row['organization_id'],user['id'],'managed_password_changed',user['id'])
        return {'changed':True,'sign_in_again':True}
