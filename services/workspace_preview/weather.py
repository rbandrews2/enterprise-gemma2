"""Timestamped NWS weather, tenant-scoped job monitoring and recipient receipts.

No generated weather, attendance mutation, background device tracking or LLM calls.
"""
import hashlib
import json
import math
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

import httpx
from fastapi import BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

DDL = (
    'CREATE TABLE IF NOT EXISTS weather_sites (organization_id TEXT NOT NULL,order_id TEXT NOT NULL,version INTEGER NOT NULL,payload TEXT NOT NULL,author_id TEXT NOT NULL,updated_at TEXT NOT NULL,last_checked_at TEXT NOT NULL DEFAULT \'\',PRIMARY KEY(organization_id,order_id))',
    'CREATE TABLE IF NOT EXISTS weather_alerts (organization_id TEXT NOT NULL,order_id TEXT NOT NULL,alert_id TEXT NOT NULL,revision TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(organization_id,order_id,alert_id))',
    'CREATE TABLE IF NOT EXISTS weather_receipts (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,order_id TEXT NOT NULL,recipient_id TEXT NOT NULL,alert_id TEXT NOT NULL,revision TEXT NOT NULL,body TEXT NOT NULL,created_at TEXT NOT NULL,acknowledged_at TEXT)',
    'CREATE INDEX IF NOT EXISTS weather_recipient ON weather_receipts(organization_id,recipient_id,created_at)',
)


def now():
    return datetime.now(timezone.utc)


def instant(value):
    try:
        result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except (ValueError, TypeError, OverflowError):
        return None


class Point(BaseModel):
    model_config = ConfigDict(extra='forbid')
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False, strict=True)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False, strict=True)


class Site(Point):
    expected_version: int = Field(ge=0, strict=True)
    radius_meters: int = Field(default=350, ge=50, le=2000, strict=True)
    monitoring: bool = False
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @model_validator(mode='after')
    def window(self):
        if self.monitoring:
            if not self.starts_at or not self.ends_at or not self.starts_at.tzinfo or not self.ends_at.tzinfo:
                raise ValueError('Monitoring requires a timezone-aware start and finish')
            if not timedelta(0) < self.ends_at - self.starts_at <= timedelta(days=7):
                raise ValueError('Monitoring window must be positive and at most seven days')
        return self


def value(data, key, convert=lambda x, unit: x):
    part = data.get(key) or {}
    number = part.get('value') if isinstance(part, dict) else None
    if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
        return None
    result = convert(number, part.get('unitCode'))
    return round(result, 1) if result is not None and math.isfinite(result) else None


def wind(x, unit):
    return x * {'wmoUnit:km_h-1': .621371, 'wmoUnit:m_s-1': 2.23694, 'wmoUnit:mi_h-1': 1}.get(unit, 0) if unit in ('wmoUnit:km_h-1', 'wmoUnit:m_s-1', 'wmoUnit:mi_h-1') else None


def alerts_normalized(features):
    result = []
    for feature in features[:100]:
        p = feature.get('properties') if isinstance(feature, dict) else None
        if not isinstance(p, dict) or p.get('status') != 'Actual' or p.get('scope') != 'Public':
            continue
        aid, expiry = p.get('id') or feature.get('id'), instant(p.get('expires'))
        effective = instant(p.get('effective')) or instant(p.get('sent'))
        if not isinstance(aid, str) or not 1 <= len(aid) <= 512 or not expiry or expiry <= now() or not effective or effective > now():
            continue
        result.append({'id': aid, 'event': str(p.get('event') or 'Weather alert')[:150],
                       'headline': str(p.get('headline') or p.get('event') or 'Weather alert')[:500],
                       'description': str(p.get('description') or '')[:4000],
                       'instruction': str(p.get('instruction') or '')[:4000],
                       'severity': p.get('severity') if p.get('severity') in ('Extreme', 'Severe', 'Moderate', 'Minor') else 'Unknown',
                       'sent': p.get('sent'), 'effective': effective.isoformat(), 'expires': expiry.isoformat(),
                       'active': True, 'source': 'National Weather Service'})
    return result


