"""Private, tenant-scoped embedded calls. API keys never leave the server."""
import hashlib
import json
import os
import re
import threading
import time
from collections import deque
from datetime import datetime
from uuid import UUID

import httpx
from fastapi import HTTPException, Request


def frame_origins(origin):
    """Exact tenant hosts only; Daily Prebuilt also uses its documented fallbacks."""
    match = re.fullmatch(r'https://([a-z0-9][a-z0-9-]{0,61})[.]daily[.]co', origin)
    if not match:
        return ()
    return tuple('https://' + match[1] + '.' + suffix
                 for suffix in ('daily.co', 'dailywebrtc.com', 'dailywebrtc.net'))


class DailyProvider:
    def __init__(self, transport=None):
        self.key = os.getenv('WZOS_DAILY_API_KEY', '').strip()
        domain = os.getenv('WZOS_DAILY_DOMAIN', '').strip()
        self.origin = 'https://' + domain if re.fullmatch(r'[a-z0-9][a-z0-9-]{0,61}\.daily\.co', domain) else ''
        self.enabled = os.getenv('WZOS_DAILY_ENABLED') == '1' and bool(self.key and self.origin)
        self.transport = transport

    def call(self, method, path, body=None, missing=False):
        if not self.enabled:
            raise HTTPException(503, 'Embedded meetings are awaiting Daily configuration.')
        try:
            with httpx.Client(timeout=httpx.Timeout(15, connect=5), follow_redirects=False,
                              trust_env=False, transport=self.transport) as client:
                with client.stream(method, 'https://api.daily.co/v1/' + path,
                                   headers={'Authorization': 'Bearer ' + self.key}, json=body) as response:
                    if missing and response.status_code == 404:
                        return None
                    if response.status_code not in (200, 201):
                        raise HTTPException(502, 'Meeting provider request was not confirmed. Try again.')
                    data = bytearray()
                    for chunk in response.iter_bytes():
                        if len(data) + len(chunk) > 65536:
                            raise ValueError('Response too large')
                        data.extend(chunk)
            result = json.loads(data)
            if not isinstance(result, dict):
                raise ValueError('Invalid provider response')
            return result
        except (httpx.HTTPError, ValueError, TypeError):
            raise HTTPException(502, 'Meeting provider response was not confirmed. Try again.') from None

    def room(self, name, expires_at, create=False, starts_at=0):
        room = self.call('GET', 'rooms/' + name, missing=True)
        if room is None and create:
            room = self.call('POST', 'rooms', {'name': name, 'privacy': 'private', 'properties': {
                'nbf': starts_at, 'exp': expires_at, 'eject_at_room_exp': True,
                'max_participants': 10, 'enable_prejoin_ui': True,
                'enable_knocking': False,
                'start_video_off': True, 'start_audio_off': True,
                'enable_dialout': False, 'enable_transcription_storage': False}})
        if room is None:
            raise HTTPException(409, 'An admin must start this meeting before members can join.')
        config = room.get('config') if isinstance(room.get('config'), dict) else {}
        if (room.get('name') != name or room.get('privacy') != 'private'
                or room.get('url') != self.origin + '/' + name
                or config.get('exp') != expires_at
                or config.get('enable_knocking') is not False
                or config.get('max_participants') != 10
                or config.get('eject_at_room_exp') is not True):
            raise HTTPException(502, 'Meeting privacy or expiration could not be confirmed.')
        return room

    def token(self, name, user, end):
        result = self.call('POST', 'meeting-tokens', {'properties': {
            'room_name': name, 'exp': min(int(time.time()) + 300, end),
            'is_owner': user['role'] == 'admin', 'user_id': hashlib.sha256(
                (user['organization_id'] + ':' + user['id']).encode()).hexdigest(),
            'user_name': str(user.get('name') or 'WZOS participant')[:100],
            'start_video_off': True, 'start_audio_off': True,
            'enable_recording_ui': False, 'enable_live_captions_ui': False,
            'start_cloud_recording': False, 'auto_start_transcription': False}})
        token = result.get('token')
        if not isinstance(token, str) or not 20 <= len(token) <= 10000:
            raise HTTPException(502, 'Meeting authorization was not confirmed.')
        return token

    def close(self, name):
        # The live API rejects past expirations. Close at the nearest accepted
        # future boundary; WZOS stops issuing tokens immediately after confirmation.
        expires = int(time.time()) + 2
        result = self.call('POST', 'rooms/' + name, {'privacy': 'private', 'properties': {
            'exp': expires, 'eject_at_room_exp': True}})
        config = result.get('config') if isinstance(result.get('config'), dict) else {}
        if (result.get('name') != name or result.get('privacy') != 'private'
                or config.get('exp') != expires
                or config.get('eject_at_room_exp') is not True):
            raise HTTPException(502, 'Ending the active meeting was not confirmed.')


