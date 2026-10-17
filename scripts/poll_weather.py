"""One bounded organization weather pass. Schedule only after workload/access review.

Uses existing database/provider environment, never prints credentials or locations.
SMS remains gated by WZOS_WEATHER_SMS_ENABLED and the existing SMS mode/allow-list.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--organization', required=True)
    parser.add_argument('--limit', type=int, default=5, choices=range(1, 6))
    options = parser.parse_args()
    if os.getenv('WZOS_WEATHER_POLLER_ENABLED') != '1':
        raise SystemExit('Weather poller disabled; activate only after deployment/access review.')
    from services.workspace_preview.postgres import PostgreSQLStorage
    from services.workspace_preview.weather import Weather
    from services.workspace_preview.messaging import Messaging
    storage = PostgreSQLStorage(os.environ['WZOS_DATABASE_URL'])
    try:
        def roster(user):
            with storage.connect() as db:
                rows = db.execute('SELECT user_id,role,organization_id FROM memberships WHERE organization_id=? AND active=1', (user['organization_id'],)).fetchall()
            return {r['user_id']: {'id': r['user_id'], 'role': r['role'], 'organization_id': r['organization_id']} for r in rows}
        app = SimpleNamespace(state=SimpleNamespace())
        app.state.messaging = Messaging(app, storage.connect, live_permitted=True)
        service = Weather(app, storage.connect, None, None, None, roster, accounts=True)
        result = service.poll(options.organization, limit=options.limit)
        print('WEATHER_PASS', json.dumps(result, sort_keys=True))
        return 0 if result['unavailable'] == 0 else 1
    finally:
        storage.close()


if __name__ == '__main__':
    raise SystemExit(main())
