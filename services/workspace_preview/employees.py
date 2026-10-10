"""Organization employee contracts shared by dispatch and training.

An admin-recorded verification is not an agency certification. Private profile
data is available only to organization admins and the employee concerned.
"""
import json
from datetime import date, datetime, timezone
from typing import Literal
from fastapi import HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

DDL = (
    'CREATE TABLE IF NOT EXISTS employee_profiles (organization_id TEXT NOT NULL,user_id TEXT NOT NULL,employee_number TEXT NOT NULL,payload TEXT NOT NULL,version INTEGER NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(organization_id,user_id),UNIQUE(organization_id,employee_number))',
    'CREATE TABLE IF NOT EXISTS employee_qualifications (organization_id TEXT NOT NULL,user_id TEXT NOT NULL,qualification_id TEXT NOT NULL,payload TEXT NOT NULL,version INTEGER NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(organization_id,user_id,qualification_id))',
    'CREATE TABLE IF NOT EXISTS employee_history (organization_id TEXT NOT NULL,user_id TEXT NOT NULL,record_key TEXT NOT NULL,version INTEGER NOT NULL,payload TEXT NOT NULL,actor_id TEXT NOT NULL,saved_at TEXT NOT NULL,PRIMARY KEY(organization_id,user_id,record_key,version))',
)


