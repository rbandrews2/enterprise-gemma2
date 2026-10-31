"""Approved-only one-shot database provisioning; credentials never printed.

Requires explicit approval for a temporary instance-wide SQL administrator.
Run in authenticated Cloud Shell with SQL proxy listening on localhost:5546.
The temporary login expires after one hour and is deleted in finally.
"""
import argparse
import json
import secrets
import subprocess
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

PROJECT = 'enterprise-gemma2'
INSTANCE = 'wzos-v2-staging-db'
DATABASE = 'wzos_checkout_acceptance'
ADMIN = 'wzos_checkout_setup_20261031'
RUNTIME = 'wzos_checkout_test'
SECRET = 'wzos-checkout-acceptance-database-url'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--approved-temporary-admin', action='store_true', required=True)
    parser.parse_args()
    token = subprocess.run(['gcloud','auth','print-access-token'], capture_output=True,
                           text=True, check=True).stdout.strip()
    base = f'https://sqladmin.googleapis.com/sql/v1beta4/projects/{PROJECT}'

    def api(method, path, body=None):
        request = urllib.request.Request(base+path, method=method,
            headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},
            data=json.dumps(body).encode() if body is not None else None)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    def wait(operation):
        for _ in range(90):
            result = api('GET','/operations/'+operation['name'])
            if result.get('status') == 'DONE':
                if result.get('error'): raise RuntimeError('Cloud SQL operation failed')
                return
            time.sleep(2)
        raise RuntimeError('Cloud SQL operation timed out')

    users = api('GET',f'/instances/{INSTANCE}/users').get('items',[])
    if any(user['name'] in (ADMIN,RUNTIME) for user in users):
        raise RuntimeError('Setup or runtime user already exists; inspect before retry')
    exists = subprocess.run(['gcloud','secrets','describe',SECRET,'--project='+PROJECT],
                            capture_output=True).returncode == 0
    if exists: raise RuntimeError('Database secret already exists; inspect before retry')
    admin_password = secrets.token_urlsafe(48)
    runtime_password = secrets.token_urlsafe(48)
    created = False
    try:
        operation = api('POST',f'/instances/{INSTANCE}/users',{
            'name':ADMIN, 'type':'BUILT_IN', 'password':admin_password,
            'passwordPolicy':{'passwordExpirationDuration':'3600s'}})
        created = True
        wait(operation)
        with psycopg.connect(host='127.0.0.1',port=5546,dbname=DATABASE,user=ADMIN,
                             password=admin_password,connect_timeout=15) as db:
            expiry=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
            db.execute(sql.SQL('ALTER ROLE {} VALID UNTIL {}').format(sql.Identifier(ADMIN),sql.Literal(expiry)))
            db.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION').format(
                sql.Identifier(RUNTIME),sql.Literal(runtime_password)))
            db.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC').format(sql.Identifier(DATABASE)))
            db.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(DATABASE),sql.Identifier(RUNTIME)))
            db.execute(sql.SQL('GRANT USAGE,CREATE ON SCHEMA public TO {}').format(sql.Identifier(RUNTIME)))
        with psycopg.connect(host='127.0.0.1',port=5546,dbname=DATABASE,user=RUNTIME,
                             password=runtime_password,connect_timeout=15) as db:
            flags=db.execute('select rolsuper,rolcreatedb,rolcreaterole,rolreplication from pg_roles where rolname=current_user').fetchone()
            if any(flags): raise RuntimeError('Runtime SQL privileges too broad')
            db.execute('CREATE TABLE acceptance_permission_probe (id integer)')
            db.execute('DROP TABLE acceptance_permission_probe')
        dsn=make_conninfo(dbname=DATABASE,user=RUNTIME,password=runtime_password,
            host=f'/cloudsql/{PROJECT}:us-central1:{INSTANCE}')
        result=subprocess.run(['gcloud','secrets','create',SECRET,'--project='+PROJECT,
            '--replication-policy=automatic','--data-file=-'],input=dsn,text=True,capture_output=True)
        if result.returncode: raise RuntimeError('Could not persist test database configuration')
        print('RESTRICTED_TEST_DATABASE_LOGIN_READY')
    finally:
        if created:
            wait(api('DELETE',f'/instances/{INSTANCE}/users?name={ADMIN}'))
            remaining=api('GET',f'/instances/{INSTANCE}/users').get('items',[])
            if any(user['name']==ADMIN for user in remaining):
                raise RuntimeError('Temporary SQL administrator cleanup not verified')
            print('TEMPORARY_SQL_ADMIN_REMOVED')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Never print database exceptions/HTTP bodies that might contain secrets.
        print('SETUP_FAILED',type(error).__name__)
        raise SystemExit(1)
