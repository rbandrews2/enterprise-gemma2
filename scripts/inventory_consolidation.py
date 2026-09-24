"""Read-only schema/count inventory for deciding which sample data to recycle.

Never exports account values, tokens, passwords or row payloads. Does not import
or delete data. SQLite reads use a consistent transaction and read-only URI.
"""
from contextlib import closing
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3


def inventory(database):
    database = Path(database).resolve(strict=True)
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
        db.execute('BEGIN')
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
        result = []
        for (name,) in tables:
            quoted = '"' + name.replace('"', '""') + '"'
            result.append({'table': name,
                           'rows': db.execute('SELECT COUNT(*) FROM ' + quoted).fetchone()[0],
                           'columns': [r[1] for r in db.execute('PRAGMA table_info(' + quoted + ')')]})
    return {'database': str(database), 'classification': 'sample-data-review', 'tables': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, action='append', default=[])
    parser.add_argument('--definitions', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.database and not args.definitions:
        parser.error('Provide at least one database or definitions file')
    report = {'format_version': 1, 'mode': 'inventory-only',
              'databases': [inventory(p) for p in args.database]}
    if args.definitions:
        raw = args.definitions.read_bytes()
        definitions = json.loads(raw)
        report['legacy_definitions'] = {
            'sha256': hashlib.sha256(raw).hexdigest(),
            'tables': sorted(r['object_name'] for r in definitions if r['kind'] == 'table'),
            'row_data_available': False}
    # Exclusive output avoids overwriting databases or earlier inventory evidence.
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
