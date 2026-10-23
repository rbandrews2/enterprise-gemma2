"""Reviewed organization roster imports; never provisions identities or sends messages."""
import csv
import hashlib
import io
import json
import re
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import Response

DDL = (
    'CREATE TABLE IF NOT EXISTS employee_roster (organization_id TEXT NOT NULL,email TEXT NOT NULL,employee_number TEXT NOT NULL,name TEXT NOT NULL,phone TEXT NOT NULL,import_id TEXT NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(organization_id,email),UNIQUE(organization_id,employee_number))',
    'CREATE TABLE IF NOT EXISTS employee_import_batches (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,actor_id TEXT NOT NULL,payload TEXT NOT NULL,fingerprint TEXT NOT NULL,expires_at TEXT NOT NULL,receipt TEXT)',
)
COLUMNS = ('name', 'email', 'employee_number', 'phone')
MAX_BYTES = 512 * 1024


class Upload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    csv_text: str = Field(min_length=1, max_length=MAX_BYTES)


class Confirmation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    reviewed: bool


def parse_csv(text, emails, numbers):
    if len(text.encode('utf-8')) > MAX_BYTES or '\x00' in text:
        raise HTTPException(422, 'Use a UTF-8 CSV file no larger than 512 KiB.')
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff'), newline=''), strict=True)
    try:
        headers = reader.fieldnames
        if not headers or len(set(headers)) != len(headers) or not set(COLUMNS[:3]).issubset(headers) or set(headers) - set(COLUMNS):
            raise HTTPException(422, 'Use the template columns: name, email, employee_number, phone.')
        rows = []
        for record in reader:
            if len(rows) >= 500:
                raise HTTPException(422, 'Import up to 500 employees at a time.')
            errors = []
            values = {k: (record.get(k) or '').strip() for k in COLUMNS}
            values['email'] = values['email'].lower()
            values['employee_number'] = values['employee_number'].upper()
            if None in record or any(record.get(k) is None for k in headers):
                errors.append('Column count does not match the template.')
            if not 2 <= len(values['name']) <= 120 or any(ord(c) < 32 for c in values['name']):
                errors.append('Enter a name between 2 and 120 characters.')
            if len(values['email']) > 254 or not re.fullmatch(r'[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+', values['email']):
                errors.append('Enter a valid email address.')
            if not re.fullmatch(r'[A-Z0-9_-]{1,40}', values['employee_number']):
                errors.append('Employee number: use 1–40 letters, numbers, underscores or hyphens.')
            if values['phone'] and not re.fullmatch(r'\+[1-9][0-9]{7,14}', values['phone']):
                errors.append('Phone: use international format, for example +15405550123.')
            duplicate = []
            if values['email'] in emails:
                duplicate.append('Email already appears in this organization or file.')
            if values['employee_number'] in numbers:
                duplicate.append('Employee number already appears in this organization or file.')
            emails.add(values['email']); numbers.add(values['employee_number'])
            rows.append({'row': len(rows)+2, **values, 'status': 'error' if errors else ('duplicate' if duplicate else 'ready'), 'issues': errors + duplicate})
    except csv.Error:
        raise HTTPException(422, 'CSV could not be read. Save it as UTF-8 CSV and try again.') from None
    if not rows:
        raise HTTPException(422, 'Add at least one employee below the template headers.')
    return rows


