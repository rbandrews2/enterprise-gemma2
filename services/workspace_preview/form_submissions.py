"""Immutable internal submissions of saved forms; no external delivery."""
import hashlib
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID
from fastapi import HTTPException, Request, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Submission(BaseModel):
    model_config=ConfigDict(extra='forbid')
    request_id: UUID
    form_id: UUID
    expected_form_version: int=Field(ge=1,strict=True)

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
