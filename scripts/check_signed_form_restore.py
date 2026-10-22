"""Synthetic API acceptance before/after a disposable PostgreSQL dump/restore.

This is a local database rehearsal, not a Cloud SQL or bucket recovery claim.
No credentials, production data, SMS or model service is used.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from services.workspace_preview.app import create_app
from services.workspace_preview.postgres import PostgreSQLStorage
from services.v2.knowledge.store import Store


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('seed', 'check'))
    parser.add_argument('evidence', type=Path)
    args = parser.parse_args()
    dsn = os.environ['WZOS_TEST_DATABASE_URL']
    # The shell harness supplies only its private Unix-socket disposable database.
    if 'host=/tmp/wzos-pg-restore.' not in dsn or not dsn.startswith('postgresql:///wzos_restore_'):
        raise SystemExit('Use only the disposable restore harness database.')
    os.environ['WZOS_WORKSPACE_PREVIEW'] = '1'
    storage = PostgreSQLStorage(dsn)
    try:
        app = create_app(storage=storage, knowledge_store=Store(args.evidence.parent/'sources', {}))
        with TestClient(app) as client:
            headers = {'X-Preview-Actor': 'enterprise-admin'}
            signature = {'version': 1, 'mode': 'drawn', 'signer_name': 'Synthetic Worker',
                         'strokes': [[{'x': .1, 'y': .2}, {'x': .6, 'y': .8}]]}
            if args.phase == 'seed':
                body = {'request_id': str(uuid4()), 'template_id': 'jsa', 'template_revision': 1,
                        'fields': {'competent_person': 'Synthetic supervisor'}, 'signature': signature}
                response = client.post('/api/form-submissions/completed', headers=headers, json=body)
                assert response.status_code == 200, response.status_code
                item = response.json()
                expected = {'submission_id': item['id'], 'form_hash': digest(item['form']),
                            'signature_hash': digest(signature), 'payload_hash': item['payload_hash']}
                args.evidence.write_text(json.dumps(expected, indent=2))
            else:
                expected = json.loads(args.evidence.read_text())
                response = client.get('/api/form-submissions', headers=headers)
                assert response.status_code == 200
                rows = [row for row in response.json()['items'] if row['id'] == expected['submission_id']]
                assert len(rows) == 1, 'Restored office submission missing or duplicated'
                item = rows[0]
                assert digest(item['form']) == expected['form_hash'], 'Restored form differs'
                assert digest(item['form']['signature']) == expected['signature_hash'], 'Restored signature differs'
                assert item['payload_hash'] == expected['payload_hash']
                assert item['status'] == 'received'
                assert client.get('/api/form-submissions').status_code == 401
                foreign = client.get('/api/form-submissions', headers={'X-Preview-Actor':'core-admin'})
                assert foreign.status_code == 200 and foreign.json()['items'] == []
                expected['restore_verified'] = True
                args.evidence.write_text(json.dumps(expected, indent=2))
            print('SIGNED_FORM_RESTORE_' + args.phase.upper() + '_PASS')
    finally:
        storage.close()


if __name__ == '__main__':
    main()