def register(app, accounts):
    with accounts.connect() as db:
        for sql in DDL:
            db.execute(sql)

    def admin(request):
        actor = accounts.actor(request)
        if actor['role'] != 'admin':
            raise HTTPException(403, 'Administrator access required')
        return actor

    def lock(db, actor):
        org = actor['organization_id']
        db.execute('UPDATE organizations SET active=active WHERE id=?', (org,))
        current = db.execute('SELECT m.role FROM memberships m JOIN organizations o ON o.id=m.organization_id WHERE m.organization_id=? AND m.user_id=? AND m.active=1 AND o.active=1', (org, actor['id'])).fetchone()
        if not current or current['role'] != 'admin':
            raise HTTPException(403, 'Active administrator access required')

    def existing(db, org):
        roster = [dict(r) for r in db.execute('SELECT email,employee_number FROM employee_roster WHERE organization_id=? ORDER BY email', (org,)).fetchall()]
        members = [dict(r) for r in db.execute('SELECT a.id,a.email,m.active,p.employee_number FROM accounts a JOIN memberships m ON m.user_id=a.id LEFT JOIN employee_profiles p ON p.user_id=a.id AND p.organization_id=m.organization_id WHERE m.organization_id=? ORDER BY a.id', (org,)).fetchall()]
        fingerprint = hashlib.sha256(json.dumps([roster, members], sort_keys=True).encode()).hexdigest()
        return fingerprint, {r['email'].lower() for r in roster+members}, {r['employee_number'] for r in roster+members if r['employee_number']}

    @app.get('/api/account/employee-import/template')
    def template(request: Request):
        admin(request)
        return Response('name,email,employee_number,phone\r\n', media_type='text/csv', headers={'Content-Disposition': 'attachment; filename="wzos-employees-template.csv"', 'Cache-Control': 'no-store'})

    @app.get('/api/account/employee-import/roster')
    def roster(request: Request, offset: int = Query(0, ge=0)):
        actor = admin(request)
        with accounts.connect() as db:
            total = db.execute('SELECT COUNT(*) FROM employee_roster WHERE organization_id=?', (actor['organization_id'],)).fetchone()[0]
            rows = db.execute('SELECT name,email,employee_number,phone FROM employee_roster WHERE organization_id=? ORDER BY name,email LIMIT 25 OFFSET ?', (actor['organization_id'], offset)).fetchall()
        return {'items': [dict(r) for r in rows], 'total': total, 'offset': offset, 'limit': 25}

    @app.post('/api/account/employee-import/review')
    def review(body: Upload, request: Request):
        actor = admin(request)
        now = datetime.now(timezone.utc)
        identifier = str(uuid4())
        with accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            lock(db, actor)
            db.execute('DELETE FROM employee_import_batches WHERE organization_id=? AND expires_at<?', (actor['organization_id'], now.isoformat()))
            count = db.execute('SELECT COUNT(*) FROM employee_import_batches WHERE organization_id=?', (actor['organization_id'],)).fetchone()[0]
            if count >= 20:
                raise HTTPException(429, 'Too many recent imports. Wait 30 minutes before reviewing another file.')
            fingerprint, emails, numbers = existing(db, actor['organization_id'])
            rows = parse_csv(body.csv_text, emails, numbers)
            db.execute('INSERT INTO employee_import_batches VALUES (?,?,?,?,?,?,NULL)', (identifier, actor['organization_id'], actor['id'], json.dumps(rows), fingerprint, (now+timedelta(minutes=30)).isoformat()))
        return {'id': identifier, 'rows': rows, 'ready': sum(r['status']=='ready' for r in rows), 'duplicates': sum(r['status']=='duplicate' for r in rows), 'errors': sum(r['status']=='error' for r in rows)}

    @app.post('/api/account/employee-import/{batch_id}/confirm')
    def confirm(batch_id: UUID, body: Confirmation, request: Request):
        actor = admin(request)
        if not body.reviewed:
            raise HTTPException(422, 'Review the rows before confirming the import.')
        now = datetime.now(timezone.utc).isoformat()
        with accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            lock(db, actor)
            batch = db.execute('SELECT * FROM employee_import_batches WHERE id=? AND organization_id=? AND actor_id=?', (str(batch_id), actor['organization_id'], actor['id'])).fetchone()
            if not batch:
                raise HTTPException(404, 'Import review not found')
            if batch['receipt']:
                return json.loads(batch['receipt'])
            if batch['expires_at'] < now:
                raise HTTPException(409, 'Review expired. Upload the file again.')
            if existing(db, actor['organization_id'])[0] != batch['fingerprint']:
                raise HTTPException(409, 'The employee list changed. Upload again to review current duplicates.')
            rows = json.loads(batch['payload'])
            ready = [r for r in rows if r['status']=='ready']
            if not ready or any(r['status']=='error' for r in rows):
                raise HTTPException(422, 'Correct the errors and upload again before importing.')
            for row in ready:
                db.execute('INSERT INTO employee_roster VALUES (?,?,?,?,?,?,?)', (actor['organization_id'], row['email'], row['employee_number'], row['name'], row['phone'], str(batch_id), now))
            receipt = {'id': str(batch_id), 'imported': len(ready), 'skipped': len(rows)-len(ready), 'completed_at': now}
            db.execute('UPDATE employee_import_batches SET receipt=? WHERE id=?', (json.dumps(receipt), str(batch_id)))
            accounts.audit(db, actor['organization_id'], actor['id'], 'employee_roster_imported', str(batch_id))
        return receipt
