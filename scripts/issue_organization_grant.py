"""Operator-only email-bound entitlement; no password, message, or account creation.

Requires the already-deployed additive schema and an authorized SQL proxy.
Credentials are read into memory from the existing database secret version 1.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import subprocess
from urllib.parse import unquote, urlsplit
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--email', required=True)
    parser.add_argument('--edition', choices=['core', 'enterprise'], required=True)
    parser.add_argument('--seats', type=int, required=True)
    args = parser.parse_args()
    email = args.email.strip().lower()
    if '@' not in email or not 1 <= args.seats <= 100000:
        parser.error('Valid email and seat allowance required')
    import psycopg
    raw = subprocess.check_output(['gcloud', 'secrets', 'versions', 'access', '1',
        '--secret=wzos-v2-staging-database-url', '--project=enterprise-gemma2'], text=True).strip()
    parsed = urlsplit(raw)
    with psycopg.connect(host='127.0.0.1', port=5544, dbname='wzos',
                        user=unquote(parsed.username), password=unquote(parsed.password),
                        connect_timeout=10) as conn:
        conn.execute("SET LOCAL statement_timeout='15s'")
        conn.execute('LOCK TABLE organization_creation_grants IN SHARE ROW EXCLUSIVE MODE')
        rows = conn.execute('SELECT id,edition,seat_limit,expires_at,organization_id FROM organization_creation_grants WHERE email=%s', (email,)).fetchall()
        now = datetime.now(timezone.utc)
        for row in rows:
            if row[4] or row[3] > now.isoformat():
                if (row[1], row[2]) != (args.edition, args.seats):
                    raise RuntimeError('Existing grant differs; review before changing entitlement')
                print(json.dumps({'id':row[0], 'edition':row[1], 'seats':row[2],
                                  'expires_at':row[3], 'already_used':bool(row[4]), 'reused':True}))
                return
        grant_id = str(uuid4()); expires = (now + timedelta(days=7)).isoformat()
        conn.execute('INSERT INTO organization_creation_grants VALUES (%s,%s,%s,%s,%s,NULL,NULL)',
                     (grant_id, email, args.edition, args.seats, expires))
    print(json.dumps({'id':grant_id,'edition':args.edition,'seats':args.seats,'expires_at':expires,'reused':False}))


if __name__ == '__main__':
    main()
