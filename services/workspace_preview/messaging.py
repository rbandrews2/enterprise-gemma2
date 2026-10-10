"""Organization-scoped SMS consent, delivery outbox, signed provider callbacks and receipts.

Provider acceptance, carrier delivery and employee acknowledgement are separate records.
Members enable SMS for their own verified number; admins cannot opt anyone in. Sending is
off unless WZOS_SMS_MODE is test (allow-listed numbers only) or live (account workspace only).
An ambiguous provider request is never resent without an admin accepting duplicate risk.
"""
import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal
from urllib.parse import parse_qsl
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from . import sms_provider

CONSENT_VERSION = '2026-10-09'
CONSENT_TEXT = ('I agree to receive work-related text messages from my organization through WZOS powered by '
                'Atlas AI Assistant at this number. Message frequency varies. Message and data rates may apply. '
                'Reply STOP to opt out or HELP for help.')
PHONE = r'^\+[1-9][0-9]{7,14}$'
MAX_ATTEMPTS = 4
LEASE_SECONDS = 60
CODE_MINUTES = 10
CODES_PER_DAY = 5
STOP_WORDS = {'STOP', 'STOPALL', 'UNSUBSCRIBE', 'CANCEL', 'END', 'QUIT', 'REVOKE', 'OPTOUT'}
START_WORDS = {'START', 'UNSTOP'}

DDL = (
    'CREATE TABLE IF NOT EXISTS message_receipts (organization_id TEXT NOT NULL,message_id TEXT NOT NULL,recipient_id TEXT NOT NULL,ack_required INTEGER NOT NULL,acknowledged_at TEXT,PRIMARY KEY(message_id,recipient_id))',
    'CREATE TABLE IF NOT EXISTS sms_contacts (organization_id TEXT NOT NULL,user_id TEXT NOT NULL,phone TEXT NOT NULL,status TEXT NOT NULL,consent_version TEXT NOT NULL,consented_at TEXT NOT NULL,verified_at TEXT,opted_out_at TEXT,code_hash TEXT,code_expires_at TEXT,code_attempts INTEGER NOT NULL,codes_day TEXT NOT NULL,codes_sent INTEGER NOT NULL,version INTEGER NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(organization_id,user_id))',
    'CREATE TABLE IF NOT EXISTS sms_outbox (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,purpose TEXT NOT NULL,reference_id TEXT NOT NULL,recipient_id TEXT NOT NULL,phone TEXT NOT NULL,body TEXT NOT NULL,status TEXT NOT NULL,reason TEXT NOT NULL,attempts INTEGER NOT NULL,next_attempt_at TEXT NOT NULL,lease_until TEXT,provider_sid TEXT UNIQUE,provider_status TEXT,error_code TEXT,created_by TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(organization_id,purpose,reference_id,recipient_id))',
    'CREATE TABLE IF NOT EXISTS sms_events (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,outbox_id TEXT,source TEXT NOT NULL,event TEXT NOT NULL,detail TEXT NOT NULL,actor_id TEXT,occurred_at TEXT NOT NULL)',
)

# Delivery states only move forward; provider callbacks can arrive out of order.
RANK = {'queued': 0, 'sending': 1, 'ambiguous': 1, 'accepted': 2, 'sent': 3, 'delivered': 4, 'undelivered': 4, 'failed': 4}
PROVIDER_STATUS = {'accepted': 'accepted', 'queued': 'accepted', 'scheduled': 'accepted', 'sending': 'accepted',
                   'sent': 'sent', 'delivered': 'delivered', 'read': 'delivered', 'undelivered': 'undelivered',
                   'failed': 'failed', 'canceled': 'failed'}
REASONS = {
    'sms_disabled': 'Text messaging is turned off for this environment.',
    'not_configured': 'Text messaging provider settings are incomplete.',
    'not_test_recipient': 'Test mode sends only to approved test numbers.',
    'no_contact': 'The recipient has not enabled text messages.',
    'not_verified': 'The recipient has not verified their number.',
    'opted_out': 'The recipient opted out of text messages.',
    'contact_changed': 'The recipient changed their number after this was queued.',
}


def now():
    return datetime.now(timezone.utc)


def stamp(value=None):
    return (value or now()).isoformat()


def masked(phone):
    return '•••• ' + phone[-4:] if phone else ''


