"""Read-only staging schema compatibility check; never initializes the live schema.

Run through an already authorized SQL proxy on localhost:5544. Credentials stay
in memory. --offline checks extraction without accessing Google or PostgreSQL.
Missing tables are review candidates, not instructions to create tables (some
definitions are preview-only). Incompatible existing columns block release.
"""
import argparse
import ast
import json
import os
from pathlib import Path
import sqlite3
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def expected_schema():
    db = sqlite3.connect(':memory:')
    try:
        for path in sorted((ROOT / 'services/workspace_preview').glob('*.py')):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    statement = node.value.strip()
                    if statement.upper().startswith('CREATE TABLE IF NOT EXISTS '):
                        db.execute(statement)
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        if not tables:
            raise RuntimeError('No candidate schema extracted')
        return {t: {r[1]: r[2].upper() for r in db.execute('PRAGMA table_info("' + t + '")')}
                for t in sorted(tables)}
    finally:
        db.close()


def compare(expected, actual):
    missing_tables = sorted(set(expected) - set(actual))
    conflicts = []
    compatible = {'TEXT': {'text'}, 'INTEGER': {'integer', 'bigint', 'smallint'},
                  'REAL': {'real', 'double precision', 'numeric'}, 'BLOB': {'bytea'}}
    for table in sorted(set(expected) & set(actual)):
        for column, kind in expected[table].items():
            live = actual[table].get(column)
            if live is None or live not in compatible.get(kind, {kind.lower()}):
                conflicts.append({'table': table, 'column': column,
                                  'expected': kind, 'actual': live})
    return {'missing_tables': missing_tables, 'conflicts': conflicts,
            'compatible_existing_columns': not conflicts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    expected = expected_schema()
    if args.offline:
        print(json.dumps({'expected_tables': sorted(expected), 'count': len(expected)}, indent=2))
        return 0
    if args.output is None or args.output.exists():
        parser.error('Supply a new private --output path')
    import psycopg
    raw = subprocess.check_output(['gcloud', 'secrets', 'versions', 'access', 'latest',
                                  '--secret=wzos-v2-staging-database-url',
                                  '--project=enterprise-gemma2'], text=True).strip()
    parsed = urlsplit(raw)
    with psycopg.connect(host='127.0.0.1', port=5544, dbname='wzos',
                         user=unquote(parsed.username), password=unquote(parsed.password),
                         connect_timeout=10) as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        conn.execute("SET LOCAL statement_timeout='15s'")
        rows = conn.execute("SELECT table_name,column_name,data_type FROM information_schema.columns "
                            "WHERE table_schema='public' ORDER BY table_name,ordinal_position").fetchall()
        actual = {}
        for table, column, kind in rows:
            actual.setdefault(table, {})[column] = kind
        result = compare(expected, actual)
        result['live_tables'] = sorted(actual)
        result['candidate_tables'] = sorted(expected)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))
    return 0 if result['compatible_existing_columns'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
