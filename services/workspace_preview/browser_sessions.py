"""Revocable Firebase session cookies; no raw token storage."""
from datetime import datetime, timedelta, timezone
import time
from fastapi import HTTPException, Request, Response

COOKIE = '__Host-wzos-session'
LIFETIME = 14 * 24 * 60 * 60


def guard(request):
    if request.headers.get('X-WZOS-Session') != '1':
        raise HTTPException(403, 'First-party session request required')


def register(app, accounts):
    from .accounts import digest, now
    with accounts.connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS browser_sessions (hash TEXT PRIMARY KEY,user_id TEXT NOT NULL,expires_at TEXT NOT NULL)')

    @app.post('/api/account/session')
    def create(request: Request, response: Response):
        guard(request)
        header = request.headers.get(accounts.auth_header, '')
        if not header.startswith('Bearer ') or len(header) > 8192:
            raise HTTPException(401, 'Fresh sign-in required')
        user = accounts.identity(request)
        try:
            claims = accounts.verify(header[7:])
            age = time.time() - float(claims.get('auth_time', 0))
            if not 0 <= age <= 300:
                raise ValueError('Not recent')
        except Exception:
            raise HTTPException(401, 'Sign in again before remembering this device') from None
        if not hasattr(accounts.verify, 'create_session'):
            raise HTTPException(503, 'Persistent sign-in is unavailable')
        try:
            cookie = accounts.verify.create_session(header[7:], timedelta(seconds=LIFETIME))
            if isinstance(cookie, bytes): cookie = cookie.decode('utf-8')
        except Exception:
            raise HTTPException(503, 'Persistent sign-in could not be established') from None
        with accounts.connect() as db:
            db.execute('DELETE FROM browser_sessions WHERE expires_at<=?', (now(),))
            previous = request.cookies.get(COOKIE)
            if previous: db.execute('DELETE FROM browser_sessions WHERE hash=?', (digest(previous),))
            db.execute('INSERT INTO browser_sessions VALUES (?,?,?) ON CONFLICT(hash) DO UPDATE SET expires_at=excluded.expires_at',
                       (digest(cookie), user['id'], (datetime.now(timezone.utc)+timedelta(seconds=LIFETIME)).isoformat()))
        response.set_cookie(COOKIE,cookie,max_age=LIFETIME,secure=True,httponly=True,samesite='strict',path='/')
        return {'persistent': True, 'expires_in': LIFETIME}

    @app.post('/api/account/logout')
    def logout(request: Request, response: Response):
        guard(request)
        cookie=request.cookies.get(COOKIE)
        if cookie:
            with accounts.connect() as db:
                db.execute('DELETE FROM browser_sessions WHERE hash=?', (digest(cookie),))
        response.delete_cookie(COOKIE,secure=True,httponly=True,samesite='strict',path='/')
        return {'signed_out': True}

    @app.post('/api/account/logout-all')
    def logout_all(request: Request, response: Response):
        guard(request)
        user=accounts.identity(request)
        with accounts.connect() as db:
            db.execute('DELETE FROM browser_sessions WHERE user_id=?', (user['id'],))
        response.delete_cookie(COOKIE,secure=True,httponly=True,samesite='strict',path='/')
        return {'remembered_sessions_revoked': True}


def verify_cookie(accounts, request):
    from .accounts import digest, now
    cookie=request.cookies.get(COOKIE, '')
    if not cookie: raise HTTPException(401,'Sign in to continue')
    guard(request)
    if not cookie or len(cookie)>8192 or not hasattr(accounts.verify,'verify_session'):
        raise HTTPException(401,'Sign in to continue')
    with accounts.connect() as db:
        row=db.execute('SELECT user_id,expires_at FROM browser_sessions WHERE hash=?',(digest(cookie),)).fetchone()
    if not row or row['expires_at']<=now():
        raise HTTPException(401,'Session expired or signed out')
    try:
        claims=accounts.verify.verify_session(cookie)
        if claims.get('uid')!=row['user_id']: raise ValueError('Identity mismatch')
        return claims
    except Exception:
        raise HTTPException(401,'Session expired or could not be verified') from None
