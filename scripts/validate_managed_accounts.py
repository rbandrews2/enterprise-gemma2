"""Operator-only acceptance of the named restricted staging service.

Creates synthetic provider users and organizations, never emails them. State holds
short-lived credentials: keep it outside Git and disable fixtures after browser QA.
Requires authorized gcloud, ADC, SQL proxy on loopback 5544 and account dependencies.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit, unquote
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
PROJECT = 'enterprise-gemma2'
SERVICE = 'wzos-v2-accounts'
ORIGIN = 'https://8080-cs-1002772085547-default.cs-us-east1-pkhd.cloudshell.dev'


def gc(*args):
    return subprocess.check_output(['gcloud', *args, '--project=' + PROJECT], text=True).strip()


def main():
    import requests
    import firebase_admin
    from firebase_admin import auth
    from psycopg.conninfo import make_conninfo
    from services.workspace_preview.postgres import PostgreSQLStorage
    from services.workspace_preview.accounts import Accounts

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'resume', 'verify', 'disable'])
    parser.add_argument('--state', required=True, type=Path)
    args = parser.parse_args()
    if os.getenv('K_SERVICE') or os.getenv('FIREBASE_AUTH_EMULATOR_HOST'):
        raise SystemExit('Run only as an operator against real restricted staging')
    if args.action == 'prepare' and args.state.exists():
        raise SystemExit('Use a new state file; existing fixtures will not be overwritten')
    state = {'users': {}, 'orgs': {}} if args.action == 'prepare' else json.loads(args.state.read_text())
    def save():
        # Create private before writing tokens, never temporarily world-readable.
        fd = os.open(args.state, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as f:
            json.dump(state, f)
    app = firebase_admin.initialize_app(options={'projectId': PROJECT})
    raw = gc('secrets', 'versions', 'access', 'latest', '--secret=wzos-v2-staging-database-url')
    u = urlsplit(raw)
    db = PostgreSQLStorage(make_conninfo(host='127.0.0.1', port=5544, dbname='wzos', user=u.username, password=unquote(u.password)))
    try:
        if args.action == 'disable':
            for user in state['users'].values():
                auth.update_user(user['uid'], disabled=True, app=app)
                auth.revoke_refresh_tokens(user['uid'], app=app)
            with db.connect() as c:
                for org in state['orgs'].values():
                    c.execute('UPDATE organizations SET active=0 WHERE id=?', (org,))
            state = {'users': {k: {'uid': v['uid'], 'email': v['email']} for k,v in state['users'].items()}, 'orgs':state['orgs'], 'disabled':True}
            save(); print('Synthetic users disabled, tokens revoked, organizations disabled'); return
        key = gc('secrets', 'versions', 'access', 'latest', '--secret=wzos-v2-staging-auth-web-key')
        url = gc('run', 'services', 'describe', SERVICE, '--region=us-central1', '--format=value(status.url)')
        iam = gc('auth', 'print-identity-token')
        def provider(action, data):
            r = requests.post('https://identitytoolkit.googleapis.com/v1/accounts:' + action, params={'key':key}, json=data, headers={'Referer':ORIGIN+'/'}, timeout=30)
            assert r.status_code == 200, 'Provider request failed: '+str(r.status_code)
            return r.json()
        def call(path, who='admin', org=None, body=None, method='GET', expected=200, token=None, include_iam=True):
            h = {'Authorization':'Bearer '+(token or state['users'][who]['idToken']), 'Origin':ORIGIN}
            if include_iam: h['X-Serverless-Authorization'] = 'Bearer '+iam
            h['X-WZOS-Organization'] = org if org is not None else state['orgs'].get('main','')
            r = requests.request(method, url+path, json=body, headers=h, timeout=40)
            assert r.status_code == expected, path+' expected '+str(expected)+' received '+str(r.status_code)
            return r.json() if r.headers.get('content-type','').startswith('application/json') else {}
        if args.action in ('prepare', 'resume'):
            password = os.environ['WZOS_SYNTHETIC_PASSWORD']
            suffix = uuid4().hex[:10]
            for role in ('admin','member','other','unverified'):
                if role in state['users']:
                    tokens=provider('signInWithPassword',{'email':state['users'][role]['email'],'password':password,'returnSecureToken':True})
                    state['users'][role].update(idToken=tokens['idToken'],refreshToken=tokens['refreshToken']);save()
                    continue
                email = 'wzos-'+role+'-'+suffix+'@example.test'
                user = auth.create_user(email=email, password=password, email_verified=role!='unverified', display_name='Synthetic '+role, app=app)
                state['users'][role]={'uid':user.uid,'email':email};save()
                tokens=provider('signInWithPassword',{'email':email,'password':password,'returnSecureToken':True})
                state['users'][role].update(idToken=tokens['idToken'],refreshToken=tokens['refreshToken']);save()
            accounts=Accounts(db.connect, None)
            for name,who in (('main','admin'),('other','other')):
                if name in state['orgs']:
                    continue
                code=accounts.issue_activation('enterprise',hours=1)
                result=call('/api/account/organizations',who,body={'name':'Synthetic acceptance '+name+' '+suffix,'activation_code':code},method='POST')
                state['orgs'][name]=result['id'];save()
            invite=call('/api/account/invitations',body={'email':state['users']['member']['email'],'role':'member'},method='POST')
            call('/api/account/join','member',body={'token':invite['token']},method='POST')
            print('Synthetic browser identities:', {k:v['email'] for k,v in state['users'].items()})
        call('/api/account',include_iam=False,expected=403)
        call('/api/account',token='invalid-test-token',expected=401)
        call('/api/account','unverified',expected=403)
        admin=call('/api/session');member=call('/api/session','member')
        assert admin['can_manage_team'] is True and member['can_manage_team'] is False
        call('/api/account/members','member',expected=403)
        call('/api/account/members')
        call('/api/session','other',expected=403)
        call('/api/session','other',org=state['orgs']['other'])
        call('/api/account/members/'+state['users']['admin']['uid'],body={'role':'member','active':True},method='PUT',expected=409)
        call('/api/account/invitations','member',body={'email':state['users']['other']['email'],'role':'admin'},method='POST',expected=403)
        r=requests.post('https://securetoken.googleapis.com/v1/token',params={'key':key},data={'grant_type':'refresh_token','refresh_token':state['users']['member']['refreshToken']},headers={'Referer':ORIGIN+'/'},timeout=30)
        assert r.status_code==200, 'Refresh failed: '+str(r.status_code)
        fresh=r.json();state['users']['member'].update(idToken=fresh['id_token'],refreshToken=fresh['refresh_token']);save()
        call('/api/session','member')
        print('PASS: IAM, real sign-in, refresh, verified-email enforcement, admin/member and cross-organization boundaries, last-admin protection')
    finally:
        db.close()
        firebase_admin.delete_app(app)


if __name__ == '__main__':
    main()
