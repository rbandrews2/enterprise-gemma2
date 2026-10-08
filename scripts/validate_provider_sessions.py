"""Operator-only real Firebase cookie probe; no deployment, email or shared DB.

Creates one disabled-on-exit synthetic identity without organization membership.
Reads the web key from WZOS_AUTH_WEB_API_KEY; never prints credentials. This checks
provider issuance/revocation, not browser cookie transport or device lifecycle.
"""
import argparse
import os
from pathlib import Path
import secrets
import sys
import time
from urllib.parse import urlsplit
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', required=True)
    args = parser.parse_args()
    origin = urlsplit(args.origin)
    if origin.scheme != 'https' or not (origin.hostname or '').endswith('.cloudshell.dev') or origin.username or origin.password or origin.query or origin.fragment:
        raise SystemExit('Use the authorized HTTPS Cloud Shell preview origin')
    if os.getenv('K_SERVICE') or os.getenv('FIREBASE_AUTH_EMULATOR_HOST'):
        raise SystemExit('Run as an operator with real Google credentials')
    key = os.environ.get('WZOS_AUTH_WEB_API_KEY')
    if not key:
        raise SystemExit('WZOS_AUTH_WEB_API_KEY is required')
    import requests
    import firebase_admin
    from firebase_admin import auth
    from datetime import timedelta
    from services.workspace_preview.accounts import FirebaseVerifier
    verifier = FirebaseVerifier('enterprise-gemma2')
    uid = None
    passed = False
    cleaned = False
    try:
        password = secrets.token_urlsafe(36)
        email = 'wzos-session-probe-' + uuid4().hex + '@example.test'
        user = auth.create_user(email=email, password=password, email_verified=True, app=verifier.app)
        uid = user.uid
        response = requests.post('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword',
                                 params={'key': key}, headers={'Referer': args.origin.rstrip('/')+'/'},
                                 json={'email': email, 'password': password, 'returnSecureToken': True}, timeout=30)
        if response.status_code != 200:
            raise RuntimeError('Provider sign-in failed')
        token = response.json()['idToken']
        assert verifier(token)['uid'] == uid
        cookie = verifier.create_session(token, timedelta(days=14))
        assert verifier.verify_session(cookie)['uid'] == uid
        # Firebase revocation timestamps have second precision.
        time.sleep(1.1)
        auth.revoke_refresh_tokens(uid, app=verifier.app)
        try:
            verifier.verify_session(cookie)
        except auth.RevokedSessionCookieError:
            passed = True
        if not passed:
            raise RuntimeError('Revoked cookie remained accepted')
    except Exception as exc:
        print('Provider cookie probe failed: ' + type(exc).__name__, file=sys.stderr)
    finally:
        if uid:
            try:
                auth.update_user(uid, disabled=True, app=verifier.app)
                auth.revoke_refresh_tokens(uid, app=verifier.app)
                cleaned = True
            except Exception:
                print('ACTION REQUIRED: disable synthetic identity UID ' + uid, file=sys.stderr)
        else:
            cleaned = True
        firebase_admin.delete_app(verifier.app)
    if passed and cleaned:
        print('PASS: real ID token, 14-day session issuance, verification and revocation; synthetic user disabled. Browser lifecycle remains unverified.')
        return 0
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
