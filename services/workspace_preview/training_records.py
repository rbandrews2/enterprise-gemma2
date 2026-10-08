"""Self-reported study acknowledgements, never automatic qualifications."""
import hashlib,json
from datetime import date,datetime,timezone
from pathlib import Path
from uuid import UUID
from fastapi import HTTPException,Request,Query
from pydantic import BaseModel,ConfigDict,Field,model_validator
from .form_submissions import Review

class Acknowledgement(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    request_id: UUID
    course_id: str=Field(min_length=1,max_length=100)
    catalog_hash: str=Field(pattern=r'^[a-f0-9]{64}$')
    completed_on: date
    minutes: int=Field(ge=1,le=1440,strict=True)
    material_reference: str=Field(min_length=3,max_length=1000)
    notes: str=Field(default='',max_length=2000)
    acknowledged: bool=Field(strict=True)
    @model_validator(mode='after')
    def confirmation(self):
        if not self.acknowledged:raise ValueError('Confirm that this is your own completed study')
        if self.completed_on>datetime.now(timezone.utc).date():raise ValueError('Completion date cannot be in the future')
        return self

def register(app,connect,actor):
    catalog=json.loads(Path(__file__).with_name('training_catalog.json').read_text(encoding='utf-8'))
    def packed(course):
        digest=hashlib.sha256(json.dumps(course,sort_keys=True).encode()).hexdigest()
        return {**course,'catalog_hash':digest}
    courses={row['id']:packed(row) for row in catalog}
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS training_records (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,user_id TEXT NOT NULL,course_id TEXT NOT NULL,payload TEXT NOT NULL,status TEXT NOT NULL,version INTEGER NOT NULL,submitted_at TEXT NOT NULL,reviewed_by TEXT,reviewed_at TEXT,note TEXT NOT NULL)')
    def unpack(row):
        item=dict(row);item['record']=json.loads(item.pop('payload'));item['qualification_issued']=False;return item
    @app.get('/api/training-records/catalog')
    def course_list(request:Request):
        actor(request);return {'items':list(courses.values()),'qualification_issued':False}
    @app.post('/api/training-records')
    def submit(body:Acknowledgement,request:Request):
        user=actor(request);submitted=body.model_dump(mode='json',exclude={'request_id'})
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            prior=db.execute('SELECT * FROM training_records WHERE id=?',(str(body.request_id),)).fetchone()
            if prior:
                if prior['organization_id']!=user['organization_id'] or prior['user_id']!=user['id'] or json.loads(prior['payload'])['acknowledgement']!=submitted:raise HTTPException(409,'Training retry conflict')
                return unpack(prior)
            course=courses.get(body.course_id)
            if not course:raise HTTPException(404,'Course not found')
            if course['catalog_hash']!=body.catalog_hash:raise HTTPException(409,'Course information changed. Reload before recording study')
            payload=json.dumps({'acknowledgement':submitted,'course':course},sort_keys=True)
            db.execute('INSERT INTO training_records VALUES (?,?,?,?,?,?,?,?,?,?,?)',(str(body.request_id),user['organization_id'],user['id'],body.course_id,payload,'received',1,datetime.now(timezone.utc).isoformat(),None,None,''))
            return unpack(db.execute('SELECT * FROM training_records WHERE id=?',(str(body.request_id),)).fetchone())
    @app.get('/api/training-records')
    def listing(request:Request,offset:int=Query(0,ge=0),limit:int=Query(25,ge=1,le=50)):
        user=actor(request);clause='organization_id=?';params=[user['organization_id']]
        if user['role']!='admin':clause+=' AND user_id=?';params.append(user['id'])
        with connect() as db:
            total=db.execute('SELECT COUNT(*) FROM training_records WHERE '+clause,params).fetchone()[0]
            rows=db.execute('SELECT * FROM training_records WHERE '+clause+' ORDER BY submitted_at DESC,id LIMIT ? OFFSET ?',[*params,limit,offset]).fetchall()
        return {'items':[unpack(row) for row in rows],'total':total,'can_review':user['role']=='admin'}
    @app.post('/api/training-records/{record_id}/review')
    def review(record_id:UUID,body:Review,request:Request):
        user=actor(request)
        if user['role']!='admin':raise HTTPException(403,'Administrator review required')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM training_records WHERE id=? AND organization_id=?',(str(record_id),user['organization_id'])).fetchone()
            if not row:raise HTTPException(404,'Training record not found')
            if row['version']==body.expected_version+1 and row['reviewed_by']==user['id'] and row['status']==body.status and row['note']==body.note:return unpack(row)
            if row['status']!='received' or row['version']!=body.expected_version:raise HTTPException(409,'Training record already reviewed. Reload its status')
            db.execute('UPDATE training_records SET status=?,version=version+1,reviewed_by=?,reviewed_at=?,note=? WHERE id=?',(body.status,user['id'],datetime.now(timezone.utc).isoformat(),body.note,str(record_id)))
            return unpack(db.execute('SELECT * FROM training_records WHERE id=?',(str(record_id),)).fetchone())
