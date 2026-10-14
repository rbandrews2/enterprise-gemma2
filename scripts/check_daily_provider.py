"""Operator-only five-minute synthetic Daily room probe; never prints credentials.

Run in authorized Cloud Shell using the test venv. No media is joined, no invitations
are sent. Requires approval for the Daily connection and synthetic room creation.
"""
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.workspace_preview.daily_meetings import DailyProvider


def main():
    result = subprocess.run(['gcloud', 'secrets', 'versions', 'access', '1',
                             '--secret=wzos-v2-daily-api-key', '--project=enterprise-gemma2'],
                            capture_output=True, text=True, timeout=30)
    if result.returncode or not result.stdout.strip():
        print('DAILY_PROVIDER_CHECK_BLOCKED: secret unavailable');return 1
    os.environ.update(WZOS_DAILY_API_KEY=result.stdout.strip(), WZOS_DAILY_DOMAIN='wzos.daily.co',
                      WZOS_DAILY_ENABLED='1')
    result = None
    provider = DailyProvider();name='wzos-'+secrets.token_hex(20);end=int(time.time())+300
    created = False
    try:
        provider.room(name, end, create=True, starts_at=int(time.time())-60);created=True
        provider.token(name, {'organization_id':'synthetic-acceptance','id':'synthetic-admin',
                             'role':'admin','name':'Synthetic WZOS acceptance'}, end)
        print('DAILY_PRIVATE_ROOM_AND_TOKEN_PASS: no media joined')
        provider.close(name)
        print('DAILY_ROOM_EXPIRY_UPDATE_PASS: active-media ejection still requires device test')
        return 0
    except Exception as error:
        print('DAILY_PROVIDER_CHECK_FAIL: '+type(error).__name__)
        return 1
    finally:
        if created:
            try:
                provider.call('DELETE','rooms/'+name)
                print('DAILY_SYNTHETIC_ROOM_REMOVED')
            except Exception:
                print('DAILY_CLEANUP_UNCONFIRMED: synthetic room expires within five minutes')
        os.environ.pop('WZOS_DAILY_API_KEY',None)


if __name__=='__main__':raise SystemExit(main())