class Profile(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    expected_version: int = Field(ge=0)
    employee_number: str = Field(min_length=1, max_length=40, pattern=r'^[A-Za-z0-9_-]+$')
    address: str = Field(default='', max_length=400)
    phone: str = Field(default='', max_length=20, pattern=r'^$|^\+[1-9][0-9]{7,14}$')
    starting_location: str = Field(default='', max_length=400)
    notes: str = Field(default='', max_length=1000)


class Qualification(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    expected_version: int = Field(ge=0)
    title: str = Field(min_length=2, max_length=160)
    issuer: str = Field(default='', max_length=160)
    credential_number: str = Field(default='', max_length=100)
    issued_on: date | None = None
    expires_on: date | None = None
    review_status: Literal['unreviewed', 'verified', 'rejected'] = 'unreviewed'
    evidence_reference: str = Field(default='', max_length=500)
    review_note: str = Field(default='', max_length=1000)

    @model_validator(mode='after')
    def valid_review(self):
        if self.issued_on and self.expires_on and self.expires_on < self.issued_on:
            raise ValueError('Expiry must not precede issue date')
        if self.issued_on and self.issued_on > datetime.now(timezone.utc).date():
            raise ValueError('Issue date must not be in the future')
        if self.review_status != 'unreviewed' and not self.review_note:
            raise ValueError('Review note is required')
        if self.review_status == 'verified' and (not self.evidence_reference or not self.issuer):
            raise ValueError('Verification requires issuer and evidence reference')
        return self


def qualification_state(payload, on_date=None):
    """Pure factual status, never a determination of job/agency eligibility."""
    on_date = on_date or datetime.now(timezone.utc).date()
    if payload.get('review_status') != 'verified':
        return payload.get('review_status', 'unreviewed')
    if not payload.get('expires_on'):
        return 'verified_expiry_unknown'
    if payload.get('expires_on') and date.fromisoformat(payload['expires_on']) < on_date:
        return 'expired'
    return 'verified_current'


def register(app, accounts):
    with accounts.connect() as db:
        for sql in DDL:
            db.execute(sql)

    def access(request, user_id=None, write=False):
        selected = accounts.actor(request)
        if (write or user_id is None) and selected['role'] != 'admin':
            raise HTTPException(403, 'Administrator access required')
        if user_id and selected['role'] != 'admin' and selected['id'] != user_id:
            raise HTTPException(404, 'Employee not found')
        return selected

    def member(db, org, user_id):
        row = db.execute('SELECT a.id,a.name,m.active FROM accounts a JOIN memberships m ON a.id=m.user_id WHERE m.organization_id=? AND a.id=?', (org, user_id)).fetchone()
        if not row:
            raise HTTPException(404, 'Employee not found')
        return row

    def packed(row):
        return {'version': row['version'], 'updated_at': row['updated_at'], **json.loads(row['payload'])} if row else None

    def save(db, selected, user_id, key, version, payload, stamp):
        db.execute('INSERT INTO employee_history VALUES (?,?,?,?,?,?,?)', (selected['organization_id'], user_id, key, version, payload, selected['id'], stamp))
        accounts.audit(db, selected['organization_id'], selected['id'], 'employee_'+key+'_saved', user_id)

    def active_admin(db, selected):
        row = db.execute('SELECT m.role FROM memberships m JOIN organizations o ON o.id=m.organization_id WHERE m.organization_id=? AND m.user_id=? AND m.active=1 AND o.active=1', (selected['organization_id'], selected['id'])).fetchone()
        if not row or row['role'] != 'admin':
            raise HTTPException(403, 'Active administrator access required')

    @app.get('/api/account/employees')
    def employees(request: Request, offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=50)):
        selected = access(request)
        with accounts.connect() as db:
            total = db.execute('SELECT COUNT(*) FROM memberships WHERE organization_id=?', (selected['organization_id'],)).fetchone()[0]
            rows = db.execute('SELECT a.id,a.name,m.active,p.employee_number,p.version FROM accounts a JOIN memberships m ON a.id=m.user_id LEFT JOIN employee_profiles p ON p.organization_id=m.organization_id AND p.user_id=a.id WHERE m.organization_id=? ORDER BY a.name,a.id LIMIT ? OFFSET ?', (selected['organization_id'], limit, offset)).fetchall()
        return {'items': [dict(r) for r in rows], 'total': total, 'offset': offset, 'limit': limit}

    @app.get('/api/account/employees/{user_id}')
    def employee(user_id: str, request: Request):
        selected = access(request, user_id)
        with accounts.connect() as db:
            db.execute('BEGIN')
            person = member(db, selected['organization_id'], user_id)
            profile = db.execute('SELECT * FROM employee_profiles WHERE organization_id=? AND user_id=?', (selected['organization_id'], user_id)).fetchone()
            rows = db.execute('SELECT * FROM employee_qualifications WHERE organization_id=? AND user_id=? ORDER BY qualification_id', (selected['organization_id'], user_id)).fetchall()
        qualifications = []
        for row in rows:
            item = packed(row)
            qualifications.append({'id': row['qualification_id'], **item, 'current_status': qualification_state(item)})
        return {**dict(person), 'profile': packed(profile), 'qualifications': qualifications}

    @app.put('/api/account/employees/{user_id}')
    def update_profile(user_id: str, body: Profile, request: Request):
        selected = access(request, user_id, write=True)
        payload = body.model_dump(exclude={'expected_version'})
        payload['employee_number'] = payload['employee_number'].upper()
        encoded = json.dumps(payload, sort_keys=True)
        stamp = datetime.now(timezone.utc).isoformat()
        org = selected['organization_id']
        with accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            active_admin(db, selected)
            member(db, org, user_id)
            row = db.execute('SELECT * FROM employee_profiles WHERE organization_id=? AND user_id=?', (org, user_id)).fetchone()
            version = row['version'] if row else 0
            if version != body.expected_version:
                if row and version == body.expected_version+1 and row['payload'] == encoded:
                    return packed(row)
                raise HTTPException(409, 'Employee changed. Reload before saving.')
            duplicate = db.execute('SELECT user_id FROM employee_profiles WHERE organization_id=? AND employee_number=? AND user_id<>?', (org, payload['employee_number'], user_id)).fetchone()
            if duplicate:
                raise HTTPException(409, 'Employee number already exists in this organization')
            db.execute('INSERT INTO employee_profiles VALUES (?,?,?,?,?,?) ON CONFLICT(organization_id,user_id) DO UPDATE SET employee_number=excluded.employee_number,payload=excluded.payload,version=excluded.version,updated_at=excluded.updated_at', (org, user_id, payload['employee_number'], encoded, version+1, stamp))
            save(db, selected, user_id, 'profile', version+1, encoded, stamp)
        return {'version': version+1, 'updated_at': stamp, **payload}

    @app.put('/api/account/employees/{user_id}/qualifications/{qualification_id}')
    def update_qualification(user_id: str, qualification_id: str, body: Qualification, request: Request):
        import re
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', qualification_id):
            raise HTTPException(422, 'Invalid qualification identifier')
        selected = access(request, user_id, write=True)
        payload = body.model_dump(mode='json', exclude={'expected_version'})
        encoded = json.dumps(payload, sort_keys=True)
        org = selected['organization_id']
        stamp = datetime.now(timezone.utc).isoformat()
        with accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            active_admin(db, selected)
            member(db, org, user_id)
            row = db.execute('SELECT * FROM employee_qualifications WHERE organization_id=? AND user_id=? AND qualification_id=?', (org, user_id, qualification_id)).fetchone()
            version = row['version'] if row else 0
            if version != body.expected_version:
                if row and version == body.expected_version+1 and row['payload'] == encoded:
                    return {**packed(row), 'current_status': qualification_state(payload)}
                raise HTTPException(409, 'Qualification changed. Reload before saving.')
            if row is None:
                count = db.execute('SELECT COUNT(*) FROM employee_qualifications WHERE organization_id=? AND user_id=?', (org, user_id)).fetchone()[0]
                if count >= 100:
                    raise HTTPException(422, 'Employee qualification limit reached')
            db.execute('INSERT INTO employee_qualifications VALUES (?,?,?,?,?,?) ON CONFLICT(organization_id,user_id,qualification_id) DO UPDATE SET payload=excluded.payload,version=excluded.version,updated_at=excluded.updated_at', (org, user_id, qualification_id, encoded, version+1, stamp))
            save(db, selected, user_id, 'qualification:'+qualification_id, version+1, encoded, stamp)
        return {'version': version+1, 'updated_at': stamp, **payload, 'current_status': qualification_state(payload)}

    @app.get('/api/account/employees/{user_id}/history')
    def history(user_id: str, request: Request, offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=50)):
        selected = access(request, user_id)
        with accounts.connect() as db:
            member(db, selected['organization_id'], user_id)
            rows = db.execute('SELECT record_key,version,payload,actor_id,saved_at FROM employee_history WHERE organization_id=? AND user_id=? ORDER BY saved_at DESC,record_key,version DESC LIMIT ? OFFSET ?', (selected['organization_id'], user_id, limit, offset)).fetchall()
        return {'items': [{**dict(r), 'payload': json.loads(r['payload'])} for r in rows], 'offset': offset, 'limit': limit}
