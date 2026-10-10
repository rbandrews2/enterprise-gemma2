"""Organization-authored training modules, assignments, scored assessments and completions.

Three different things stay separate:
- self-reported study (training_records): the member's own statement, admin-reviewed;
- assessment completion (here): WZOS scored a passing attempt on a published version;
- verified qualifications (Codex's employee contract): only an admin verifies those.
Nothing here issues a certificate or a qualification. Media are links the organization
attests it may use; WZOS does not host or embed third-party video.
"""
import json
from datetime import date, datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from fastapi import HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

DDL = (
    'CREATE TABLE IF NOT EXISTS training_modules (organization_id TEXT NOT NULL,id TEXT NOT NULL,status TEXT NOT NULL,published_version INTEGER NOT NULL,draft TEXT NOT NULL,draft_version INTEGER NOT NULL,updated_by TEXT NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(organization_id,id))',
    'CREATE TABLE IF NOT EXISTS training_module_versions (organization_id TEXT NOT NULL,module_id TEXT NOT NULL,version INTEGER NOT NULL,payload TEXT NOT NULL,published_by TEXT NOT NULL,published_at TEXT NOT NULL,PRIMARY KEY(organization_id,module_id,version))',
    'CREATE TABLE IF NOT EXISTS training_assignments (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,module_id TEXT NOT NULL,module_version INTEGER NOT NULL,user_id TEXT NOT NULL,due_on TEXT,status TEXT NOT NULL,assigned_by TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(organization_id,module_id,module_version,user_id))',
    'CREATE TABLE IF NOT EXISTS training_attempts (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,user_id TEXT NOT NULL,module_id TEXT NOT NULL,module_version INTEGER NOT NULL,answers TEXT NOT NULL,score INTEGER NOT NULL,passed INTEGER NOT NULL,submitted_at TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS training_completions (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,user_id TEXT NOT NULL,module_id TEXT NOT NULL,module_version INTEGER NOT NULL,attempt_id TEXT NOT NULL,score INTEGER NOT NULL,completed_at TEXT NOT NULL,UNIQUE(organization_id,user_id,module_id,module_version))',
)
MODULE_ID = r'^[a-z0-9][a-z0-9_-]{0,59}$'


def now():
    return datetime.now(timezone.utc).isoformat()


class Section(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    heading: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=8000)


class Media(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=160)
    url: str = Field(pattern=r'^https://[^\s]{4,500}$')
    rights_confirmed: bool = Field(strict=True)
    rights_note: str = Field(min_length=5, max_length=500)

    @model_validator(mode='after')
    def rights(self):
        if not self.rights_confirmed:
            raise ValueError('Confirm your organization may use this media for training')
        return self


