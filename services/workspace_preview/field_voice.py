"""Enterprise voice-assisted drafts. Model output is never an autonomous action."""
import asyncio
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Annotated, Literal
from uuid import UUID, uuid5, NAMESPACE_URL

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .field_voice_transport import Extractor, Speech, MAX_AUDIO
from .form_submissions import CompletedForm, printable_snapshot
from .forms_hub import load_catalog
from .intelligence import ModelUnavailable

DDL = (
    'CREATE TABLE IF NOT EXISTS field_voice_drafts (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,owner_id TEXT NOT NULL,job_id TEXT NOT NULL,job_version INTEGER NOT NULL,version INTEGER NOT NULL,payload TEXT NOT NULL,state TEXT NOT NULL,model TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,submission_ids TEXT NOT NULL)',
    'CREATE INDEX IF NOT EXISTS field_voice_drafts_org_owner ON field_voice_drafts(organization_id,owner_id,updated_at)',
)


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Quantity(Strict):
    item_name: str = Field(min_length=1, max_length=160)
    quantity: float | None = Field(default=None, ge=0, le=1e10, allow_inf_nan=False, strict=True)
    unit: str | None = Field(default=None, max_length=60)


class Incident(Strict):
    details: str = Field(min_length=1, max_length=2000)
    time_mentioned: str | None = Field(default=None, max_length=100)
    priority: Literal['low', 'medium', 'high'] | None = None


class Report(Strict):
    schema_version: Literal[1] = 1
    is_relevant: bool = Field(strict=True)
    route_location: str | None = Field(default=None, max_length=500)
    work_description: str | None = Field(default=None, max_length=2000)
    production_quantities: list[Quantity] = Field(default_factory=list, max_length=30)
    incidents: list[Incident] = Field(default_factory=list, max_length=8)
    unresolved: list[Annotated[str, Field(max_length=300)]] = Field(default_factory=list, max_length=20)


class Basis(Strict):
    job_id: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')
    expected_job_version: int = Field(ge=1, strict=True)


class Extract(Basis):
    transcript: str = Field(min_length=5, max_length=6000)


class Fields(Strict):
    work_date: date | None = None
    report: Report


class Draft(Basis):
    request_id: UUID
    fields: Fields


class Patch(Strict):
    expected_version: int = Field(ge=1, strict=True)
    fields: Fields


