"""Opt-in WebAuthn credentials, with Google remaining the identity authority."""
import base64
import hashlib
import json
import os
import secrets
import time
from urllib.parse import urlsplit
from fastapi import HTTPException, Request, Response
from pydantic import BaseModel, Field, ConfigDict
from .accounts import digest, now
from .browser_sessions import guard

COOKIE = '__Host-wzos-passkey'


def encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')


def decode(value):
    return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))


class Ceremony(BaseModel):
    model_config = ConfigDict(extra='forbid')
    credential: dict
    label: str = Field(default='My device', min_length=1, max_length=80)


def register(app, accounts):
    origin = os.getenv('WZOS_PASSKEY_ORIGIN', '')
    if not origin:
        return False
    parsed = urlsplit(origin)
    rp_id = os.getenv('WZOS_PASSKEY_RP_ID', '')
    local = parsed.scheme == 'http' and parsed.hostname == 'localhost' and not os.getenv('K_SERVICE')
    if (not rp_id or parsed.hostname != rp_id or (parsed.scheme != 'https' and not local)
            or origin != f'{parsed.scheme}://{parsed.netloc}' or parsed.username or parsed.password):
        raise RuntimeError('Passkeys require an exact configured origin and matching RP host')
    from webauthn import generate_registration_options, generate_authentication_options, verify_registration_response, verify_authentication_response, options_to_json
    from webauthn.helpers.structs import AuthenticatorSelectionCriteria, ResidentKeyRequirement, UserVerificationRequirement, PublicKeyCredentialDescriptor
    with accounts.connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS passkeys (id TEXT PRIMARY KEY,user_id TEXT NOT NULL,public_key TEXT NOT NULL,sign_count INTEGER NOT NULL,label TEXT NOT NULL,created_at TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS passkey_challenges (hash TEXT PRIMARY KEY,challenge TEXT NOT NULL,kind TEXT NOT NULL,user_id TEXT NOT NULL,expires_at INTEGER NOT NULL)')

    def first_party(request):
        guard(request)
        if request.headers.get('origin') != origin:
            raise HTTPException(403, 'Passkey origin is not authorized')

    def recent(request):
        user = accounts.identity(request)
        header = request.headers.get(accounts.auth_header, '')
        try:
            if header.startswith('Bearer '):
                claims = accounts.verify(header[7:])
            else:
                from .browser_sessions import verify_cookie
                claims = verify_cookie(accounts, request)
            if not 0 <= time.time() - float(claims.get('auth_time', 0)) <= 300:
                raise ValueError('stale')
        except Exception:
            raise HTTPException(401, 'Sign in again before changing passkeys') from None
        return user

    def issue(request, response, kind, user_id, options):
        challenge = encode(options.challenge)
        nonce = secrets.token_urlsafe(32)
        with accounts.connect() as db:
            db.execute('DELETE FROM passkey_challenges WHERE expires_at<=?', (int(time.time()),))
            prior = request.cookies.get(COOKIE)
            if prior:
                db.execute('DELETE FROM passkey_challenges WHERE hash=?', (digest(prior),))
            if db.execute('SELECT COUNT(*) AS n FROM passkey_challenges').fetchone()['n'] >= 5000:
                raise HTTPException(429, 'Please try again later')
            db.execute('INSERT INTO passkey_challenges VALUES (?,?,?,?,?)', (digest(nonce), challenge, kind, user_id, int(time.time())+300))
        response.set_cookie(COOKIE, nonce, max_age=300, secure=True, httponly=True, samesite='strict', path='/')
        return json.loads(options_to_json(options))

    def consume(request, response, kind, user_id=None):
        nonce = request.cookies.get(COOKIE, '')
        if not nonce or len(nonce)>256:
            raise HTTPException(401, 'Start the passkey request again')
        with accounts.connect() as db:
            row = db.execute('DELETE FROM passkey_challenges WHERE hash=? RETURNING challenge,kind,user_id,expires_at', (digest(nonce),)).fetchone()
        response.delete_cookie(COOKIE, secure=True, httponly=True, samesite='strict', path='/')
        if not row or row['kind'] != kind or row['expires_at'] <= int(time.time()) or (user_id is not None and row['user_id'] != user_id):
            raise HTTPException(401, 'Passkey request expired or already used')
        return decode(row['challenge'])

    @app.get('/api/account/passkeys')
    def listing(request: Request):
        user = accounts.identity(request)
        with accounts.connect() as db:
            rows = db.execute('SELECT id,label,created_at FROM passkeys WHERE user_id=? ORDER BY created_at', (user['id'],)).fetchall()
        return {'items': [dict(row) for row in rows]}

    @app.post('/api/account/passkeys/register/options')
    def enroll_options(request: Request, response: Response):
        first_party(request); user = recent(request)
        with accounts.connect() as db:
            rows = db.execute('SELECT id FROM passkeys WHERE user_id=?', (user['id'],)).fetchall()
        if len(rows)>=10:
            raise HTTPException(409, 'Remove an unused passkey first')
        options = generate_registration_options(rp_id=rp_id, rp_name='Work Zone OS', user_id=hashlib.sha256(user['id'].encode()).digest(), user_name=user['email'],
            authenticator_selection=AuthenticatorSelectionCriteria(resident_key=ResidentKeyRequirement.REQUIRED, user_verification=UserVerificationRequirement.REQUIRED),
            exclude_credentials=[PublicKeyCredentialDescriptor(id=decode(row['id'])) for row in rows])
        return issue(request, response, 'register', user['id'], options)

    @app.post('/api/account/passkeys/register/verify')
    def enroll_verify(body: Ceremony, request: Request, response: Response):
        first_party(request); user = recent(request)
        challenge = consume(request, response, 'register', user['id'])
        if len(json.dumps(body.credential))>32768:
            raise HTTPException(413, 'Passkey response too large')
        try:
            result = verify_registration_response(credential=body.credential, expected_challenge=challenge, expected_rp_id=rp_id, expected_origin=origin, require_user_verification=True)
        except Exception:
            raise HTTPException(400, 'Passkey could not be verified') from None
        with accounts.connect() as db:
            inserted = db.execute('INSERT INTO passkeys VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING RETURNING id',
                (encode(result.credential_id),user['id'],encode(result.credential_public_key),result.sign_count,body.label,now())).fetchone()
        if not inserted:
            raise HTTPException(409, 'This passkey is already registered')
        return {'registered': True}

    @app.post('/api/account/passkeys/login/options')
    def login_options(request: Request, response: Response):
        first_party(request)
        return issue(request,response,'login','',generate_authentication_options(rp_id=rp_id,user_verification=UserVerificationRequirement.REQUIRED))

    @app.post('/api/account/passkeys/login/verify')
    def login_verify(body: Ceremony, request: Request, response: Response):
        first_party(request); challenge = consume(request,response,'login')
        credential = body.credential
        if len(json.dumps(credential))>32768:
            raise HTTPException(413, 'Passkey response too large')
        with accounts.connect() as db:
            row = db.execute('SELECT * FROM passkeys WHERE id=?', (str(credential.get('id',''))[:2048],)).fetchone()
        if not row:
            raise HTTPException(401, 'Passkey sign-in failed')
        try:
            if credential.get('response',{}).get('userHandle') != encode(hashlib.sha256(row['user_id'].encode()).digest()):
                raise ValueError('user handle')
            result = verify_authentication_response(credential=credential, expected_challenge=challenge, expected_rp_id=rp_id, expected_origin=origin,
                credential_public_key=decode(row['public_key']), credential_current_sign_count=row['sign_count'], require_user_verification=True)
        except Exception:
            raise HTTPException(401, 'Passkey sign-in failed') from None
        with accounts.connect() as db:
            updated = db.execute('UPDATE passkeys SET sign_count=? WHERE id=? AND sign_count=? RETURNING id', (result.new_sign_count,row['id'],row['sign_count'])).fetchone()
        if not updated:
            raise HTTPException(401, 'Start passkey sign-in again')
        try:
            token = accounts.verify.passkey_token(row['user_id'])
        except Exception:
            raise HTTPException(503, 'Passkey sign-in unavailable; use your password') from None
        response.headers['Cache-Control']='no-store'
        return {'custom_token': token}

    @app.delete('/api/account/passkeys/{credential_id}')
    def remove(credential_id: str, request: Request):
        first_party(request); user = recent(request)
        with accounts.connect() as db:
            removed = db.execute('DELETE FROM passkeys WHERE id=? AND user_id=? RETURNING id',(credential_id,user['id'])).fetchone()
            if not removed:
                raise HTTPException(404,'Passkey not found')
            db.execute('DELETE FROM browser_sessions WHERE user_id=?',(user['id'],))
        return {'removed': True, 'remembered_sessions_revoked': True}
    return True