class NWS:
    """Bounded host-only transport with a small shared cache, including outage backoff."""
    def __init__(self, transport=None):
        self.transport, self.cache, self.failures = transport, {}, {}
        self.lock = threading.Lock()
        self.slots = threading.BoundedSemaphore(4)

    def get(self, client, url):
        parts = urlsplit(url)
        if parts.scheme != 'https' or parts.netloc != 'api.weather.gov' or parts.fragment:
            raise ValueError('Unexpected provider URL')
        with client.stream('GET', url) as response:
            response.raise_for_status()
            body = bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body) > 524288:
                    raise ValueError('Weather response too large')
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError('Invalid weather response')
        return data

    def current(self, latitude, longitude):
        key = (round(latitude, 4), round(longitude, 4))
        with self.lock:
            saved = self.cache.get(key)
            if saved and time.monotonic() - saved[0] < 60:
                return saved[1]
            failed = self.failures.get(key, 0)
            if time.monotonic() - failed < 60:
                return {**saved[1], 'status': 'stale'} if saved else {'status': 'unavailable', 'alerts': [], 'source': 'National Weather Service'}
        if not self.slots.acquire(blocking=False):
            raise HTTPException(429, 'Weather is busy. Try again shortly.')
        try:
            with httpx.Client(transport=self.transport, timeout=8, follow_redirects=False,
                              headers={'User-Agent': '(workzoneos.org, WZOS weather)', 'Accept': 'application/geo+json'}) as client:
                base = 'https://api.weather.gov'
                meta = self.get(client, f'{base}/points/{key[0]},{key[1]}')['properties']
                locality = meta.get('relativeLocation', {}).get('properties', {})
                try:
                    forecast = self.get(client, meta['forecastHourly'])['properties']
                except (httpx.HTTPError, ValueError, KeyError, TypeError):
                    forecast = {}
                periods = forecast.get('periods') or []
                if not isinstance(periods, list):
                    periods = []
                period = next((p for p in periods if isinstance(p, dict) and instant(p.get('startTime')) and instant(p.get('endTime')) and instant(p['startTime']) <= now() < instant(p['endTime'])), {})
                raw = self.get(client, f'{base}/alerts/active?point={key[0]},{key[1]}')
                if not isinstance(raw.get('features'), list):
                    raise ValueError('Invalid alerts')
                result = {'status': 'ready', 'source': 'National Weather Service', 'basis': 'forecast',
                          'location': ', '.join(str(locality.get(k) or '') for k in ('city', 'state')).strip(', ') or 'Selected location',
                          'latitude': key[0], 'longitude': key[1], 'fetched_at': now().isoformat(),
                          'source_time': forecast.get('updateTime'), 'temperature_f': period.get('temperature') if period.get('temperatureUnit') == 'F' else None,
                          'condition': str(period.get('shortForecast') or 'Conditions unavailable')[:180],
                          'feels_like_f': None, 'humidity_percent': value(period, 'relativeHumidity'),
                          'wind_mph': None, 'gust_mph': None, 'precipitation_inches': None,
                          'wind_text': str(period.get('windSpeed') or '')[:64],
                          'alerts': alerts_normalized(raw['features'])}
                # Observation failure must not discard successfully retrieved official alerts.
                try:
                    stations = self.get(client, meta['observationStations']).get('features') or []
                    observation = self.get(client, stations[0]['id'].rstrip('/') + '/observations/latest')['properties']
                    observed = instant(observation.get('timestamp'))
                    if observed and timedelta(0) <= now() - observed < timedelta(hours=1):
                        result.update(basis='observation', wind_text='', source_time=observed.isoformat(),
                                      condition=str(observation.get('textDescription') or result['condition'])[:180],
                                      temperature_f=value(observation, 'temperature', lambda x,u: x * 9/5 + 32 if u == 'wmoUnit:degC' else None),
                                      feels_like_f=value(observation, 'heatIndex', lambda x,u: x * 9/5 + 32 if u == 'wmoUnit:degC' else None),
                                      humidity_percent=value(observation, 'relativeHumidity'),
                                      wind_mph=value(observation, 'windSpeed', wind), gust_mph=value(observation, 'windGust', wind),
                                      precipitation_inches=value(observation, 'precipitationLastHour', lambda x,u: x / 25.4 if u == 'wmoUnit:mm' else None))
                except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError, AttributeError):
                    pass
            with self.lock:
                if len(self.cache) >= 256:
                    self.cache.pop(next(iter(self.cache)))
                self.cache[key] = (time.monotonic(), result)
                self.failures.pop(key, None)
            return result
        except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError, AttributeError):
            with self.lock:
                if len(self.failures) >= 256:
                    self.failures.pop(next(iter(self.failures)))
                self.failures[key] = time.monotonic()
            return {**saved[1], 'status': 'stale'} if saved else {'status': 'unavailable', 'alerts': [], 'source': 'National Weather Service'}
        finally:
            self.slots.release()


