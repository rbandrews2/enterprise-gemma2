"""Read-only row fingerprints for the restricted staging backup restore drill.

Connect through an operator SQL proxy on 5544 (source) or 5545 (isolated restore).
No row contents or credentials are written to evidence. Compare before disabling
the synthetic acceptance accounts; those mutations intentionally change rows.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, unquote

import psycopg
from psycopg import sql
from validate_managed_accounts import gc


def fingerprint(connection):
    result = {}
    with connection.transaction():
        connection.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        tables = connection.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").fetchall()
        for (table,) in tables:
            rows = connection.execute(sql.SQL('SELECT row_to_json(t)::text FROM {} AS t').format(sql.Identifier('public', table))).fetchall()
            canonical = sorted(json.dumps(json.loads(row[0]), sort_keys=True, separators=(',', ':')) for row in rows)
            digest = hashlib.sha256()
            for row in canonical:
                encoded = row.encode('utf-8')
                digest.update(len(encoded).to_bytes(8, 'big'))
                digest.update(encoded)
            result[table] = {'rows': len(rows), 'sha256': digest.hexdigest()}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, choices=(5544, 5545), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compare', type=Path)
    parser.add_argument('--file-evidence', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Use a new evidence path; existing evidence is preserved')
    raw = gc('secrets', 'versions', 'access', 'latest', '--secret=wzos-v2-staging-database-url')
    parsed = urlsplit(raw)
    with psycopg.connect(host='127.0.0.1', port=args.port, dbname='wzos', user=parsed.username,
                        password=unquote(parsed.password), connect_timeout=10, autocommit=True) as conn:
        result = fingerprint(conn)
        if args.file_evidence:
            file = json.loads(args.file_evidence.read_text())
            row = conn.execute('SELECT organization_id, object_key, sha256, size_bytes FROM workspace_files WHERE id=%s', (file['file_id'],)).fetchone()
            expected = (file['organization_id'], file['object_key'], file['sha256'], file['size_bytes'])
            if row != expected:
                raise SystemExit('FAIL: restored file metadata differs')
            from google.cloud import storage
            from validate_managed_files import BUCKET
            if file['bucket'] != BUCKET:
                raise SystemExit('Unexpected evidence bucket')
            blob = storage.Client(project='enterprise-gemma2').bucket(BUCKET).blob(file['object_key'], generation=int(file['generation']))
            data = blob.download_as_bytes(timeout=30)
            if len(data) != file['size_bytes'] or hashlib.sha256(data).hexdigest() != file['sha256']:
                raise SystemExit('FAIL: preserved object differs from restored metadata')
    if not result:
        raise SystemExit('No application tables found')
    evidence = {'tables': result, 'total_rows': sum(t['rows'] for t in result.values())}
    if args.file_evidence:
        evidence['restored_file_reference_verified'] = True
    if args.compare:
        previous = json.loads(args.compare.read_text())
        if previous['tables'] != result:
            raise SystemExit('FAIL: restored table counts or row fingerprints differ')
        evidence['matches_source'] = True
    args.output.write_text(json.dumps(evidence, indent=2) + '\n')
    print('PASS:', len(result), 'tables;', evidence['total_rows'], 'rows;',
          'restored fingerprints match source' if args.compare else 'source fingerprints preserved')


if __name__ == '__main__':
    main()