def code_hash(organization_id, user_id, code):
    return hashlib.sha256(f'{organization_id}:{user_id}:{code}'.encode()).hexdigest()


def test_recipients():
    return {n.strip() for n in os.getenv('WZOS_SMS_TEST_RECIPIENTS', '').split(',') if re.fullmatch(PHONE, n.strip())}


def sms_mode(live_permitted):
    mode = os.getenv('WZOS_SMS_MODE', 'disabled').strip().lower()
    if mode == 'live' and not live_permitted:
        return 'disabled'
    return mode if mode in ('disabled', 'test', 'live') else 'disabled'


def event(db, organization_id, outbox_id, source, name, detail='', actor_id=None, event_id=None):
    db.execute('INSERT INTO sms_events VALUES (?,?,?,?,?,?,?,?)',
               (event_id or str(uuid4()), organization_id, outbox_id, source, name, detail[:300], actor_id, stamp()))


class ContactRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    request_id: UUID
    expected_version: int = Field(ge=0)
    phone: str = Field(pattern=PHONE)
    consent: bool = Field(strict=True)
    consent_version: str = Field(max_length=40)


class CodeInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    code: str = Field(pattern=r'^[0-9]{6}$')


class VersionInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_version: int = Field(ge=1)


class Resolution(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    action: Literal['retry', 'mark_failed', 'cancel']
    confirm_possible_duplicate: bool = False
    note: str = Field(default='', max_length=300)


class Messaging:
    """SMS outbox shared by Messaging and, later, approved dispatch assignments."""

    def __init__(self, app, connect, live_permitted):
        self.app, self.connect, self.live_permitted = app, connect, live_permitted
        with connect() as db:
            for sql in DDL:
                db.execute(sql)

    def provider(self):
        injected = getattr(self.app.state, 'sms_provider', None)
        return injected if injected is not None else sms_provider.TwilioProvider.from_environment()

    def mode(self):
        return sms_mode(self.live_permitted)

    def readiness(self):
        mode, config = self.mode(), sms_provider.settings()
        missing = [] if getattr(self.app.state, 'sms_provider', None) is not None else config['missing']
        if mode == 'test' and not test_recipients():
            missing = [*missing, 'WZOS_SMS_TEST_RECIPIENTS']
        base = config['base_url']
        return {'mode': mode, 'ready': mode != 'disabled' and not missing, 'missing': missing,
                'live_permitted': self.live_permitted, 'test_recipient_count': len(test_recipients()),
                'status_callback_url': base + '/api/messaging/twilio/status' if base else '',
                'inbound_url': base + '/api/messaging/twilio/inbound' if base else ''}

    def blocker(self, db, row):
        """Current reason a queued text cannot be sent, or None."""
        mode = self.mode()
        if mode == 'disabled':
            return 'sms_disabled'
        if self.readiness()['missing']:
            return 'not_configured'
        contact = db.execute('SELECT * FROM sms_contacts WHERE organization_id=? AND user_id=?',
                             (row['organization_id'], row['recipient_id'])).fetchone()
        if not contact:
            return 'no_contact'
        if contact['status'] == 'opted_out':
            return 'opted_out'
        if contact['phone'] != row['phone']:
            return 'contact_changed'
        if row['purpose'] != 'verification' and contact['status'] != 'verified':
            return 'not_verified'
        if mode == 'test' and row['phone'] not in test_recipients():
            return 'not_test_recipient'
        return None

    def enqueue(self, db, *, organization_id, recipient_id, body, purpose, reference_id, actor_id, phone=None):
        """Queue one text inside the caller's transaction; repeats return the original row."""
        prior = db.execute('SELECT * FROM sms_outbox WHERE organization_id=? AND purpose=? AND reference_id=? AND recipient_id=?',
                           (organization_id, purpose, reference_id, recipient_id)).fetchone()
        if prior:
            return dict(prior)
        if phone is None:
            contact = db.execute('SELECT phone FROM sms_contacts WHERE organization_id=? AND user_id=?',
                                 (organization_id, recipient_id)).fetchone()
            phone = contact['phone'] if contact else ''
        row = {'id': str(uuid4()), 'organization_id': organization_id, 'purpose': purpose, 'reference_id': reference_id,
               'recipient_id': recipient_id, 'phone': phone}
        reason = self.blocker(db, row) or ''
        status, created = ('blocked' if reason else 'queued'), stamp()
        db.execute('INSERT INTO sms_outbox VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                   (row['id'], organization_id, purpose, reference_id, recipient_id, phone, body, status, reason, 0,
                    created, None, None, None, None, actor_id, created, created))
        event(db, organization_id, row['id'], 'app', status, reason, actor_id)
        return dict(db.execute('SELECT * FROM sms_outbox WHERE id=?', (row['id'],)).fetchone())

    def process(self, organization_id=None, ids=None, limit=10):
        """Claim due texts, call the provider outside the transaction, then record outcomes."""
        counts = {'claimed': 0, 'accepted': 0, 'retry_scheduled': 0, 'failed': 0, 'ambiguous': 0, 'blocked': 0}
        provider, claimed, current = self.provider(), [], stamp()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            scope, params = ('', []) if organization_id is None else (' AND organization_id=?', [organization_id])
            for row in db.execute("SELECT * FROM sms_outbox WHERE status='sending' AND lease_until<?" + scope, [current, *params]).fetchall():
                # A send that never recorded its outcome may have reached the provider.
                db.execute("UPDATE sms_outbox SET status='ambiguous',reason='lease_expired',lease_until=NULL,updated_at=? WHERE id=?", (current, row['id']))
                event(db, row['organization_id'], row['id'], 'app', 'ambiguous', 'lease_expired')
                counts['ambiguous'] += 1
            if ids is not None:
                if not ids:
                    return counts
                scope += ' AND id IN (' + ','.join('?' * len(ids)) + ')'
                params += list(ids)
            rows = db.execute("SELECT * FROM sms_outbox WHERE status='queued' AND next_attempt_at<=?" + scope +
                              ' ORDER BY created_at,id LIMIT ?', [current, *params, limit]).fetchall()
            for row in rows:
                reason = self.blocker(db, row) or ('' if provider else 'not_configured')
                if reason:
                    db.execute("UPDATE sms_outbox SET status='blocked',reason=?,updated_at=? WHERE id=?", (reason, current, row['id']))
                    event(db, row['organization_id'], row['id'], 'app', 'blocked', reason)
                    counts['blocked'] += 1
                    continue
                lease = stamp(now() + timedelta(seconds=LEASE_SECONDS))
                db.execute("UPDATE sms_outbox SET status='sending',attempts=attempts+1,lease_until=?,updated_at=? WHERE id=?", (lease, current, row['id']))
                event(db, row['organization_id'], row['id'], 'app', 'sending', f'attempt {row["attempts"] + 1}')
                claimed.append({**dict(row), 'attempts': row['attempts'] + 1})
        for row in claimed:
            counts['claimed'] += 1
            try:
                result = provider.send(row['id'], row['phone'], row['body'])
            except Exception:
                result = sms_provider.SendResult('ambiguous', detail='Provider call failed unexpectedly')
            counts[self.record(row, result)] += 1
        return counts

    def record(self, row, result):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current = db.execute('SELECT * FROM sms_outbox WHERE id=?', (row['id'],)).fetchone()
            updated = stamp()
            redact = row['purpose'] == 'verification' and result.outcome != 'retryable'
            body = '[verification code withheld]' if redact else current['body']
            if current['status'] != 'sending' or current['attempts'] != row['attempts']:
                # A signed status callback already advanced this text; keep its state.
                db.execute('UPDATE sms_outbox SET provider_sid=COALESCE(provider_sid,?),body=?,lease_until=NULL,updated_at=? WHERE id=?',
                           (result.sid, body, updated, row['id']))
                event(db, row['organization_id'], row['id'], 'provider_api', result.outcome, result.detail)
                return 'accepted' if result.outcome == 'accepted' else 'ambiguous'
            outcome, status, reason, due = result.outcome, None, '', current['next_attempt_at']
            if outcome == 'accepted':
                status = PROVIDER_STATUS.get(result.provider_status or '', 'accepted')
            elif outcome == 'retryable' and row['attempts'] < MAX_ATTEMPTS:
                status, outcome = 'queued', 'retry_scheduled'
                due = stamp(now() + timedelta(seconds=30 * 2 ** (row['attempts'] - 1)))
            elif outcome == 'retryable':
                status, outcome, reason = 'failed', 'failed', 'retries_exhausted'
            elif outcome == 'rejected' and result.error_code in sms_provider.OPTED_OUT_CODES:
                status, outcome, reason = 'blocked', 'blocked', 'opted_out'
                self.opt_out(db, row['phone'], 'provider_api', organization_id=row['organization_id'])
            elif outcome == 'rejected':
                status, outcome, reason = 'failed', 'failed', 'provider_rejected'
            else:
                status, reason = 'ambiguous', 'provider_response_unknown'
            db.execute('UPDATE sms_outbox SET status=?,reason=?,next_attempt_at=?,lease_until=NULL,provider_sid=?,provider_status=?,error_code=?,body=?,updated_at=? WHERE id=?',
                       (status, reason, due, result.sid, result.provider_status, result.error_code, body, updated, row['id']))
            event(db, row['organization_id'], row['id'], 'provider_api', status,
                  ' '.join(filter(None, [result.detail, result.error_code and 'code ' + result.error_code])))
            return outcome

    def opt_out(self, db, phone, source, organization_id=None):
        """Opt a number out; STOP applies to every organization using this sender."""
        scope, params = ('', []) if organization_id is None else (' AND organization_id=?', [organization_id])
        contacts = db.execute("SELECT * FROM sms_contacts WHERE phone=? AND status<>'opted_out'" + scope, [phone, *params]).fetchall()
        current = stamp()
        for contact in contacts:
            db.execute("UPDATE sms_contacts SET status='opted_out',opted_out_at=?,code_hash=NULL,version=version+1,updated_at=? WHERE organization_id=? AND user_id=?",
                       (current, current, contact['organization_id'], contact['user_id']))
            event(db, contact['organization_id'], None, source, 'opted_out', masked(phone), contact['user_id'])
        for row in db.execute("SELECT id,organization_id FROM sms_outbox WHERE phone=? AND status='queued'" + scope, [phone, *params]).fetchall():
            db.execute("UPDATE sms_outbox SET status='blocked',reason='opted_out',updated_at=? WHERE id=?", (current, row['id']))
            event(db, row['organization_id'], row['id'], source, 'blocked', 'opted_out')
        return len(contacts)