def eligible(db, site, uid, *, accounts):
    org, oid = site['organization_id'], site['order_id']
    if not accounts:
        return True
    member = db.execute('SELECT m.role FROM memberships m JOIN organizations o ON o.id=m.organization_id WHERE m.organization_id=? AND m.user_id=? AND m.active=1 AND o.active=1', (org, uid)).fetchone()
    if not member:
        return False
    order = db.execute('SELECT owner_id FROM preview_orders WHERE id=? AND organization_id=?', (oid, org)).fetchone()
    if not order:
        return False
    if member['role'] == 'admin' or order['owner_id'] == uid:
        return True
    assigned = db.execute("SELECT a.starts_at,a.ends_at FROM dispatch_assignments a JOIN dispatch_plans p ON p.id=a.plan_id AND p.organization_id=a.organization_id JOIN organizations o ON o.id=a.organization_id WHERE o.edition='enterprise' AND a.organization_id=? AND a.order_id=? AND a.user_id=? AND a.status IN ('sent','accepted') AND p.status='sent'", (org, oid, uid)).fetchall()
    settings = db.execute('SELECT payload FROM weather_sites WHERE organization_id=? AND order_id=?', (org, oid)).fetchone()
    config = json.loads(settings['payload']) if settings else {}
    start, end = instant(config.get('starts_at')), instant(config.get('ends_at'))
    return any(not start or not end or (instant(a['starts_at']) < end and instant(a['ends_at']) > start) for a in assigned)


def sms_blocker(db, row):
    if os.getenv('WZOS_WEATHER_SMS_ENABLED') != '1':
        return 'weather_sms_disabled'
    receipt = db.execute('SELECT * FROM weather_receipts WHERE id=? AND organization_id=? AND recipient_id=?', (row['reference_id'], row['organization_id'], row['recipient_id'])).fetchone()
    if not receipt:
        return 'weather_notice_unavailable'
    site = db.execute('SELECT * FROM weather_sites WHERE organization_id=? AND order_id=?', (row['organization_id'], receipt['order_id'])).fetchone()
    alert = db.execute('SELECT * FROM weather_alerts WHERE organization_id=? AND order_id=? AND alert_id=?', (row['organization_id'], receipt['order_id'], receipt['alert_id'])).fetchone()
    if not site or site['author_id'] != row['created_by'] or not alert or alert['revision'] != receipt['revision'] or not eligible(db, site, row['recipient_id'], accounts=True):
        return 'weather_notice_superseded'
    data, hazard = json.loads(site['payload']), json.loads(alert['payload'])
    if not data['monitoring'] or not (instant(data['starts_at']) <= now() < instant(data['ends_at'])):
        return 'weather_monitor_inactive'
    if hazard['active'] and instant(hazard['expires']) <= now():
        return 'weather_alert_expired'
    return None