class Question(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    prompt: str = Field(min_length=3, max_length=1000)
    options: list[str] = Field(min_length=2, max_length=6)
    answer: int = Field(ge=0, strict=True)

    @model_validator(mode='after')
    def valid(self):
        if any(not o or len(o) > 300 for o in self.options) or len(set(self.options)) != len(self.options):
            raise ValueError('Options must be distinct and at most 300 characters')
        if self.answer >= len(self.options):
            raise ValueError('The correct answer must be one of the options')
        return self


class Draft(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    expected_version: int = Field(ge=0)
    title: str = Field(min_length=2, max_length=160)
    summary: str = Field(default='', max_length=1000)
    sections: list[Section] = Field(default_factory=list, max_length=30)
    media: list[Media] = Field(default_factory=list, max_length=10)
    questions: list[Question] = Field(default_factory=list, max_length=50)
    passing_score: int = Field(default=80, ge=50, le=100, strict=True)
    max_attempts: int = Field(default=3, ge=1, le=10, strict=True)


class Publish(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_version: int = Field(ge=1)


class Assign(BaseModel):
    model_config = ConfigDict(extra='forbid')
    module_id: str = Field(pattern=MODULE_ID)
    user_ids: list[str] = Field(min_length=1, max_length=100)
    due_on: date | None = None


class Attempt(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: UUID
    module_version: int = Field(ge=1)
    answers: list[int] = Field(max_length=50)


def register(app, connect, actor, actors):
    with connect() as db:
        for sql in DDL:
            db.execute(sql)

    def admin(request):
        user = actor(request)
        if user['role'] != 'admin':
            raise HTTPException(403, 'Administrator access required')
        return user

    def module_row(db, org, module_id):
        row = db.execute('SELECT * FROM training_modules WHERE organization_id=? AND id=?', (org, module_id)).fetchone()
        if not row:
            raise HTTPException(404, 'Training module not found')
        return row

    def published(db, org, module_id, version):
        row = db.execute('SELECT * FROM training_module_versions WHERE organization_id=? AND module_id=? AND version=?', (org, module_id, version)).fetchone()
        if not row:
            raise HTTPException(404, 'Published training version not found')
        return json.loads(row['payload'])

    def learner_view(payload, module_id, version):
        """Content and questions for members; answers never leave the server."""
        return {'id': module_id, 'version': version, **{k: payload[k] for k in ('title', 'summary', 'sections', 'media', 'passing_score', 'max_attempts')},
                'questions': [{'prompt': q['prompt'], 'options': q['options']} for q in payload['questions']],
                'certificate_issued': False, 'qualification_issued': False}

    def admin_view(row):
        return {'id': row['id'], 'status': row['status'], 'published_version': row['published_version'], 'draft_version': row['draft_version'],
                'draft': json.loads(row['draft']), 'updated_at': row['updated_at']}

    @app.get('/api/training-modules')
    def modules(request: Request):
        user = actor(request)
        with connect() as db:
            rows = db.execute('SELECT * FROM training_modules WHERE organization_id=? ORDER BY id', (user['organization_id'],)).fetchall()
            if user['role'] == 'admin':
                return {'items': [admin_view(r) for r in rows]}
            items = [learner_view(published(db, user['organization_id'], r['id'], r['published_version']), r['id'], r['published_version'])
                     for r in rows if r['status'] == 'published']
        return {'items': items}

    @app.put('/api/training-modules/{module_id}')
    def save_draft(module_id: str, body: Draft, request: Request):
        user = admin(request)
        import re
        if not re.fullmatch(MODULE_ID, module_id):
            raise HTTPException(422, 'Module identifiers use lowercase letters, digits, hyphens or underscores')
        draft = json.dumps(body.model_dump(exclude={'expected_version'}), sort_keys=True)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM training_modules WHERE organization_id=? AND id=?', (user['organization_id'], module_id)).fetchone()
            version = row['draft_version'] if row else 0
            if version != body.expected_version:
                if row and version == body.expected_version + 1 and row['draft'] == draft:
                    return admin_view(row)
                raise HTTPException(409, 'This training module changed. Reload before saving.')
            if row:
                db.execute('UPDATE training_modules SET draft=?,draft_version=?,updated_by=?,updated_at=? WHERE organization_id=? AND id=?',
                           (draft, version + 1, user['id'], now(), user['organization_id'], module_id))
            else:
                db.execute('INSERT INTO training_modules VALUES (?,?,?,?,?,?,?,?)', (user['organization_id'], module_id, 'draft', 0, draft, 1, user['id'], now()))
            return admin_view(module_row(db, user['organization_id'], module_id))

    @app.post('/api/training-modules/{module_id}/publish')
    def publish(module_id: str, body: Publish, request: Request):
        user = admin(request)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = module_row(db, user['organization_id'], module_id)
            draft = json.loads(row['draft'])
            if row['draft_version'] != body.expected_version:
                raise HTTPException(409, 'This training module changed. Reload before publishing.')
            if row['published_version']:
                current = published(db, user['organization_id'], module_id, row['published_version'])
                if current == draft and row['status'] == 'published':
                    return admin_view(row)
            if not draft['questions']:
                raise HTTPException(422, 'Add at least one assessment question before publishing')
            if not draft['sections'] and not draft['media']:
                raise HTTPException(422, 'Add training content before publishing')
            version = row['published_version'] + 1
            db.execute('INSERT INTO training_module_versions VALUES (?,?,?,?,?,?)', (user['organization_id'], module_id, version, row['draft'], user['id'], now()))
            db.execute("UPDATE training_modules SET status='published',published_version=?,updated_at=? WHERE organization_id=? AND id=?", (version, now(), user['organization_id'], module_id))
            return admin_view(module_row(db, user['organization_id'], module_id))

    @app.post('/api/training-modules/{module_id}/retire')
    def retire(module_id: str, request: Request):
        user = admin(request)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            module_row(db, user['organization_id'], module_id)
            db.execute("UPDATE training_modules SET status='retired',updated_at=? WHERE organization_id=? AND id=?", (now(), user['organization_id'], module_id))
            db.execute("UPDATE training_assignments SET status='cancelled',updated_at=? WHERE organization_id=? AND module_id=? AND status='assigned'", (now(), user['organization_id'], module_id))
            return admin_view(module_row(db, user['organization_id'], module_id))

    @app.get('/api/training-modules/{module_id}/versions/{version}')
    def read_version(module_id: str, version: int, request: Request):
        user = actor(request)
        with connect() as db:
            row = module_row(db, user['organization_id'], module_id)
            payload = published(db, user['organization_id'], module_id, version)
            if user['role'] != 'admin' and row['status'] != 'published' and not db.execute(
                    'SELECT 1 FROM training_assignments WHERE organization_id=? AND module_id=? AND module_version=? AND user_id=?', (user['organization_id'], module_id, version, user['id'])).fetchone():
                raise HTTPException(404, 'Training module not found')
        return learner_view(payload, module_id, version)

    @app.post('/api/training-assignments')
    def assign(body: Assign, request: Request):
        user = admin(request)
        team = {k for k, v in actors(user).items() if v['organization_id'] == user['organization_id']}
        if not set(body.user_ids) <= team or len(set(body.user_ids)) != len(body.user_ids):
            raise HTTPException(422, 'Assign distinct active members of this organization')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = module_row(db, user['organization_id'], body.module_id)
            if row['status'] != 'published':
                raise HTTPException(409, 'Publish this module before assigning it')
            created = []
            for uid in body.user_ids:
                existing = db.execute('SELECT * FROM training_assignments WHERE organization_id=? AND module_id=? AND module_version=? AND user_id=?',
                                      (user['organization_id'], body.module_id, row['published_version'], uid)).fetchone()
                if existing:
                    created.append(dict(existing))
                    continue
                assignment_id, stamp = str(uuid4()), now()
                db.execute('INSERT INTO training_assignments VALUES (?,?,?,?,?,?,?,?,?,?)', (assignment_id, user['organization_id'], body.module_id, row['published_version'], uid,
                                                                                            body.due_on.isoformat() if body.due_on else None, 'assigned', user['id'], stamp, stamp))
                created.append(dict(db.execute('SELECT * FROM training_assignments WHERE id=?', (assignment_id,)).fetchone()))
        return {'items': created}

    @app.post('/api/training-assignments/{assignment_id}/cancel')
    def cancel_assignment(assignment_id: UUID, request: Request):
        user = admin(request)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM training_assignments WHERE id=? AND organization_id=?', (str(assignment_id), user['organization_id'])).fetchone()
            if not row:
                raise HTTPException(404, 'Assignment not found')
            if row['status'] == 'completed':
                raise HTTPException(409, 'Completed training stays on record')
            db.execute("UPDATE training_assignments SET status='cancelled',updated_at=? WHERE id=?", (now(), row['id']))
            return dict(db.execute('SELECT * FROM training_assignments WHERE id=?', (row['id'],)).fetchone())

    @app.get('/api/training-assignments')
    def assignments(request: Request, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
        user = actor(request)
        clause, params = 'a.organization_id=?', [user['organization_id']]
        if user['role'] != 'admin':
            clause += ' AND a.user_id=?'
            params.append(user['id'])
        with connect() as db:
            rows = db.execute('SELECT a.*,(SELECT COUNT(*) FROM training_attempts t WHERE t.organization_id=a.organization_id AND t.user_id=a.user_id AND t.module_id=a.module_id AND t.module_version=a.module_version) AS attempts FROM training_assignments a WHERE '
                              + clause + ' ORDER BY a.created_at DESC,a.id LIMIT ? OFFSET ?', [*params, limit, offset]).fetchall()
            titles = {r['id']: json.loads(r['draft'])['title'] for r in db.execute('SELECT id,draft FROM training_modules WHERE organization_id=?', (user['organization_id'],)).fetchall()}
        return {'items': [{**dict(r), 'title': titles.get(r['module_id'], r['module_id'])} for r in rows]}

    @app.post('/api/training-modules/{module_id}/attempts')
    def attempt(module_id: str, body: Attempt, request: Request):
        user = actor(request)
        org = user['organization_id']
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            prior = db.execute('SELECT * FROM training_attempts WHERE id=?', (str(body.request_id),)).fetchone()
            if prior:
                if prior['organization_id'] != org or prior['user_id'] != user['id'] or prior['module_id'] != module_id or json.loads(prior['answers']) != body.answers:
                    raise HTTPException(409, 'Assessment retry conflict')
                return result(db, prior)
            row = module_row(db, org, module_id)
            if row['status'] != 'published' or row['published_version'] != body.module_version:
                raise HTTPException(409, 'This training changed. Reload the current version before answering.')
            payload = published(db, org, module_id, body.module_version)
            if len(body.answers) != len(payload['questions']):
                raise HTTPException(422, 'Answer every question')
            if db.execute('SELECT 1 FROM training_completions WHERE organization_id=? AND user_id=? AND module_id=? AND module_version=?', (org, user['id'], module_id, body.module_version)).fetchone():
                raise HTTPException(409, 'You already passed this version')
            used = db.execute('SELECT COUNT(*) FROM training_attempts WHERE organization_id=? AND user_id=? AND module_id=? AND module_version=?', (org, user['id'], module_id, body.module_version)).fetchone()[0]
            if used >= payload['max_attempts']:
                raise HTTPException(409, 'No attempts remain for this version. Ask your admin for help.')
            correct = sum(1 for given, q in zip(body.answers, payload['questions']) if given == q['answer'])
            score = round(100 * correct / len(payload['questions']))
            passed = score >= payload['passing_score']
            stamp = now()
            db.execute('INSERT INTO training_attempts VALUES (?,?,?,?,?,?,?,?,?)', (str(body.request_id), org, user['id'], module_id, body.module_version, json.dumps(body.answers), score, int(passed), stamp))
            if passed:
                db.execute('INSERT INTO training_completions VALUES (?,?,?,?,?,?,?,?)', (str(uuid4()), org, user['id'], module_id, body.module_version, str(body.request_id), score, stamp))
                db.execute("UPDATE training_assignments SET status='completed',updated_at=? WHERE organization_id=? AND user_id=? AND module_id=? AND module_version=? AND status='assigned'",
                           (stamp, org, user['id'], module_id, body.module_version))
            return result(db, db.execute('SELECT * FROM training_attempts WHERE id=?', (str(body.request_id),)).fetchone())

    def result(db, row):
        payload = published(db, row['organization_id'], row['module_id'], row['module_version'])
        used = db.execute('SELECT COUNT(*) FROM training_attempts WHERE organization_id=? AND user_id=? AND module_id=? AND module_version=?',
                          (row['organization_id'], row['user_id'], row['module_id'], row['module_version'])).fetchone()[0]
        # Correct answers are not revealed, so the assessment stays usable for retakes.
        return {'id': row['id'], 'score': row['score'], 'passed': bool(row['passed']), 'passing_score': payload['passing_score'],
                'attempts_used': used, 'attempts_allowed': payload['max_attempts'], 'submitted_at': row['submitted_at'],
                'record_type': 'assessment_completion' if row['passed'] else 'assessment_attempt',
                'certificate_issued': False, 'qualification_issued': False}

    @app.get('/api/training-completions')
    def completions(request: Request, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
        user = actor(request)
        clause, params = 'organization_id=?', [user['organization_id']]
        if user['role'] != 'admin':
            clause += ' AND user_id=?'
            params.append(user['id'])
        with connect() as db:
            rows = db.execute('SELECT * FROM training_completions WHERE ' + clause + ' ORDER BY completed_at DESC,id LIMIT ? OFFSET ?', [*params, limit, offset]).fetchall()
            titles = {r['id']: json.loads(r['draft'])['title'] for r in db.execute('SELECT id,draft FROM training_modules WHERE organization_id=?', (user['organization_id'],)).fetchall()}
        return {'items': [{**dict(r), 'title': titles.get(r['module_id'], r['module_id']), 'record_type': 'assessment_completion',
                           'certificate_issued': False, 'qualification_issued': False} for r in rows]}
