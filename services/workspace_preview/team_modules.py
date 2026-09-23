"""Synthetic team message workflow and personal study planning, not live delivery."""
import json
from pathlib import Path
from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException, Request, Query
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class Message(BaseModel):
    model_config=ConfigDict(extra="forbid",str_strip_whitespace=True)
    request_id: UUID
    recipient_id: str
    text: str=Field(min_length=1,max_length=2000)

class Study(BaseModel):
    model_config=ConfigDict(extra="forbid")
    status: Literal['not_started','studying','review_requested']

def register(app,connect,actor,actors,synthetic=True):
    catalog=json.loads(Path(__file__).with_name('training_catalog.json').read_text(encoding='utf-8'))
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS study_plans (organization_id TEXT,owner_id TEXT,course_id TEXT,status TEXT,updated_at TEXT,PRIMARY KEY(organization_id,owner_id,course_id))')
        db.execute('CREATE TABLE IF NOT EXISTS fixture_messages (id TEXT PRIMARY KEY,organization_id TEXT,sender_id TEXT,recipient_id TEXT,body TEXT,created_at TEXT)')
    @app.get('/api/training')
    def training(request:Request):
        user=actor(request)
        with connect() as db:
            rows=db.execute('SELECT * FROM study_plans WHERE organization_id=? AND owner_id=?',(user['organization_id'],user['id'])).fetchall()
        statuses={r['course_id']:r['status'] for r in rows}
        return {'items':[{**c,'study_status':statuses.get(c['id'],'not_started')} for c in catalog], 'certification_enabled':False}
    @app.put('/api/training/{course_id}')
    def study(course_id:str,body:Study,request:Request):
        user=actor(request)
        if course_id not in {c['id'] for c in catalog}:raise HTTPException(404,'Course not found')
        with connect() as db:db.execute('INSERT INTO study_plans VALUES (?,?,?,?,?) ON CONFLICT(organization_id,owner_id,course_id) DO UPDATE SET status=excluded.status,updated_at=excluded.updated_at',(user['organization_id'],user['id'],course_id,body.status,datetime.now(timezone.utc).isoformat()))
        return {'status':body.status,'certificate_issued':False,'review_notification_sent':False}
    @app.get('/api/messages')
    def messages(request:Request,offset:int=Query(0,ge=0)):
        user=actor(request)
        with connect() as db:
            rows=db.execute('SELECT * FROM fixture_messages WHERE organization_id=? AND (sender_id=? OR recipient_id=?) ORDER BY created_at DESC,id LIMIT 50 OFFSET ?',(user['organization_id'],user['id'],user['id'],offset)).fetchall()
        return {'items':[dict(r) for r in rows],'synthetic_only':synthetic,'external_delivery':False}
    @app.post('/api/messages')
    def send(body:Message,request:Request):
        user=actor(request);recipient=actors(user).get(body.recipient_id)
        if not recipient or recipient['organization_id']!=user['organization_id']:raise HTTPException(404,'Test member not found')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            prior=db.execute('SELECT * FROM fixture_messages WHERE id=?',(str(body.request_id),)).fetchone()
            if prior:
                if prior['organization_id']!=user['organization_id'] or prior['sender_id']!=user['id'] or prior['recipient_id']!=body.recipient_id or prior['body']!=body.text:raise HTTPException(409,'Message retry identifier conflict')
            else:db.execute('INSERT INTO fixture_messages VALUES (?,?,?,?,?,?)',(str(body.request_id),user['organization_id'],user['id'],body.recipient_id,body.text,datetime.now(timezone.utc).isoformat()))
        return {'id':str(body.request_id),'status':'stored_for_test_recipient' if synthetic else 'stored_for_recipient','external_delivery':False}