class Weather:
    def __init__(self, app, connect, actor, jobs, order, roster, accounts):
        self.app, self.connect, self.actor, self.jobs, self.order, self.roster, self.accounts = app, connect, actor, jobs, order, roster, accounts
        self.provider, self.rate, self.lock = NWS(), {}, threading.Lock()
        with connect() as db:
            for sql in DDL:
                db.execute(sql)

    def current(self, point, user):
        key = (user['organization_id'], user['id'])
        with self.lock:
            if len(self.rate) > 2000:
                self.rate = {k:v for k,v in self.rate.items() if time.monotonic() - v < 10}
            if time.monotonic() - self.rate.get(key, -100) < 10:
                raise HTTPException(429, 'Wait a few seconds before refreshing weather.')
            self.rate[key] = time.monotonic()
        return self.provider.current(point.latitude, point.longitude)

    def poll(self, org=None, limit=5):
        """One bounded pass; external scheduler required for closed-app monitoring."""
        with self.connect() as db:
            rows = db.execute('SELECT * FROM weather_sites' + (' WHERE organization_id=?' if org else '') + ' ORDER BY last_checked_at,order_id LIMIT 1000', [*([org] if org else [])]).fetchall()
        result = {'checked': 0, 'unavailable': 0, 'notices': 0}
        queued, deadline = [], time.monotonic() + 120
        for site in rows:
            config = json.loads(site['payload'])
            if not config['monitoring'] or not instant(config.get('starts_at')) or not instant(config.get('ends_at')) or not (instant(config['starts_at']) <= now() < instant(config['ends_at'])):
                continue
            if result['checked'] >= limit or time.monotonic() >= deadline:
                break
            weather = self.provider.current(config['latitude'], config['longitude'])
            result['checked'] += 1
            with self.connect() as db:
                db.execute('UPDATE weather_sites SET last_checked_at=? WHERE organization_id=? AND order_id=?', (now().isoformat(), site['organization_id'], site['order_id']))
            if weather['status'] != 'ready':
                result['unavailable'] += 1
                continue
            orgid, oid = site['organization_id'], site['order_id']
            with self.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                current = db.execute('SELECT * FROM weather_sites WHERE organization_id=? AND order_id=?', (orgid, oid)).fetchone()
                if not current or current['version'] != site['version']:
                    continue
                if self.accounts:
                    admin = db.execute("SELECT 1 FROM memberships WHERE organization_id=? AND user_id=? AND active=1 AND role='admin'", (orgid, site['author_id'])).fetchone()
                    if not admin:
                        continue
                record = db.execute('SELECT payload FROM preview_orders WHERE organization_id=? AND id=?', (orgid, oid)).fetchone()
                if not record:
                    continue
                title = json.loads(record['payload'])['title']
                prior = {r['alert_id']: json.loads(r['payload']) for r in db.execute('SELECT * FROM weather_alerts WHERE organization_id=? AND order_id=?', (orgid, oid)).fetchall()}
                incoming = {a['id']: a for a in weather['alerts'] if instant(a.get('expires')) and instant(a['expires']) > now()}
                for aid, old in prior.items():
                    if aid not in incoming and old.get('active'):
                        incoming[aid] = {**old, 'active': False, 'headline': 'No longer active: ' + old['event']}
                recipients = self.roster({'organization_id': orgid})
                for aid, hazard in incoming.items():
                    revision = hashlib.sha256(json.dumps(hazard, sort_keys=True).encode()).hexdigest()
                    db.execute('INSERT INTO weather_alerts VALUES (?,?,?,?,?) ON CONFLICT(organization_id,order_id,alert_id) DO UPDATE SET revision=excluded.revision,payload=excluded.payload', (orgid, oid, aid, revision, json.dumps(hazard)))
                    for uid, person in recipients.items():
                        if person.get('organization_id') != orgid or not eligible(db, site, uid, accounts=self.accounts):
                            continue
                        rid = hashlib.sha256(json.dumps([orgid, oid, aid, revision, uid]).encode()).hexdigest()
                        body = f"Atlas weather alert - {title}: {hazard['headline']}. NWS; valid until {hazard['expires']}. Open My jobs or Weather for details."
                        inserted = db.execute('INSERT INTO weather_receipts VALUES (?,?,?,?,?,?,?,?,NULL) ON CONFLICT DO NOTHING', (rid, orgid, oid, uid, aid, revision, body, now().isoformat()))
                        if not inserted.rowcount:
                            continue
                        result['notices'] += 1
                        db.execute('INSERT INTO fixture_messages VALUES (?,?,?,?,?,?)', (rid, orgid, site['author_id'], uid, body, now().isoformat()))
                        db.execute('INSERT INTO message_receipts VALUES (?,?,?,?,?)', (orgid, rid, uid, 1, None))
                        messaging = getattr(self.app.state, 'messaging', None)
                        if messaging and os.getenv('WZOS_WEATHER_SMS_ENABLED') == '1':
                            text = messaging.enqueue(db, organization_id=orgid, recipient_id=uid, body=body[:1200] + ' Reply STOP to opt out.', purpose='weather', reference_id=rid, actor_id=site['author_id'])
                            if text['status'] == 'queued':
                                queued.append(text['id'])
        messaging = getattr(self.app.state, 'messaging', None)
        if messaging and os.getenv('WZOS_WEATHER_SMS_ENABLED') == '1':
            with self.connect() as db:
                pending = db.execute("SELECT id FROM sms_outbox WHERE purpose='weather' AND status='queued'" + (' AND organization_id=?' if org else '') + ' ORDER BY created_at,id LIMIT 100', [org] if org else []).fetchall()
            if pending:
                messaging.process(ids=[r['id'] for r in pending], limit=100)
        return result


