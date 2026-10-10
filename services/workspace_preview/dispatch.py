"""Enterprise dispatch: staffing requirements, deterministic proposals and reviewed sending.

Eligibility comes only from organization records: active membership, Codex's employee
qualification and availability contracts, existing assignments and team schedules.
Missing or unverifiable facts are never treated as eligible. Admins approve every send;
approval re-checks the records the proposal was based on, so stale plans cannot be sent.
Assignment notices go through Messaging (in-app, plus SMS only for members who enabled it).
"""
import json
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .employees import availability_state, qualification_state

DDL = (
    'CREATE TABLE IF NOT EXISTS dispatch_requirements (organization_id TEXT NOT NULL,order_id TEXT NOT NULL,version INTEGER NOT NULL,payload TEXT NOT NULL,updated_by TEXT NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(organization_id,order_id))',
    'CREATE TABLE IF NOT EXISTS dispatch_plans (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,order_id TEXT NOT NULL,status TEXT NOT NULL,version INTEGER NOT NULL,payload TEXT NOT NULL,created_by TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,approved_by TEXT,approved_at TEXT,approval_request_id TEXT UNIQUE)',
    'CREATE TABLE IF NOT EXISTS dispatch_assignments (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,plan_id TEXT NOT NULL,order_id TEXT NOT NULL,user_id TEXT NOT NULL,role_id TEXT NOT NULL,status TEXT NOT NULL,starts_at TEXT NOT NULL,ends_at TEXT NOT NULL,message_id TEXT,responded_at TEXT,response_note TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS dispatch_events (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,order_id TEXT NOT NULL,plan_id TEXT,actor_id TEXT NOT NULL,event TEXT NOT NULL,detail TEXT NOT NULL,occurred_at TEXT NOT NULL)',
)
ACTIVE = ('sent', 'accepted')  # assignments that occupy the employee's time
OVERRIDABLE = {'availability_unknown', 'unavailable', 'qualification_expiry_unknown'}
REASONS = {
    'inactive_member': 'Not an active member of this organization',
    'qualification_missing': 'Required qualification is not on record',
    'qualification_unreviewed': 'Required qualification has not been verified',
    'qualification_rejected': 'Required qualification was rejected',
    'qualification_expired': 'Required qualification expires before the job ends',
    'qualification_expiry_unknown': 'Qualification is verified but has no expiry date',
    'availability_unknown': 'Availability is not recorded for the whole job',
    'unavailable': 'Recorded as unavailable during the job',
    'assignment_conflict': 'Already assigned to an overlapping job',
    'schedule_conflict': 'Has an overlapping team schedule entry',
}
ID = r'^[a-z0-9_-]{1,40}$'
QUALIFICATION_ID = r'^[A-Za-z0-9_-]{1,80}$'


def now():
    return datetime.now(timezone.utc).isoformat()


def utc(value):
    return datetime.fromisoformat(value).astimezone(timezone.utc)


