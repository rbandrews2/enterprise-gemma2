"""Organization team messages with receipts and optional SMS copies, plus personal study planning."""
import json
from pathlib import Path
from datetime import datetime, timezone
from uuid import UUID
from fastapi import BackgroundTasks, HTTPException, Request, Query
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from . import messaging as sms

class Message(BaseModel):
    model_config=ConfigDict(extra="forbid",str_strip_whitespace=True)
    request_id: UUID
    recipient_id: str
    text: str=Field(min_length=1,max_length=2000)
    request_acknowledgement: bool=False
    sms_copy: bool=False

def sms_text(user,text):
    # Texts carry the work message itself; private records and links are never attached.
    body=text if len(text)<=600 else text[:597]+'...'
    return f"WZOS {user['organization']}: {user['name']} sent you a message: {body} Reply STOP to opt out."

class Study(BaseModel):
    model_config=ConfigDict(extra="forbid")
    status: Literal['not_started','studying','review_requested']

def register(app,connect,actor,actors,synthetic=True):
    catalog=json.loads(Path(__file__).with_name('training_catalog.json').read_text(encoding='utf-8'))
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS study_plans (organization_id TEXT,owner_id TEXT,course_id TEXT,status TEXT,updated_at TEXT,PRIMARY KEY(organization_id,owner_id,course_id))')
        db.execute('CREATE TABLE IF NOT EXISTS fixture_messages (id TEXT PRIMARY KEY,organization_id TEXT,sender_id TEXT,recipient_id TEXT,body TEXT,created_at TEXT)')
    service=sms.register(app,connect,actor,actors,live_permitted=not synthetic)
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
            ids=[r['id'] for r in rows];marks=','.join('?'*len(ids))
            receipts={r['message_id']:r for r in db.execute('SELECT * FROM message_receipts WHERE organization_id=? AND message_id IN ('+marks+')',[user['organization_id'],*ids]).fetchall()} if ids else {}
            texts={r['reference_id']:r for r in db.execute("SELECT * FROM sms_outbox WHERE organization_id=? AND purpose='message' AND reference_id IN ("+marks+')',[user['organization_id'],*ids]).fetchall()} if ids else {}
        def item(row):
            receipt=receipts.get(row['id']);text=texts.get(row['id']) if row['sender_id']==user['id'] else None
            return {**dict(row),'acknowledgement_requested':bool(receipt and receipt['ack_required']),'acknowledged_at':receipt['acknowledged_at'] if receipt else None,
                    'sms':sms.public(text,include_body=False) if text else None}
        return {'items':[item(r) for r in rows],'synthetic_only':synthetic,'external_delivery':service.readiness()['ready']}
    @app.post('/api/messages')
    def send(body:Message,request:Request,background:BackgroundTasks):
        user=actor(request);recipient=actors(user).get(body.recipient_id)
        if not recipient or recipient['organization_id']!=user['organization_id']:raise HTTPException(404,'Test member not found' if synthetic else 'Member not found')
        if body.sms_copy and user['role']!='admin':raise HTTPException(403,'Only admins can send text message copies')
        message_id=str(body.request_id);queued=None
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            prior=db.execute('SELECT * FROM fixture_messages WHERE id=?',(message_id,)).fetchone()
            if prior:
                receipt=db.execute('SELECT ack_required FROM message_receipts WHERE message_id=?',(message_id,)).fetchone()
                text=db.execute("SELECT * FROM sms_outbox WHERE organization_id=? AND purpose='message' AND reference_id=?",(user['organization_id'],message_id)).fetchone()
                same=(prior['organization_id']==user['organization_id'] and prior['sender_id']==user['id'] and prior['recipient_id']==body.recipient_id and prior['body']==body.text
                      and bool(receipt and receipt['ack_required'])==body.request_acknowledgement and bool(text)==body.sms_copy)
                if not same:raise HTTPException(409,'Message retry identifier conflict')
                queued=dict(text) if text else None
            else:
                db.execute('INSERT INTO fixture_messages VALUES (?,?,?,?,?,?)',(message_id,user['organization_id'],user['id'],body.recipient_id,body.text,datetime.now(timezone.utc).isoformat()))
                db.execute('INSERT INTO message_receipts VALUES (?,?,?,?,?)',(user['organization_id'],message_id,body.recipient_id,int(body.request_acknowledgement),None))
                if body.sms_copy:
                    queued=service.enqueue(db,organization_id=user['organization_id'],recipient_id=body.recipient_id,body=sms_text(user,body.text),purpose='message',reference_id=message_id,actor_id=user['id'])
        if queued and queued['status']=='queued':background.add_task(service.process,user['organization_id'],[queued['id']])
        return {'id':message_id,'status':'stored_for_test_recipient' if synthetic else 'stored_for_recipient','external_delivery':bool(queued and queued['status']!='blocked'),
                'acknowledgement_requested':body.request_acknowledgement,'sms':sms.public(queued,include_body=False) if queued else None}
    @app.post('/api/messages/{message_id}/acknowledge')
    def acknowledge(message_id:UUID,request:Request):
        user=actor(request)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT r.* FROM message_receipts r JOIN fixture_messages m ON m.id=r.message_id WHERE r.message_id=? AND r.organization_id=? AND m.organization_id=? AND r.recipient_id=?',(str(message_id),user['organization_id'],user['organization_id'],user['id'])).fetchone()
            if not row:raise HTTPException(404,'Message not found')
            stamp=row['acknowledged_at'] or datetime.now(timezone.utc).isoformat()
            if not row['acknowledged_at']:db.execute('UPDATE message_receipts SET acknowledged_at=? WHERE message_id=? AND recipient_id=?',(stamp,str(message_id),user['id']))
        return {'id':str(message_id),'acknowledged_at':stamp}