def public(row, include_body=True):
    item = {key: row[key] for key in ('id', 'purpose', 'reference_id', 'recipient_id', 'status', 'reason', 'attempts',
                                      'provider_status', 'error_code', 'created_by', 'created_at', 'updated_at')}
    item['phone'] = masked(row['phone'])
    item['reason_text'] = REASONS.get(row['reason'], '')
    item['provider_sid'] = bool(row['provider_sid'])
    if include_body:
        item['body'] = row['body']
    return item


def contact_view(row, own=True):
    if not row:
        return {'status': 'none', 'phone': '', 'version': 0}
    view = {'status': row['status'], 'phone': row['phone'] if own else masked(row['phone']), 'version': row['version'],
            'consent_version': row['consent_version'], 'consented_at': row['consented_at'],
            'verified_at': row['verified_at'], 'opted_out_at': row['opted_out_at'], 'updated_at': row['updated_at']}
    if own:
        view['code_expires_at'] = row['code_expires_at'] if row['status'] == 'pending_verification' else None
    return view


async def form_params(request):
    raw = await request.body()
    if len(raw) > 16384:
        raise HTTPException(413, 'Callback too large')
    try:
        return parse_qsl(raw.decode('utf-8'), keep_blank_values=True)
    except UnicodeDecodeError:
        raise HTTPException(400, 'Invalid callback') from None


