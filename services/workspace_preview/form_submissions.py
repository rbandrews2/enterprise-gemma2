"""Immutable organization-scoped office submissions and review."""
import hashlib
import json
import os
import math
from datetime import date, time
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID
from fastapi import BackgroundTasks, HTTPException, Request, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Submission(BaseModel):
    model_config=ConfigDict(extra='forbid')
    request_id: UUID
    form_id: UUID
    expected_form_version: int=Field(ge=1,strict=True)

class CompletedForm(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    request_id: UUID
    template_id: str = Field(min_length=1, max_length=100)
    template_revision: int = Field(ge=1, strict=True)
    fields: dict = Field(max_length=100)
    order: str = Field(default='', max_length=200)
    location: str = Field(default='', max_length=500)


def printable_snapshot(body, templates):
    template = templates.get((body.template_id, body.template_revision))
    if not template:
        raise HTTPException(404, 'Form template revision not found')
    if len(json.dumps(body.fields)) > 64000:
        raise HTTPException(422, 'Form entries are too large')
    definitions = {f['key']: f for section in template['sections'] for f in section['fields']}
    if set(body.fields) - definitions.keys():
        raise HTTPException(422, 'Unknown form field')
    cleaned = {}
    def text(value, maximum=4000):
        if not isinstance(value, str) or len(value) > maximum:
            raise HTTPException(422, 'Invalid form entry or text too long')
        return value.strip()
    for key, value in body.fields.items():
        field = definitions[key]; kind = field['type']
        if kind == 'rows':
            columns = {c['key']: c for c in field['columns']}
            if not isinstance(value, list) or len(value) > field['max_rows']:
                raise HTTPException(422, 'Too many form rows')
            rows = []
            for row in value:
                if not isinstance(row, dict) or set(row) - columns.keys():
                    raise HTTPException(422, 'Invalid form row')
                rows.append({k: text(v, columns[k].get('max_length', 200)) for k, v in row.items()})
            cleaned[key] = rows
        elif kind == 'multiselect':
            if not isinstance(value, list) or any(not isinstance(v,str) for v in value) or len(value) != len(set(value)) or not set(value) <= set(field['options']):
                raise HTTPException(422, 'Invalid form choices')
            cleaned[key] = value
        else:
            value = text(value, field.get('max_length', 4000 if kind=='textarea' else 200))
            if kind == 'select' and value and value not in field['options']:
                raise HTTPException(422, 'Invalid form choice')
            if value and kind in ('date', 'time', 'number'):
                try:
                    if kind == 'date': date.fromisoformat(value)
                    elif kind == 'time': time.fromisoformat(value)
                    else:
                        number = float(value)
                        if not math.isfinite(number) or number < field.get('min',-math.inf) or number > field.get('max',math.inf): raise ValueError()
                except ValueError:
                    raise HTTPException(422, 'Invalid form date, time or number')
            cleaned[key] = value
    if not any(v for v in cleaned.values()):
        raise HTTPException(422, 'Complete at least one form field before sending to office')
    return {'title': template['title'], 'form_type':'printable', 'status':'completed',
            'template_id':body.template_id, 'template_revision':body.template_revision,
            'template':template, 'fields':cleaned, 'order':body.order, 'location':body.location}


class Review(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    expected_version: int=Field(ge=1,strict=True)
    status: Literal['reviewed','changes_requested']
    note: str=Field(default='',max_length=2000)
    @model_validator(mode='after')
    def required_note(self):
        if self.status=='changes_requested' and not self.note:raise ValueError('Explain the requested changes')
        return self

def register(app,connect,actor):
    from .forms_hub import load_catalog
    templates, _ = load_catalog()
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS form_submissions (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,form_id TEXT NOT NULL,form_version INTEGER NOT NULL,submitted_by TEXT NOT NULL,payload TEXT NOT NULL,payload_hash TEXT NOT NULL,status TEXT NOT NULL,version INTEGER NOT NULL,submitted_at TEXT NOT NULL,reviewed_by TEXT,reviewed_at TEXT,note TEXT NOT NULL,UNIQUE(organization_id,form_id,form_version))')
    def unpack(row):
        item=dict(row);item['form']=json.loads(item.pop('payload'));item['external_delivery']=False;return item
    @app.post('/api/form-submissions')
    def submit(body:Submission,request:Request):
        user=actor(request);org=user['organization_id'];sid=str(body.request_id);fid=str(body.form_id)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            prior=db.execute('SELECT * FROM form_submissions WHERE id=?',(sid,)).fetchone()
            if prior:
                if (prior['organization_id'],prior['submitted_by'],prior['form_id'],prior['form_version'])!=(org,user['id'],fid,body.expected_form_version):raise HTTPException(409,'Submission retry conflict')
                return unpack(prior)
            row=db.execute("SELECT * FROM module_records WHERE organization_id=? AND kind='forms' AND id=?",(org,fid)).fetchone()
            if not row or (user['role']!='admin' and row['owner_id']!=user['id']):raise HTTPException(404,'Saved form not found')
            if row['version']!=body.expected_form_version:raise HTTPException(409,'Form changed. Reload the saved version before submitting')
            if db.execute('SELECT id FROM form_submissions WHERE organization_id=? AND form_id=? AND form_version=?',(org,fid,row['version'])).fetchone():raise HTTPException(409,'This saved form version has already been submitted')
            if json.loads(row['payload']).get('status')=='cancelled':raise HTTPException(409,'Cancelled forms cannot be submitted')
            db.execute('INSERT INTO form_submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',(sid,org,fid,row['version'],user['id'],row['payload'],hashlib.sha256(row['payload'].encode()).hexdigest(),'received',1,datetime.now(timezone.utc).isoformat(),None,None,''))
            return unpack(db.execute('SELECT * FROM form_submissions WHERE id=?',(sid,)).fetchone())
    @app.post('/api/form-submissions/completed')
    def send_completed(body:CompletedForm,request:Request,background:BackgroundTasks):
        user=actor(request);sid=str(body.request_id);org=user['organization_id']
        if body.template_id=='daily-work-report' and (user['edition']!='enterprise' or os.getenv('WZOS_FIELD_VOICE_ENABLED')!='1'):
            raise HTTPException(403, 'Daily Work Report requires enabled Enterprise access')
        payload=json.dumps(printable_snapshot(body,templates),sort_keys=True,separators=(',',':'))
        digest=hashlib.sha256(payload.encode()).hexdigest();queued=[]
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            prior=db.execute('SELECT * FROM form_submissions WHERE id=?',(sid,)).fetchone()
            if prior:
                if (prior['organization_id'],prior['submitted_by'],prior['payload_hash']) != (org,user['id'],digest):
                    raise HTTPException(409,'Office submission retry conflict')
                return unpack(prior)
            db.execute('INSERT INTO form_submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (sid,org,sid,1,user['id'],payload,digest,'received',1,datetime.now(timezone.utc).isoformat(),None,None,''))
            notify=getattr(app.state,'notify_office',None)
            if notify: queued=notify(db,user,sid)
            saved=unpack(db.execute('SELECT * FROM form_submissions WHERE id=?',(sid,)).fetchone())
        service=getattr(app.state,'messaging',None)
        if queued and service: background.add_task(service.process,org,queued)
        return saved
    @app.get('/api/form-submissions')
    def listing(request:Request,offset:int=Query(0,ge=0),limit:int=Query(25,ge=1,le=50)):
        user=actor(request);clause='organization_id=?';params=[user['organization_id']]
        if user['role']!='admin':clause+=' AND submitted_by=?';params.append(user['id'])
        with connect() as db:
            total=db.execute('SELECT COUNT(*) FROM form_submissions WHERE '+clause,params).fetchone()[0]
            rows=db.execute('SELECT * FROM form_submissions WHERE '+clause+' ORDER BY submitted_at DESC,id LIMIT ? OFFSET ?',[*params,limit,offset]).fetchall()
        return {'items':[unpack(r) for r in rows],'total':total,'offset':offset,'can_review':user['role']=='admin'}
    @app.post('/api/form-submissions/{submission_id}/review')
    def review(submission_id:UUID,body:Review,request:Request):
        user=actor(request)
        if user['role']!='admin':raise HTTPException(403,'Administrator review required')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM form_submissions WHERE id=? AND organization_id=?',(str(submission_id),user['organization_id'])).fetchone()
            if not row:raise HTTPException(404,'Submission not found')
            if row['version']==body.expected_version+1 and row['reviewed_by']==user['id'] and row['status']==body.status and row['note']==body.note:return unpack(row)
            if row['version']!=body.expected_version or row['status']!='received':raise HTTPException(409,'Submission already reviewed. Reload its status')
            db.execute('UPDATE form_submissions SET status=?,version=version+1,reviewed_by=?,reviewed_at=?,note=? WHERE id=?',(body.status,user['id'],datetime.now(timezone.utc).isoformat(),body.note,str(submission_id)))
            return unpack(db.execute('SELECT * FROM form_submissions WHERE id=?',(str(submission_id),)).fetchone())