class Role(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    id: str = Field(pattern=ID)
    title: str = Field(min_length=1, max_length=80)
    count: int = Field(ge=1, le=20, strict=True)
    qualification_ids: list[str] = Field(default_factory=list, max_length=10)

    @model_validator(mode='after')
    def identifiers(self):
        import re
        if len(set(self.qualification_ids)) != len(self.qualification_ids) or not all(re.fullmatch(QUALIFICATION_ID, q) for q in self.qualification_ids):
            raise ValueError('Qualification identifiers must be distinct letters, digits, underscores or hyphens')
        return self


class Requirements(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    expected_version: int = Field(ge=0)
    starts_at: datetime
    ends_at: datetime
    roles: list[Role] = Field(min_length=1, max_length=10)
    notes: str = Field(default='', max_length=1000)

    @model_validator(mode='after')
    def window(self):
        if self.starts_at.utcoffset() is None or self.ends_at.utcoffset() is None:
            raise ValueError('Job times require a timezone')
        if self.ends_at <= self.starts_at or self.ends_at - self.starts_at > timedelta(days=7):
            raise ValueError('The job must end after it starts and last at most 7 days')
        if len({r.id for r in self.roles}) != len(self.roles):
            raise ValueError('Role identifiers must be distinct')
        return self


class Pick(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    role_id: str = Field(pattern=ID)
    user_id: str = Field(min_length=1, max_length=200)
    override_reason: str = Field(default='', max_length=500)


class PlanEdit(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_version: int = Field(ge=1)
    assignments: list[Pick] = Field(max_length=200)


class Approval(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: UUID
    expected_version: int = Field(ge=1)


class Cancellation(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=3, max_length=500)


class Response(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    response: Literal['accepted', 'declined']
    note: str = Field(default='', max_length=500)


def register(app, connect, actor, permitted_row, actors):
    with connect() as db:
        for sql in DDL:
            db.execute(sql)

    def enterprise(request, admin=True):
        user = actor(request)
        if user['edition'] != 'enterprise':
            raise HTTPException(403, 'Dispatch is an Enterprise feature. Core messaging and schedules remain available.')
        if admin and user['role'] != 'admin':
            raise HTTPException(403, 'Administrator access required')
        return user

    def log(db, user, order_id, plan_id, name, detail=''):
        db.execute('INSERT INTO dispatch_events VALUES (?,?,?,?,?,?,?,?)',
                   (str(uuid4()), user['organization_id'], order_id, plan_id, user['id'], name, detail[:500], now()))

    def requirement(db, org, order_id):
        row = db.execute('SELECT * FROM dispatch_requirements WHERE organization_id=? AND order_id=?', (org, order_id)).fetchone()
        return {**json.loads(row['payload']), 'version': row['version'], 'updated_at': row['updated_at']} if row else None

    def evaluate(db, user, person, role, req, ignore_plan=None):
        """Facts and reasons for one employee in one role; never infers missing facts."""
        org, uid = user['organization_id'], person['id']
        start, end = utc(req['starts_at']), utc(req['ends_at'])
        hard, soft = [], []
        member = db.execute('SELECT active FROM memberships WHERE organization_id=? AND user_id=?', (org, uid)).fetchone()
        if not member or not member['active']:
            hard.append('inactive_member')
        profile = db.execute('SELECT version,payload FROM employee_profiles WHERE organization_id=? AND user_id=?', (org, uid)).fetchone()
        quals = {}
        for qid in role['qualification_ids']:
            row = db.execute('SELECT version,payload FROM employee_qualifications WHERE organization_id=? AND user_id=? AND qualification_id=?', (org, uid, qid)).fetchone()
            quals[qid] = row['version'] if row else 0
            if not row:
                hard.append('qualification_missing')
                continue
            payload = json.loads(row['payload'])
            # Must hold for the whole job: evaluate on the final day as well as the first.
            states = {qualification_state(payload, start.date()), qualification_state(payload, end.date())}
            if 'expired' in states:
                hard.append('qualification_expired')
            elif 'rejected' in states:
                hard.append('qualification_rejected')
            elif 'unreviewed' in states:
                hard.append('qualification_unreviewed')
            elif 'verified_expiry_unknown' in states:
                soft.append('qualification_expiry_unknown')
        availability = availability_state(json.loads(profile['payload']), start, end) if profile else 'unknown'
        if availability == 'unknown':
            soft.append('availability_unknown')
        elif availability == 'unavailable':
            soft.append('unavailable')
        busy = db.execute("SELECT starts_at,ends_at,plan_id FROM dispatch_assignments WHERE organization_id=? AND user_id=? AND status IN ('sent','accepted')", (org, uid)).fetchall()
        if any(r['plan_id'] != ignore_plan and utc(r['starts_at']) < end and utc(r['ends_at']) > start for r in busy):
            hard.append('assignment_conflict')
        for row in db.execute("SELECT payload FROM module_records WHERE organization_id=? AND kind='schedule'", (org,)).fetchall():
            entry = json.loads(row['payload'])
            if entry.get('status') != 'cancelled' and uid in entry.get('assignees', []) and entry.get('start') and entry.get('end'):
                if utc(entry['start']) < end and utc(entry['end']) > start:
                    hard.append('schedule_conflict')
                    break
        week = [r for r in busy if abs((utc(r['starts_at']) - start).total_seconds()) <= 7 * 86400]
        return {'user_id': uid, 'name': person['name'], 'eligible': not hard and not soft, 'blockers': sorted(set(hard)),
                'warnings': sorted(set(soft)), 'availability': availability, 'recent_assignments': len(week),
                'snapshot': {'profile_version': profile['version'] if profile else 0, 'qualification_versions': quals}}

    def people(user):
        return {k: v for k, v in actors(user).items() if v['organization_id'] == user['organization_id']}

    def order_state(db, user, order_id):
        order = permitted_row(db, order_id, user)
        req = requirement(db, user['organization_id'], order_id)
        if not req:
            raise HTTPException(409, 'Save staffing requirements for this work order first')
        return order, req

    def sent_plan(db, user, order_id):
        # A new revision replaces the order's sent plan, so its people are not in conflict with it.
        row = db.execute("SELECT id FROM dispatch_plans WHERE organization_id=? AND order_id=? AND status='sent'", (user['organization_id'], order_id)).fetchone()
        return row['id'] if row else None

    def plan_row(db, user, plan_id):
        row = db.execute('SELECT * FROM dispatch_plans WHERE id=? AND organization_id=?', (str(plan_id), user['organization_id'])).fetchone()
        if not row:
            raise HTTPException(404, 'Dispatch plan not found')
        return row

    def view(db, row, order=None, req=None):
        plan = {**json.loads(row['payload']), **{k: row[k] for k in ('id', 'order_id', 'status', 'version', 'created_by', 'created_at', 'updated_at', 'approved_by', 'approved_at')}}
        if order is not None and req is not None:
            plan['stale'] = row['status'] in ('draft', 'sent') and (plan['requirement_version'] != req['version'] or plan['order_version'] != order['version'])
        plan['sent_assignments'] = [dict(r) for r in db.execute('SELECT id,user_id,role_id,status,responded_at,response_note,updated_at FROM dispatch_assignments WHERE plan_id=? ORDER BY role_id,user_id', (row['id'],)).fetchall()]
        for item in plan['sent_assignments']:
            text = db.execute("SELECT status,reason FROM sms_outbox WHERE purpose='dispatch' AND reference_id=?", (item['id'],)).fetchone() if has_outbox(db) else None
            item['sms'] = {'status': text['status'], 'reason': text['reason']} if text else None
        return plan

    def has_outbox(db):
        return getattr(app.state, 'messaging', None) is not None

    def validate_picks(db, user, req, picks, ignore_plan=None):
        roles = {r['id']: r for r in req['roles']}
        team = people(user)
        if len({p['user_id'] for p in picks}) != len(picks):
            raise HTTPException(422, 'Each employee can fill only one role in a plan')
        counts = {}
        chosen = []
        for pick in picks:
            role = roles.get(pick['role_id'])
            if not role:
                raise HTTPException(422, 'Unknown role in plan')
            counts[role['id']] = counts.get(role['id'], 0) + 1
            if counts[role['id']] > role['count']:
                raise HTTPException(422, f'Too many people for {role["title"]}')
            person = team.get(pick['user_id']) or {'id': pick['user_id'], 'name': ''}
            if pick['user_id'] not in team:
                raise HTTPException(422, 'Assignments must be active members of this organization')
            result = evaluate(db, user, person, role, req, ignore_plan)
            if result['blockers']:
                raise HTTPException(422, f'{person["name"]} cannot be assigned: ' + '; '.join(REASONS[b] for b in result['blockers']))
            if result['warnings'] and len(pick.get('override_reason', '').strip()) < 10:
                raise HTTPException(422, f'{person["name"]} needs an override justification (at least 10 characters): ' + '; '.join(REASONS[w] for w in result['warnings']))
            chosen.append({'role_id': role['id'], 'user_id': pick['user_id'], 'name': person['name'],
                           'override_reason': pick.get('override_reason', '').strip() if result['warnings'] else '', 'evaluation': result})
        unfilled = [{'role_id': r['id'], 'title': r['title'], 'missing': r['count'] - counts.get(r['id'], 0)} for r in req['roles'] if counts.get(r['id'], 0) < r['count']]
        return chosen, unfilled

    def notice(db, user, recipient_id, text, reference, background):
        """In-app message plus an SMS copy when the recipient enabled texts."""
        message_id = str(uuid4())
        db.execute('INSERT INTO fixture_messages VALUES (?,?,?,?,?,?)', (message_id, user['organization_id'], user['id'], recipient_id, text, now()))
        db.execute('INSERT INTO message_receipts VALUES (?,?,?,?,?)', (user['organization_id'], message_id, recipient_id, 0, None))
        messaging = getattr(app.state, 'messaging', None)
        if messaging is not None:
            body = f"WZOS {user['organization']}: {text} Reply STOP to opt out."
            queued = messaging.enqueue(db, organization_id=user['organization_id'], recipient_id=recipient_id, body=body,
                                       purpose='dispatch', reference_id=reference, actor_id=user['id'])
            if queued['status'] == 'queued':
                background.append(queued['id'])
        return message_id

    def when(req):
        return f"{utc(req['starts_at']).strftime('%Y-%m-%d %H:%M')}–{utc(req['ends_at']).strftime('%H:%M')} UTC"

    def deliver(user, background, ids):
        messaging = getattr(app.state, 'messaging', None)
        if messaging is not None and ids:
            background.add_task(messaging.process, user['organization_id'], ids)

    @app.get('/api/dispatch/orders/{order_id}')
    def dispatch_order(order_id: str, request: Request):
        user = enterprise(request)
        with connect() as db:
            order = permitted_row(db, order_id, user)
            req = requirement(db, user['organization_id'], order_id)
            rows = db.execute('SELECT * FROM dispatch_plans WHERE organization_id=? AND order_id=? ORDER BY created_at DESC,id LIMIT 10', (user['organization_id'], order_id)).fetchall()
            plans = [view(db, r, order, req) for r in rows] if req else []
        return {'order_id': order_id, 'order_version': order['version'], 'requirements': req, 'plans': plans, 'reasons': REASONS}

    @app.put('/api/dispatch/orders/{order_id}/requirements')
    def save_requirements(order_id: str, body: Requirements, request: Request):
        user = enterprise(request)
        payload = body.model_dump(mode='json', exclude={'expected_version'})
        payload['starts_at'], payload['ends_at'] = (body.starts_at.astimezone(timezone.utc).isoformat(), body.ends_at.astimezone(timezone.utc).isoformat())
        encoded = json.dumps(payload, sort_keys=True)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            permitted_row(db, order_id, user)
            row = db.execute('SELECT * FROM dispatch_requirements WHERE organization_id=? AND order_id=?', (user['organization_id'], order_id)).fetchone()
            version = row['version'] if row else 0
            if version != body.expected_version:
                if row and version == body.expected_version + 1 and row['payload'] == encoded:
                    return requirement(db, user['organization_id'], order_id)
                raise HTTPException(409, 'Staffing requirements changed. Reload before saving.')
            db.execute('INSERT INTO dispatch_requirements VALUES (?,?,?,?,?,?) ON CONFLICT(organization_id,order_id) DO UPDATE SET version=excluded.version,payload=excluded.payload,updated_by=excluded.updated_by,updated_at=excluded.updated_at',
                       (user['organization_id'], order_id, version + 1, encoded, user['id'], now()))
            log(db, user, order_id, None, 'requirements_saved', f'version {version + 1}')
            return requirement(db, user['organization_id'], order_id)

    @app.post('/api/dispatch/orders/{order_id}/proposals')
    def propose(order_id: str, request: Request):
        user = enterprise(request)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            order, req = order_state(db, user, order_id)
            team, ignore = people(user), sent_plan(db, user, order_id)
            picks, candidates = [], {}
            for role in req['roles']:
                results = [evaluate(db, user, person, role, req, ignore) for person in team.values()]
                # Deterministic ranking: fully eligible first, then lighter recent workload, then name.
                results.sort(key=lambda r: (not r['eligible'], r['recent_assignments'], r['name'], r['user_id']))
                candidates[role['id']] = results[:50]
                taken = {p['user_id'] for p in picks}
                for result in [r for r in results if r['eligible'] and r['user_id'] not in taken][:role['count']]:
                    picks.append({'role_id': role['id'], 'user_id': result['user_id']})
            chosen, unfilled = validate_picks(db, user, req, picks, ignore)
            plan_id, stamp = str(uuid4()), now()
            payload = {'requirement_version': req['version'], 'order_version': order['version'], 'assignments': chosen,
                       'unfilled': unfilled, 'candidates': candidates, 'method': 'deterministic_rules_v1'}
            db.execute('INSERT INTO dispatch_plans VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                       (plan_id, user['organization_id'], order_id, 'draft', 1, json.dumps(payload, sort_keys=True), user['id'], stamp, stamp, None, None, None))
            log(db, user, order_id, plan_id, 'proposal_created', f'{len(chosen)} proposed, {sum(u["missing"] for u in unfilled)} unfilled')
            return view(db, plan_row(db, user, plan_id), order, req)

    @app.put('/api/dispatch/plans/{plan_id}')
    def edit_plan(plan_id: UUID, body: PlanEdit, request: Request):
        user = enterprise(request)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = plan_row(db, user, plan_id)
            if row['status'] != 'draft':
                raise HTTPException(409, 'Only draft plans can be edited. Create a new proposal to change sent assignments.')
            if row['version'] != body.expected_version:
                raise HTTPException(409, 'This plan changed. Reload before editing.')
            order, req = order_state(db, user, row['order_id'])
            payload = json.loads(row['payload'])
            if payload['requirement_version'] != req['version'] or payload['order_version'] != order['version']:
                raise HTTPException(409, 'The work order or its requirements changed. Create a new proposal.')
            chosen, unfilled = validate_picks(db, user, req, [p.model_dump() for p in body.assignments], sent_plan(db, user, row['order_id']))
            payload.update(assignments=chosen, unfilled=unfilled)
            db.execute('UPDATE dispatch_plans SET payload=?,version=version+1,updated_at=? WHERE id=?', (json.dumps(payload, sort_keys=True), now(), row['id']))
            overrides = sum(1 for c in chosen if c['override_reason'])
            log(db, user, row['order_id'], row['id'], 'plan_edited', f'{len(chosen)} assigned, {overrides} with override justification')
            return view(db, plan_row(db, user, plan_id), order, req)

    @app.post('/api/dispatch/plans/{plan_id}/approve')
    def approve(plan_id: UUID, body: Approval, request: Request, background: BackgroundTasks):
        user = enterprise(request)
        queued = []
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = plan_row(db, user, plan_id)
            if row['status'] == 'sent' and row['approval_request_id'] == str(body.request_id):
                order, req = order_state(db, user, row['order_id'])
                return view(db, row, order, req)
            if row['status'] != 'draft' or row['version'] != body.expected_version:
                raise HTTPException(409, 'This plan changed or was already handled. Reload before approving.')
            order, req = order_state(db, user, row['order_id'])
            payload = json.loads(row['payload'])
            if payload['requirement_version'] != req['version'] or payload['order_version'] != order['version']:
                raise HTTPException(409, 'The work order or its requirements changed after this proposal. Create a new proposal.')
            if not payload['assignments']:
                raise HTTPException(422, 'Add at least one assignment before approving')
            previous = db.execute("SELECT id FROM dispatch_plans WHERE organization_id=? AND order_id=? AND status='sent'", (user['organization_id'], row['order_id'])).fetchall()
            ignore = previous[0]['id'] if previous else None
            # Re-check every assignment against current records and the proposal snapshot.
            current, _ = validate_picks(db, user, req, [{k: a[k] for k in ('role_id', 'user_id', 'override_reason')} for a in payload['assignments']], ignore_plan=ignore)
            for before, after in zip(payload['assignments'], current):
                if before['evaluation']['snapshot'] != after['evaluation']['snapshot']:
                    raise HTTPException(409, f'{before["name"]}\'s employee record changed after this proposal. Review it again before sending.')
            stamp, title = now(), json.loads(order['payload']).get('title', 'Work order')
            address = json.loads(order['payload']).get('address', '')
            roles = {r['id']: r['title'] for r in req['roles']}
            kept = {a['user_id'] for a in payload['assignments']}
            for old in previous:
                for item in db.execute("SELECT * FROM dispatch_assignments WHERE plan_id=? AND status IN ('sent','accepted')", (old['id'],)).fetchall():
                    db.execute("UPDATE dispatch_assignments SET status='replaced',updated_at=? WHERE id=?", (stamp, item['id']))
                    if item['user_id'] not in kept:
                        notice(db, user, item['user_id'], f'Assignment cancelled: {title} {when(req)}. You are no longer assigned to this job.', item['id'] + ':cancel', queued)
                db.execute("UPDATE dispatch_plans SET status='superseded',updated_at=? WHERE id=?", (stamp, old['id']))
                log(db, user, row['order_id'], old['id'], 'plan_superseded', 'replaced by ' + row['id'])
            for assignment in payload['assignments']:
                assignment_id = str(uuid4())
                text = f'New assignment: {title}, {roles[assignment["role_id"]]}, {when(req)}. Location: {address}. Open WZOS Messaging to accept or decline.'
                db.execute('INSERT INTO dispatch_assignments VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                           (assignment_id, user['organization_id'], row['id'], row['order_id'], assignment['user_id'], assignment['role_id'], 'sent',
                            req['starts_at'], req['ends_at'], None, None, '', stamp, stamp))
                message_id = notice(db, user, assignment['user_id'], text, assignment_id, queued)
                db.execute('UPDATE dispatch_assignments SET message_id=? WHERE id=?', (message_id, assignment_id))
            db.execute("UPDATE dispatch_plans SET status='superseded',updated_at=? WHERE organization_id=? AND order_id=? AND status='draft' AND id<>?", (stamp, user['organization_id'], row['order_id'], row['id']))
            db.execute("UPDATE dispatch_plans SET status='sent',version=version+1,approved_by=?,approved_at=?,approval_request_id=?,updated_at=? WHERE id=?",
                       (user['id'], stamp, str(body.request_id), stamp, row['id']))
            log(db, user, row['order_id'], row['id'], 'plan_approved_and_sent', f'{len(payload["assignments"])} assignments')
            result = view(db, plan_row(db, user, plan_id), order, req)
        deliver(user, background, queued)
        return result

    @app.post('/api/dispatch/plans/{plan_id}/cancel')
    def cancel(plan_id: UUID, body: Cancellation, request: Request, background: BackgroundTasks):
        user = enterprise(request)
        queued = []
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = plan_row(db, user, plan_id)
            if row['status'] == 'cancelled' and row['version'] == body.expected_version + 1:
                return view(db, row)
            if row['status'] not in ('draft', 'sent') or row['version'] != body.expected_version:
                raise HTTPException(409, 'This plan changed or was already handled. Reload before cancelling.')
            stamp = now()
            req = requirement(db, user['organization_id'], row['order_id'])
            order = permitted_row(db, row['order_id'], user)
            title = json.loads(order['payload']).get('title', 'Work order')
            for item in db.execute("SELECT * FROM dispatch_assignments WHERE plan_id=? AND status IN ('sent','accepted','declined')", (row['id'],)).fetchall():
                db.execute("UPDATE dispatch_assignments SET status='cancelled',updated_at=? WHERE id=?", (stamp, item['id']))
                notice(db, user, item['user_id'], f'Assignment cancelled: {title} {when(req)}. Reason: {body.reason}', item['id'] + ':cancel', queued)
            db.execute("UPDATE dispatch_plans SET status='cancelled',version=version+1,updated_at=? WHERE id=?", (stamp, row['id']))
            log(db, user, row['order_id'], row['id'], 'plan_cancelled', body.reason)
            result = view(db, plan_row(db, user, plan_id))
        deliver(user, background, queued)
        return result

    @app.get('/api/dispatch/my-assignments')
    def mine(request: Request, offset: int = Query(0, ge=0)):
        user = enterprise(request, admin=False)
        with connect() as db:
            rows = db.execute('SELECT * FROM dispatch_assignments WHERE organization_id=? AND user_id=? ORDER BY starts_at DESC,id LIMIT 25 OFFSET ?', (user['organization_id'], user['id'], offset)).fetchall()
            items = []
            for row in rows:
                order = db.execute('SELECT payload FROM preview_orders WHERE id=? AND organization_id=?', (row['order_id'], user['organization_id'])).fetchone()
                details = json.loads(order['payload']) if order else {}
                req = requirement(db, user['organization_id'], row['order_id']) or {'roles': []}
                titles = {r['id']: r['title'] for r in req['roles']}
                items.append({**{k: row[k] for k in ('id', 'order_id', 'role_id', 'status', 'starts_at', 'ends_at', 'responded_at', 'response_note', 'updated_at')},
                              'role_title': titles.get(row['role_id'], row['role_id']), 'order_title': details.get('title', ''), 'address': details.get('address', '')})
        return {'items': items}

    @app.post('/api/dispatch/assignments/{assignment_id}/respond')
    def respond(assignment_id: UUID, body: Response, request: Request):
        user = enterprise(request, admin=False)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM dispatch_assignments WHERE id=? AND organization_id=? AND user_id=?', (str(assignment_id), user['organization_id'], user['id'])).fetchone()
            if not row:
                raise HTTPException(404, 'Assignment not found')
            if row['status'] == body.response:
                return {'id': row['id'], 'status': row['status'], 'responded_at': row['responded_at']}
            if row['status'] != 'sent':
                raise HTTPException(409, 'This assignment was already answered, changed or cancelled. Contact your admin to change it.')
            stamp = now()
            db.execute('UPDATE dispatch_assignments SET status=?,responded_at=?,response_note=?,updated_at=? WHERE id=?', (body.response, stamp, body.note, stamp, row['id']))
            if row['message_id']:
                db.execute('UPDATE message_receipts SET acknowledged_at=COALESCE(acknowledged_at,?) WHERE message_id=? AND recipient_id=?', (stamp, row['message_id'], user['id']))
            log(db, user, row['order_id'], row['plan_id'], 'assignment_' + body.response, body.note)
        return {'id': row['id'], 'status': body.response, 'responded_at': stamp}

    @app.get('/api/dispatch/orders/{order_id}/events')
    def events(order_id: str, request: Request):
        user = enterprise(request)
        with connect() as db:
            permitted_row(db, order_id, user)
            rows = db.execute('SELECT plan_id,actor_id,event,detail,occurred_at FROM dispatch_events WHERE organization_id=? AND order_id=? ORDER BY occurred_at DESC,id LIMIT 100', (user['organization_id'], order_id)).fetchall()
        return {'items': [dict(r) for r in rows]}