def register(app, connect, actor, jobs, order, roster, *, accounts=False):
    service = Weather(app, connect, actor, jobs, order, roster, accounts)
    app.state.weather = service

    @app.post('/api/weather/current')
    def current(body: Point, request: Request):
        return service.current(body, actor(request))

    @app.get('/api/weather/sites')
    def sites(request: Request):
        user = actor(request)
        with connect() as db:
            allowed = {j['id']: j for j in jobs(db, user)}
            rows = db.execute('SELECT * FROM weather_sites WHERE organization_id=?', (user['organization_id'],)).fetchall()
        return {'items': [{'order_id': r['order_id'], 'title': allowed[r['order_id']]['title'], 'version': r['version'], **json.loads(r['payload'])} for r in rows if r['order_id'] in allowed]}

    @app.put('/api/weather/sites/{order_id}')
    def save(order_id: str, body: Site, request: Request):
        user = actor(request)
        if user['role'] != 'admin':
            raise HTTPException(403, 'Only admins configure weather and arrival sites')
        if body.monitoring and body.ends_at <= now():
            raise HTTPException(422, 'Choose a future monitoring finish')
        payload = body.model_dump(mode='json', exclude={'expected_version'})
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            order(db, order_id, user)
            previous = db.execute('SELECT version FROM weather_sites WHERE organization_id=? AND order_id=?', (user['organization_id'], order_id)).fetchone()
            if not previous and db.execute('SELECT COUNT(*) AS count FROM weather_sites WHERE organization_id=?', (user['organization_id'],)).fetchone()['count'] >= 100:
                raise HTTPException(409, 'This organization has reached its 100 configured-site limit')
            if (previous['version'] if previous else 0) != body.expected_version:
                raise HTTPException(409, 'Site settings changed. Refresh before saving.')
            version = body.expected_version + 1
            db.execute('INSERT INTO weather_sites (organization_id,order_id,version,payload,author_id,updated_at) VALUES (?,?,?,?,?,?) ON CONFLICT(organization_id,order_id) DO UPDATE SET version=excluded.version,payload=excluded.payload,author_id=excluded.author_id,updated_at=excluded.updated_at', (user['organization_id'], order_id, version, json.dumps(payload), user['id'], now().isoformat()))
        return {'order_id': order_id, 'version': version, **payload}

    @app.post('/api/weather/poll')
    def poll(request: Request, background: BackgroundTasks):
        user = actor(request)
        if user['role'] != 'admin':
            raise HTTPException(403, 'Only admins request job weather checks')
        # Bounded, authenticated manual pass; not an unauthenticated cron endpoint.
        with service.lock:
            key = ('poll', user['organization_id'])
            if time.monotonic() - service.rate.get(key, -100) < 60:
                raise HTTPException(429, 'Job weather was checked recently. Wait one minute.')
            service.rate[key] = time.monotonic()
        background.add_task(service.poll, user['organization_id'])
        return {'status': 'scheduled', 'background_monitoring': os.getenv('WZOS_WEATHER_BACKGROUND_ENABLED') == '1'}

    @app.get('/api/weather/notices')
    def notices(request: Request):
        user = actor(request)
        with connect() as db:
            rows = db.execute('SELECT r.*,a.payload,a.revision AS current_revision FROM weather_receipts r JOIN weather_alerts a ON a.organization_id=r.organization_id AND a.order_id=r.order_id AND a.alert_id=r.alert_id WHERE r.organization_id=? AND r.recipient_id=? ORDER BY r.created_at DESC,r.id DESC LIMIT 100', (user['organization_id'], user['id'])).fetchall()
            result = []
            for row in rows:
                site = {'organization_id': user['organization_id'], 'order_id': row['order_id']}
                if eligible(db, site, user['id'], accounts=accounts):
                    result.append({**dict(row), 'alert': json.loads(row['payload']), 'superseded': row['revision'] != row['current_revision']})
        return {'items': [{k:v for k,v in r.items() if k != 'payload'} for r in result], 'sms_enabled': os.getenv('WZOS_WEATHER_SMS_ENABLED') == '1', 'background_monitoring': os.getenv('WZOS_WEATHER_BACKGROUND_ENABLED') == '1'}

    @app.post('/api/weather/notices/{notice_id}/ack')
    def acknowledge(notice_id: str, request: Request):
        user = actor(request)
        with connect() as db:
            row = db.execute('SELECT * FROM weather_receipts WHERE id=? AND organization_id=? AND recipient_id=?', (notice_id, user['organization_id'], user['id'])).fetchone()
            if not row or not eligible(db, row, user['id'], accounts=accounts):
                raise HTTPException(404, 'Weather notice unavailable')
            stamp = now().isoformat()
            db.execute('UPDATE weather_receipts SET acknowledged_at=COALESCE(acknowledged_at,?) WHERE id=?', (stamp, notice_id))
            db.execute('UPDATE message_receipts SET acknowledged_at=COALESCE(acknowledged_at,?) WHERE message_id=? AND recipient_id=?', (stamp, notice_id, user['id']))
        return {'acknowledged': True}
