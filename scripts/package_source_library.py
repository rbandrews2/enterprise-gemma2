"""Build a verified, rebuildable deployment snapshot from preserved official sources.

No downloads, model calls or review upgrades. Destination must be new. Only
catalog source revisions and their metadata enter the snapshot, never customer data.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.v2.knowledge.store import Store


def verify(destination):
    destination = Path(destination).resolve()
    report = json.loads((destination/'snapshot.json').read_text(encoding='utf-8'))
    for name, digest in report['files'].items():
        path = (destination/name).resolve()
        if destination not in path.parents or not path.is_file():
            raise ValueError('Snapshot path is missing or outside its directory')
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Snapshot file hash mismatch: '+name)
    actual = {p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file()}
    if actual != set(report['files']) | {'snapshot.json'}:
        raise ValueError('Unexpected snapshot files')
    with closing(sqlite3.connect((destination/'index.sqlite').as_uri()+'?mode=ro', uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Snapshot index integrity failure')
    return report


def package(store, destination):
    destination = Path(destination).resolve()
    source = store.data.resolve()
    if destination == source or source in destination.parents or destination in source.parents:
        raise ValueError('Snapshot must be separate from source data')
    destination.mkdir(parents=True, exist_ok=False)
    coverage = []
    for source_id in sorted(store.catalog):
        revisions = store.revisions(source_id)
        coverage.append({'source_id':source_id, 'revisions':len(revisions),
                         'status':revisions[0]['extraction_state'] if revisions else 'missing',
                         'review_status':revisions[0]['review_status'] if revisions else 'unreviewed'})
        for manifest in revisions:
            revision = manifest['revision']
            if len(revision) != 64 or any(c not in '0123456789abcdef' for c in revision):
                raise ValueError('Invalid revision hash')
            folder = source/'revisions'/source_id/revision
            kind = store.catalog[source_id].kind
            original = folder/f'original.{kind}'
            extracted = folder/'extracted.json'
            if hashlib.sha256(original.read_bytes()).hexdigest() != revision:
                raise ValueError('Original document hash mismatch')
            if hashlib.sha256(extracted.read_bytes()).hexdigest() != manifest['extracted_sha256']:
                raise ValueError('Extracted text hash mismatch')
            for name in (original.name, 'extracted.json', 'manifest.json'):
                target = destination/'revisions'/source_id/revision/name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(folder/name, target)
        for section in ('current','attempts'):
            path = source/section/f'{source_id}.json'
            if path.exists():
                target = destination/section/path.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
    snapshot = Store(destination, store.catalog)
    snapshot.rebuild()
    files = {p.relative_to(destination).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(destination.rglob('*')) if p.is_file()}
    report = {'coverage':coverage, 'files':files, 'applicability_verified':False}
    (destination/'snapshot.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--destination', type=Path)
    group.add_argument('--verify', type=Path)
    args = parser.parse_args()
    report = verify(args.verify) if args.verify else package(Store(), args.destination)
    print(json.dumps({'files':len(report['files']), 'coverage':report['coverage']}, indent=2))


if __name__ == '__main__':
    main()