class Send(Strict):
    expected_version: int = Field(ge=1, strict=True)
    reviewed: Literal[True]


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def register(app, connect, actor, permitted_row, roster, *, accounts=False):
    with connect() as db:
        for sql in DDL:
            db.execute(sql)
    templates, _ = load_catalog()
    app.state.field_voice_extractor = Extractor()
    app.state.field_voice_speech = Speech()
    inflight, rates = set(), defaultdict(deque)
    concurrency = asyncio.Semaphore(2)

    def access(request, enabled=True):
        user = actor(request)
        if user['edition'] != 'enterprise':
            raise HTTPException(403, 'Smart Field Voice requires Enterprise.')
        if enabled and os.getenv('WZOS_FIELD_VOICE_ENABLED') != '1':
            raise HTTPException(503, 'Smart Field Voice is not enabled.')
        return user

    def job(db, user, ident, version=None):
        try:
            row = permitted_row(db, str(ident), user)
            details = json.loads(row['payload'])
        except HTTPException as error:
            if error.status_code != 404 or not accounts:
                raise
            assignment = db.execute("""SELECT p.payload FROM dispatch_assignments a JOIN dispatch_plans p
                ON p.id=a.plan_id AND p.organization_id=a.organization_id
                WHERE a.order_id=? AND a.organization_id=? AND a.user_id=?
                AND a.status IN ('sent','accepted') AND p.status='sent' ORDER BY a.created_at DESC LIMIT 1""",
                (str(ident), user['organization_id'], user['id'])).fetchone()
            if not assignment:
                raise error
            row = db.execute('SELECT id,version FROM preview_orders WHERE id=? AND organization_id=?',
                (str(ident), user['organization_id'])).fetchone()
            if not row:
                raise error
            snapshot = json.loads(assignment['payload']).get('delivery_snapshot')
            if not snapshot:
                raise HTTPException(409, 'Ask your admin to refresh the dispatched job details.')
            details = {'title': snapshot.get('order_title'), 'address': snapshot.get('address')}
        if version is not None and version != row['version']:
            raise HTTPException(409, 'The job changed. Reload and review before continuing.')
        return {'id': str(ident), 'version': row['version'],
                'title': details.get('title') or 'Assigned job', 'address': details.get('address') or ''}

    @asynccontextmanager
    async def gate(user):
        key = (user['organization_id'], user['id']); now = time.monotonic()
        for old in list(rates):
            while rates[old] and rates[old][0] < now-60:
                rates[old].popleft()
            if not rates[old]:
                del rates[old]
        if key in inflight or len(inflight) >= 2 or len(rates) > 2000 or len(rates[key]) >= 6:
            raise HTTPException(429, 'Atlas is busy. Wait before explicitly trying again.')
        rates[key].append(now); inflight.add(key)
        try:
            async with concurrency:
                yield
        finally:
            inflight.discard(key)

    def get_draft(db, user, ident):
        row = db.execute('SELECT * FROM field_voice_drafts WHERE id=? AND organization_id=?',
                         (str(ident), user['organization_id'])).fetchone()
        if not row or (user['role'] != 'admin' and row['owner_id'] != user['id']):
            raise HTTPException(404, 'Field report not found.')
        job(db, user, row['job_id'])
        return row

    def serialize(row):
        value = dict(row); value['fields'] = json.loads(value.pop('payload'))
        value['submission_ids'] = json.loads(value['submission_ids'])
        return value

    @app.get('/field-voice.js')
    def script():
        return FileResponse(Path(__file__).with_name('static')/'field-voice.js', media_type='text/javascript')

    @app.get('/device-setup.js')
    def setup_script():
        return FileResponse(Path(__file__).with_name('static')/'device-setup.js', media_type='text/javascript')

    @app.get('/field-voice.css')
    def style():
        return FileResponse(Path(__file__).with_name('static')/'field-voice.css', media_type='text/css')

    @app.get('/api/field-voice/config')
    def config(request: Request):
        access(request, False)
        return {'enabled': os.getenv('WZOS_FIELD_VOICE_ENABLED') == '1',
                'speech_enabled': os.getenv('WZOS_FIELD_VOICE_SPEECH_ENABLED') == '1',
                'max_seconds': 30, 'max_bytes': MAX_AUDIO, 'audio_retained': False}

    @app.get('/api/field-voice/jobs')
    def jobs(request: Request):
        user = access(request); result = []
        with connect() as db:
            query = 'SELECT id FROM preview_orders WHERE organization_id=?'
            params = [user['organization_id']]
            if user['role'] != 'admin':
                query += ' AND (owner_id=?'
                params.append(user['id'])
                if accounts:
                    query += " OR id IN (SELECT a.order_id FROM dispatch_assignments a JOIN dispatch_plans p ON p.id=a.plan_id AND p.organization_id=a.organization_id WHERE a.organization_id=? AND a.user_id=? AND a.status IN ('sent','accepted') AND p.status='sent')"
                    params.extend([user['organization_id'], user['id']])
                query += ')'
            ids = db.execute(query+' ORDER BY updated_at DESC LIMIT 100', params).fetchall()
            for row in ids:
                try:
                    result.append(job(db, user, row['id']))
                except HTTPException as error:
                    if error.status_code not in (404, 409):
                        raise
        return {'items': result, 'limit': 100}

    @app.post('/api/field-voice/transcribe')
    async def transcribe(request: Request, job_id: str, expected_job_version: int):
        user = access(request)
        with connect() as db:
            job(db, user, job_id, expected_job_version)
        if request.headers.get('content-type', '').split(';')[0] != 'audio/wav':
            raise HTTPException(415, 'Use a WAV recording.')
        async with gate(user):
            audio = bytearray()
            try:
                async for chunk in request.stream():
                    if len(audio)+len(chunk) > MAX_AUDIO:
                        raise HTTPException(413, 'Recording exceeds 6 MiB.')
                    audio.extend(chunk)
                text = await app.state.field_voice_speech.transcribe(bytes(audio))
                return {'transcript': text, 'audio_retained': False}
            except ValueError:
                raise HTTPException(422, 'Use a complete WAV recording of at most 30 seconds.') from None
            except ModelUnavailable as error:
                raise HTTPException(503, str(error)) from None
            finally:
                audio.clear()

    @app.post('/api/field-voice/extract')
    async def extract(body: Extract, request: Request):
        user = access(request)
        with connect() as db:
            selected = job(db, user, body.job_id, body.expected_job_version)
        async with gate(user):
            try:
                result = Report.model_validate(await app.state.field_voice_extractor.extract(
                    body.transcript, selected, Report.model_json_schema()))
            except (ValidationError, ModelUnavailable, ValueError):
                raise HTTPException(503, 'Atlas could not produce a valid draft. Your text is unchanged.') from None
        if not result.is_relevant or not (result.work_description or result.production_quantities or result.incidents):
            raise HTTPException(422, 'No actionable field-work details were found. Nothing was saved.')
        if result.route_location and result.route_location.casefold() != selected['address'].casefold():
            result.unresolved = (result.unresolved + ['Compare the spoken location with the selected job.'])[:20]
        return {'job': selected, 'fields': {'work_date': None, 'report': result.model_dump()},
                'saved': False, 'model': Extractor.model}

    @app.post('/api/field-voice/drafts')
    def create(body: Draft, request: Request):
        user = access(request); ident = str(body.request_id)
        payload = packed(body.fields.model_dump(mode='json')); now = datetime.now(timezone.utc).isoformat()
        if not body.fields.report.is_relevant:
            raise HTTPException(422, 'Review relevant field-work details first.')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE'); job(db, user, body.job_id, body.expected_job_version)
            prior = db.execute('SELECT * FROM field_voice_drafts WHERE id=?', (ident,)).fetchone()
            if prior:
                if (prior['organization_id'], prior['owner_id'], prior['job_id'], prior['job_version'], prior['payload']) != (
                        user['organization_id'], user['id'], str(body.job_id), body.expected_job_version, payload):
                    raise HTTPException(409, 'Draft retry conflict.')
                return serialize(prior)
            db.execute('INSERT INTO field_voice_drafts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                (ident, user['organization_id'], user['id'], str(body.job_id), body.expected_job_version,
                 1, payload, 'draft', Extractor.model, now, now, '[]'))
            return serialize(db.execute('SELECT * FROM field_voice_drafts WHERE id=?', (ident,)).fetchone())

    @app.get('/api/field-voice/drafts')
    def listing(request: Request):
        user = access(request); output = []
        with connect() as db:
            rows = db.execute('SELECT * FROM field_voice_drafts WHERE organization_id=? ORDER BY updated_at DESC LIMIT 100',
                              (user['organization_id'],)).fetchall()
            for row in rows:
                try:
                    output.append(serialize(get_draft(db, user, row['id'])))
                except HTTPException as error:
                    if error.status_code != 404:
                        raise
        return {'items': output}

    @app.get('/api/field-voice/drafts/{ident}')
    def read(ident: UUID, request: Request):
        user = access(request)
        with connect() as db:
            return serialize(get_draft(db, user, ident))

    @app.patch('/api/field-voice/drafts/{ident}')
    def update(ident: UUID, body: Patch, request: Request):
        user = access(request)
        if not body.fields.report.is_relevant:
            raise HTTPException(422, 'Keep relevant field-work details only.')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE'); row = get_draft(db, user, ident)
            job(db, user, row['job_id'], row['job_version'])
            if row['state'] != 'draft' or row['version'] != body.expected_version:
                raise HTTPException(409, 'The draft changed or was submitted. Reload before editing.')
            db.execute('UPDATE field_voice_drafts SET payload=?,version=version+1,updated_at=? WHERE id=?',
                (packed(body.fields.model_dump(mode='json')), datetime.now(timezone.utc).isoformat(), str(ident)))
            return serialize(get_draft(db, user, ident))

    @app.post('/api/field-voice/drafts/{ident}/send-to-office')
    def send(ident: UUID, body: Send, request: Request):
        user = access(request); now = datetime.now(timezone.utc).isoformat()
        # Resolve recipients outside the write transaction; roster remains tenant scoped.
        admins = [r for r in roster(user).values() if r['organization_id'] == user['organization_id'] and r['role'] == 'admin']
        with connect() as db:
            db.execute('BEGIN IMMEDIATE'); row = get_draft(db, user, ident)
            if row['state'] == 'sent' and row['version'] == body.expected_version+1:
                return serialize(row)
            if row['state'] != 'draft' or row['version'] != body.expected_version:
                raise HTTPException(409, 'Reload the current draft before sending.')
            selected = job(db, user, row['job_id'], row['job_version'])
            fields = Fields.model_validate_json(row['payload']); report = fields.report
            if not fields.work_date or not report.work_description:
                raise HTTPException(422, 'Confirm the work date and work description.')
            if any(q.quantity is None or not q.unit for q in report.production_quantities):
                raise HTTPException(422, 'Resolve or remove quantities with an unknown value or unit.')
            docs = [('daily-work-report', {'work_date': fields.work_date.isoformat(),
                'description': report.work_description, 'reported_by': user['name'],
                'quantities': [{'item': q.item_name, 'quantity': str(q.quantity), 'unit': q.unit} for q in report.production_quantities]})]
            for incident in report.incidents:
                docs.append(('incident', {'description': incident.details + (
                    '\nTime reported (not independently verified): '+incident.time_mentioned if incident.time_mentioned else ''),
                    'follow_up': 'Reviewed priority: '+(incident.priority or 'Not specified'), 'reported_by': user['name']}))
            submissions = []
            audit = {'assisted_by': 'Atlas', 'model': row['model'], 'schema_version': 1,
                     'reviewed_by': user['id'], 'reviewed_at': now, 'bundle_id': str(ident)}
            for index, (template, values) in enumerate(docs):
                sid = str(uuid5(NAMESPACE_URL, 'wzos-field-voice:'+str(ident)+':'+str(index)))
                snapshot = printable_snapshot(CompletedForm(request_id=sid, template_id=template,
                    template_revision=1, fields=values, order=selected['title'], location=selected['address']), templates)
                snapshot['field_voice_review'] = audit
                payload = packed(snapshot)
                db.execute('INSERT INTO form_submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (sid, user['organization_id'], sid, 1, user['id'], payload,
                     hashlib.sha256(payload.encode()).hexdigest(), 'received', 1, now, None, None, ''))
                submissions.append(sid)
            summary = f"Reviewed field report: {selected['title']}. {len(report.production_quantities)} production entries; {len(report.incidents)} incident reports. Open Forms hub for office review."
            for admin in admins:
                mid = str(uuid5(NAMESPACE_URL, 'wzos-field-voice-notice:'+str(ident)+':'+admin['id']))
                db.execute('INSERT INTO fixture_messages VALUES (?,?,?,?,?,?)',
                    (mid, user['organization_id'], user['id'], admin['id'], summary, now))
                db.execute('INSERT INTO message_receipts VALUES (?,?,?,?,?)', (user['organization_id'], mid, admin['id'], 0, None))
            # Deliberately no SMS helper, queue or background send.
            db.execute("UPDATE field_voice_drafts SET state='sent',version=version+1,updated_at=?,submission_ids=? WHERE id=?",
                       (now, packed(submissions), str(ident)))
            return serialize(get_draft(db, user, ident))