def signed(request, params):
    base = sms_provider.settings()['base_url']
    query = request.scope.get('query_string', b'').decode()
    url = base + request.url.path + ('?' + query if query else '')
    token = os.getenv('WZOS_TWILIO_AUTH_TOKEN', '').strip()
    if not base or not sms_provider.valid_signature(token, url, params, request.headers.get('X-Twilio-Signature', '')):
        raise HTTPException(403, 'Invalid signature')
    return dict(params)


def register(app, connect, actor, actors, live_permitted):
    service = Messaging(app, connect, live_permitted)
    app.state.messaging = service

    def admin(request):
        user = actor(request)
        if user['role'] != 'admin':
            raise HTTPException(403, 'Administrator access required')
        return user

    @app.get('/api/messaging/sms/readiness')
    def readiness(request: Request):
        admin(request)
        return service.readiness()

    @app.get('/api/messaging/sms/contact')
    def own_contact(request: Request):
        user = actor(request)
        with connect() as db:
            row = db.execute('SELECT * FROM sms_contacts WHERE organization_id=? AND user_id=?', (user['organization_id'], user['id'])).fetchone()
        readiness = service.readiness()
        return {**contact_view(row), 'consent_text': CONSENT_TEXT, 'current_consent_version': CONSENT_VERSION,
                'sms_mode': readiness['mode'], 'sms_ready': readiness['ready']}

    @app.put('/api/messaging/sms/contact')
    def enroll(body: ContactRequest, request: Request, background: BackgroundTasks):
        user = actor(request)
        org, uid = user['organization_id'], user['id']
        if not body.consent:
            raise HTTPException(422, 'Consent is required to receive text messages')
        if body.consent_version != CONSENT_VERSION:
            raise HTTPException(409, 'The consent wording changed. Reload and review it before continuing.')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM sms_contacts WHERE organization_id=? AND user_id=?', (org, uid)).fetchone()
            prior = db.execute("SELECT id FROM sms_outbox WHERE organization_id=? AND purpose='verification' AND reference_id=? AND recipient_id=?",
                               (org, str(body.request_id), uid)).fetchone()
            if prior and row and row['phone'] == body.phone:
                return contact_view(row)
            version = row['version'] if row else 0
            if version != body.expected_version:
                raise HTTPException(409, 'Text message settings changed. Reload before saving.')
            today, current = now().date().isoformat(), stamp()
            sent = row['codes_sent'] if row and row['codes_day'] == today else 0
            if sent >= CODES_PER_DAY:
                raise HTTPException(429, 'Too many verification codes today. Try again tomorrow.')
            code = f'{secrets.randbelow(1000000):06d}'
            expires = stamp(now() + timedelta(minutes=CODE_MINUTES))
            values = (body.phone, 'pending_verification', CONSENT_VERSION, current, None, None, code_hash(org, uid, code),
                      expires, 0, today, sent + 1, version + 1, current)
            if row:
                db.execute('UPDATE sms_contacts SET phone=?,status=?,consent_version=?,consented_at=?,verified_at=?,opted_out_at=?,code_hash=?,code_expires_at=?,code_attempts=?,codes_day=?,codes_sent=?,version=?,updated_at=? WHERE organization_id=? AND user_id=?',
                           (*values, org, uid))
            else:
                db.execute('INSERT INTO sms_contacts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (org, uid, *values))
            event(db, org, None, 'member', 'consent_recorded', f'{masked(body.phone)} consent {CONSENT_VERSION}', uid)
            text = f'WZOS verification code: {code}. It expires in {CODE_MINUTES} minutes. If you did not request it, ignore this message. Reply STOP to opt out.'
            queued = service.enqueue(db, organization_id=org, recipient_id=uid, body=text, purpose='verification',
                                     reference_id=str(body.request_id), actor_id=uid, phone=body.phone)
            row = db.execute('SELECT * FROM sms_contacts WHERE organization_id=? AND user_id=?', (org, uid)).fetchone()
        if queued['status'] == 'queued':
            background.add_task(service.process, org, [queued['id']])
        return {**contact_view(row), 'verification_delivery': public(queued, include_body=False)}

    @app.post('/api/messaging/sms/contact/verify')
    def verify(body: CodeInput, request: Request):
        user = actor(request)
        org, uid = user['organization_id'], user['id']
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM sms_contacts WHERE organization_id=? AND user_id=?', (org, uid)).fetchone()
            if row and row['status'] == 'verified':
                return contact_view(row)
            if not row or row['status'] != 'pending_verification' or not row['code_hash']:
                raise HTTPException(409, 'Request a new verification code first')
            if row['code_attempts'] >= 5 or row['code_expires_at'] < stamp():
                raise HTTPException(409, 'This code expired. Request a new verification code.')
            if not secrets.compare_digest(row['code_hash'], code_hash(org, uid, body.code)):
                db.execute('UPDATE sms_contacts SET code_attempts=code_attempts+1 WHERE organization_id=? AND user_id=?', (org, uid))
                return Response('{"detail":"The code did not match"}', status_code=422, media_type='application/json')
            current = stamp()
            db.execute("UPDATE sms_contacts SET status='verified',verified_at=?,code_hash=NULL,code_expires_at=NULL,version=version+1,updated_at=? WHERE organization_id=? AND user_id=?",
                       (current, current, org, uid))
            event(db, org, None, 'member', 'verified', masked(row['phone']), uid)
            return contact_view(db.execute('SELECT * FROM sms_contacts WHERE organization_id=? AND user_id=?', (org, uid)).fetchone())

    @app.post('/api/messaging/sms/contact/opt-out')
    def member_opt_out(body: VersionInput, request: Request):
        user = actor(request)
        org, uid = user['organization_id'], user['id']
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM sms_contacts WHERE organization_id=? AND user_id=?', (org, uid)).fetchone()
            if not row:
                raise HTTPException(404, 'Text messages are not enabled')
            if row['status'] == 'opted_out' and row['version'] == body.expected_version + 1:
                return contact_view(row)
            if row['version'] != body.expected_version:
                raise HTTPException(409, 'Text message settings changed. Reload before saving.')
            current = stamp()
            db.execute("UPDATE sms_contacts SET status='opted_out',opted_out_at=?,code_hash=NULL,version=version+1,updated_at=? WHERE organization_id=? AND user_id=?",
                       (current, current, org, uid))
            event(db, org, None, 'member', 'opted_out', masked(row['phone']), uid)
            for queued in db.execute("SELECT id FROM sms_outbox WHERE organization_id=? AND recipient_id=? AND status='queued'", (org, uid)).fetchall():
                db.execute("UPDATE sms_outbox SET status='blocked',reason='opted_out',updated_at=? WHERE id=?", (current, queued['id']))
                event(db, org, queued['id'], 'member', 'blocked', 'opted_out', uid)
            return contact_view(db.execute('SELECT * FROM sms_contacts WHERE organization_id=? AND user_id=?', (org, uid)).fetchone())

    @app.get('/api/messaging/sms/contacts')
    def contacts(request: Request):
        user = admin(request)
        people = {k: v for k, v in actors(user).items() if v['organization_id'] == user['organization_id']}
        with connect() as db:
            rows = {r['user_id']: r for r in db.execute('SELECT * FROM sms_contacts WHERE organization_id=?', (user['organization_id'],)).fetchall()}
        return {'items': [{'id': pid, 'name': person['name'], 'role': person['role'], **contact_view(rows.get(pid), own=False)}
                          for pid, person in sorted(people.items(), key=lambda item: (item[1]['name'], item[0]))]}

    @app.get('/api/messaging/sms/outbox')
    def outbox(request: Request, status: str | None = Query(None, max_length=20), offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=50)):
        user = admin(request)
        clause, params = 'organization_id=?', [user['organization_id']]
        if status:
            clause += ' AND status=?'
            params.append(status)
        with connect() as db:
            total = db.execute('SELECT COUNT(*) FROM sms_outbox WHERE ' + clause, params).fetchone()[0]
            rows = db.execute('SELECT * FROM sms_outbox WHERE ' + clause + ' ORDER BY created_at DESC,id LIMIT ? OFFSET ?', [*params, limit, offset]).fetchall()
        return {'items': [public(r) for r in rows], 'total': total, 'offset': offset, 'limit': limit}

    @app.get('/api/messaging/sms/outbox/{outbox_id}/events')
    def events(outbox_id: UUID, request: Request):
        user = admin(request)
        with connect() as db:
            if not db.execute('SELECT 1 FROM sms_outbox WHERE id=? AND organization_id=?', (str(outbox_id), user['organization_id'])).fetchone():
                raise HTTPException(404, 'Text message not found')
            rows = db.execute('SELECT source,event,detail,actor_id,occurred_at FROM sms_events WHERE outbox_id=? AND organization_id=? ORDER BY occurred_at,id LIMIT 100',
                              (str(outbox_id), user['organization_id'])).fetchall()
        return {'items': [dict(r) for r in rows]}

    @app.post('/api/messaging/sms/outbox/{outbox_id}/resolve')
    def resolve(outbox_id: UUID, body: Resolution, request: Request, background: BackgroundTasks):
        user = admin(request)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM sms_outbox WHERE id=? AND organization_id=?', (str(outbox_id), user['organization_id'])).fetchone()
            if not row:
                raise HTTPException(404, 'Text message not found')
            allowed = {'ambiguous': {'retry', 'mark_failed'}, 'blocked': {'retry', 'cancel'}, 'queued': {'cancel'}}
            if body.action not in allowed.get(row['status'], set()):
                raise HTTPException(409, 'This text message cannot be changed in its current state')
            if row['status'] == 'ambiguous' and body.action == 'retry' and not body.confirm_possible_duplicate:
                raise HTTPException(409, 'The provider may already have this message. Confirm that a duplicate is acceptable before resending.')
            if row['purpose'] == 'verification' and body.action == 'retry':
                raise HTTPException(409, 'Verification codes are not resent. The member can request a new code.')
            current = stamp()
            status, reason = {'retry': ('queued', ''), 'mark_failed': ('failed', 'admin_marked_failed'), 'cancel': ('cancelled', 'admin_cancelled')}[body.action]
            db.execute('UPDATE sms_outbox SET status=?,reason=?,next_attempt_at=?,updated_at=? WHERE id=?', (status, reason, current, current, row['id']))
            event(db, row['organization_id'], row['id'], 'admin', 'admin_' + body.action, body.note, user['id'])
            updated = db.execute('SELECT * FROM sms_outbox WHERE id=?', (row['id'],)).fetchone()
        if status == 'queued':
            background.add_task(service.process, user['organization_id'], [row['id']])
        return public(updated)

    @app.post('/api/messaging/sms/process')
    def process(request: Request):
        user = admin(request)
        return service.process(user['organization_id'], limit=25)

    @app.post('/api/messaging/twilio/status')
    async def status_callback(request: Request):
        data = signed(request, await form_params(request))
        outbox_id, sid = request.query_params.get('outbox', ''), data.get('MessageSid', '')
        mapped = PROVIDER_STATUS.get(data.get('MessageStatus', ''))
        error = data.get('ErrorCode') or None
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM sms_outbox WHERE id=?', (outbox_id,)).fetchone()
            if not row or (row['provider_sid'] and sid and row['provider_sid'] != sid):
                return Response(status_code=204)
            key = hashlib.sha256(f'{outbox_id}|{sid}|{data.get("MessageStatus")}|{error}'.encode()).hexdigest()
            if db.execute('SELECT 1 FROM sms_events WHERE id=?', (key,)).fetchone():
                return Response(status_code=204)
            event(db, row['organization_id'], row['id'], 'callback', data.get('MessageStatus', 'unknown')[:30],
                  'code ' + error if error else '', event_id=key)
            # Provider evidence overrides an admin's "mark failed" guess, never a final provider state.
            terminal = row['status'] in ('blocked', 'cancelled', 'delivered', 'undelivered') or (
                row['status'] == 'failed' and row['reason'] != 'admin_marked_failed')
            if mapped and not terminal and (row['status'] == 'failed' or RANK[mapped] > RANK.get(row['status'], 0)):
                db.execute('UPDATE sms_outbox SET status=?,reason=?,provider_status=?,error_code=COALESCE(?,error_code),provider_sid=COALESCE(provider_sid,?),lease_until=NULL,updated_at=? WHERE id=?',
                           (mapped, '', data.get('MessageStatus'), error, sid or None, stamp(), row['id']))
            if error in sms_provider.OPTED_OUT_CODES:
                service.opt_out(db, row['phone'], 'callback', organization_id=row['organization_id'])
        return Response(status_code=204)

    @app.post('/api/messaging/twilio/inbound')
    async def inbound(request: Request):
        data = signed(request, await form_params(request))
        phone = data.get('From', '')
        word = (data.get('OptOutType') or data.get('Body', '')).strip().upper()
        # Other replies are not stored: only opt-out and opt-in keywords change state.
        if re.fullmatch(PHONE, phone) and word in STOP_WORDS | START_WORDS:
            with connect() as db:
                db.execute('BEGIN IMMEDIATE')
                if word in STOP_WORDS:
                    service.opt_out(db, phone, 'inbound')
                else:
                    current = stamp()
                    for contact in db.execute("SELECT * FROM sms_contacts WHERE phone=? AND status='opted_out' AND verified_at IS NOT NULL", (phone,)).fetchall():
                        db.execute("UPDATE sms_contacts SET status='verified',opted_out_at=NULL,version=version+1,updated_at=? WHERE organization_id=? AND user_id=?",
                                   (current, contact['organization_id'], contact['user_id']))
                        event(db, contact['organization_id'], None, 'inbound', 'opted_in', masked(phone), contact['user_id'])
        return Response('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type='application/xml')

    return service