def register(app, connect, actor, provider=None):
    base_actor = actor
    def actor(request):
        user = base_actor(request)
        if user['edition'] != 'enterprise':
            raise HTTPException(403, 'Video meetings require Enterprise.')
        return user
    provider = provider or DailyProvider()
    app.state.daily_meetings = provider
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS daily_meeting_rooms (
          organization_id TEXT NOT NULL,record_id TEXT NOT NULL,record_version INTEGER NOT NULL,
          room_name TEXT NOT NULL,expires_at INTEGER NOT NULL,state TEXT NOT NULL,
          PRIMARY KEY(organization_id,record_id))''')
    lock, history = threading.Lock(), {}

    def limit(user):
        with lock:
            now = time.monotonic()
            for key in list(history):
                while history[key] and history[key][0] < now - 60:
                    history[key].popleft()
                if not history[key]:
                    del history[key]
            for key, cap in [((user['organization_id'], user['id']), 6), ((user['organization_id'],), 30)]:
                if len(history.get(key, ())) >= cap or len(history) > 2000:
                    raise HTTPException(429, 'Too many meeting requests. Try again shortly.')
            for key in [(user['organization_id'], user['id']), (user['organization_id'],)]:
                history.setdefault(key, deque()).append(now)

    def selected(db, user, record_id):
        row = db.execute("SELECT * FROM module_records WHERE organization_id=? AND kind='schedule' AND id=?",
                         (user['organization_id'], str(record_id))).fetchone()
        if not row:
            raise HTTPException(404, 'Meeting not found')
        details = json.loads(row['payload'])
        if details.get('meeting_provider') != 'daily' or details.get('status') == 'cancelled':
            raise HTTPException(409, 'This embedded meeting is not available.')
        if user['role'] != 'admin' and details.get('assignees') and user['id'] not in details['assignees']:
            raise HTTPException(404, 'Meeting not available for this member')
        try:
            start = int(datetime.fromisoformat(details['start']).timestamp())
            end = int(datetime.fromisoformat(details['end']).timestamp())
        except (KeyError, ValueError, TypeError, OverflowError):
            raise HTTPException(409, 'Meeting schedule needs an admin review.') from None
        if not start - 900 <= time.time() < end or not 0 < end - start <= 3600:
            raise HTTPException(409, 'Join within 15 minutes of the scheduled start and before the meeting ends.')
        return row, start, end

    def end_existing(db, org, record_id):
        row = db.execute('SELECT * FROM daily_meeting_rooms WHERE organization_id=? AND record_id=?',
                         (org, str(record_id))).fetchone()
        if row and row['state'] == 'prepared' and row['expires_at'] > time.time():
            provider.close(row['room_name'])
        if row:
            db.execute("UPDATE daily_meeting_rooms SET state='closed' WHERE organization_id=? AND record_id=?",
                       (org, str(record_id)))
    app.state.end_daily_meeting = end_existing

    @app.get('/api/meetings/config')
    def config(request: Request):
        actor(request)
        return {'daily_enabled': provider.enabled, 'daily_origin': provider.origin if provider.enabled else '',
                'max_participants': 10, 'max_duration_minutes': 60}

    @app.post('/api/meetings/{record_id}/prepare')
    def prepare(record_id: UUID, request: Request):
        user = actor(request)
        if user['role'] != 'admin':
            raise HTTPException(403, 'Only admins can start embedded meetings')
        limit(user)
        with connect() as db:
            row, start, end = selected(db, user, record_id)
            version = row['version']
        name = 'wzos-' + hashlib.sha256((user['organization_id'] + ':' + str(record_id)
                                       + ':' + str(version)).encode()).hexdigest()[:40]
        # Network waits do not hold the shared writer lock or block time punches.
        provider.room(name, end, create=True, starts_at=start - 900)
        fresh = actor(request)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current, _, _ = selected(db, fresh, record_id)
            if (any(fresh[k] != user[k] for k in ('id', 'organization_id', 'role'))
                    or current['version'] != version):
                raise HTTPException(409, 'Meeting access changed. Reload before starting.')
            db.execute('''INSERT INTO daily_meeting_rooms VALUES (?,?,?,?,?,?)
              ON CONFLICT(organization_id,record_id) DO UPDATE SET record_version=excluded.record_version,
              room_name=excluded.room_name,expires_at=excluded.expires_at,state=excluded.state''',
                       (user['organization_id'], str(record_id), row['version'], name, end, 'prepared'))
        return {'status': 'prepared'}

    @app.post('/api/meetings/{record_id}/join')
    def join(record_id: UUID, request: Request):
        user = actor(request)
        limit(user)
        with connect() as db:
            row, _, end = selected(db, user, record_id)
            room = db.execute('SELECT * FROM daily_meeting_rooms WHERE organization_id=? AND record_id=?',
                              (user['organization_id'], str(record_id))).fetchone()
            if not room or room['state'] != 'prepared' or room['record_version'] != row['version']:
                raise HTTPException(409, 'An admin must start the current meeting before members can join.')
            version, name = row['version'], room['room_name']
        provider.room(name, end)
        token = provider.token(name, user, end)
        # Fail closed if membership or meeting changed while the provider responded.
        fresh = actor(request)
        if any(fresh[k] != user[k] for k in ('id', 'organization_id', 'role')):
            raise HTTPException(409, 'Meeting access changed. Reload before joining.')
        with connect() as db:
            current, _, _ = selected(db, fresh, record_id)
            available = db.execute('SELECT * FROM daily_meeting_rooms WHERE organization_id=? AND record_id=?',
                                   (fresh['organization_id'], str(record_id))).fetchone()
            if (current['version'] != version or not available or available['state'] != 'prepared'
                    or available['record_version'] != version or available['room_name'] != name):
                raise HTTPException(409, 'Meeting changed. Reload before joining.')
        return {'url': provider.origin + '/' + name, 'token': token, 'expires_at': end}
