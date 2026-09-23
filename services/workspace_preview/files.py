"""Private, bounded file persistence shared by all workspace modules."""
import hashlib
import re
from pathlib import Path
from typing import Literal
from uuid import UUID
from fastapi import HTTPException, Query, Request
from fastapi.responses import Response

MAX_BYTES = 10 * 1024 * 1024
TYPES = {'application/pdf': b'%PDF-', 'image/png': b'\x89PNG\r\n\x1a\n', 'image/jpeg': b'\xff\xd8\xff'}


class LocalFiles:
    cloud = False
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, key):
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root.resolve()):
            raise ValueError('Invalid object key')
        return path

    def put(self, key, data, content_type):
        path = self.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open('xb') as file:
                file.write(data)
        except FileExistsError:
            if path.read_bytes() != data:
                raise ValueError('Object already exists with different content')

    def get(self, key):
        path=self.path(key)
        if path.stat().st_size > MAX_BYTES:
            raise ValueError('Stored file exceeds limit')
        return path.read_bytes()


class GoogleFiles:
    cloud = True
    def __init__(self, bucket, client=None):
        if client is None:
            from google.cloud import storage
            client = storage.Client()
        self.bucket = client.bucket(bucket)
        self.bucket.reload(timeout=20)
        iam = self.bucket.iam_configuration
        if not iam.uniform_bucket_level_access_enabled or iam.public_access_prevention != 'enforced':
            raise ValueError('Private file bucket must enforce uniform access and public access prevention')

    def put(self, key, data, content_type):
        from google.api_core.exceptions import PreconditionFailed
        blob=self.bucket.blob(key)
        blob.metadata={'sha256':hashlib.sha256(data).hexdigest()}
        try:
            blob.upload_from_string(data, content_type=content_type, if_generation_match=0, timeout=30)
        except PreconditionFailed:
            blob.reload(timeout=20)
            if blob.size != len(data) or (blob.metadata or {}).get('sha256') != hashlib.sha256(data).hexdigest():
                raise ValueError('Object conflict') from None

    def get(self, key):
        blob=self.bucket.blob(key)
        blob.reload(timeout=20)
        if blob.size > MAX_BYTES:
            raise ValueError('Stored file exceeds limit')
        return blob.download_as_bytes(if_generation_match=blob.generation, timeout=30)


def register(app, connect, actor, permitted_order, store):
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS workspace_files (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,owner_id TEXT NOT NULL,entity_kind TEXT NOT NULL,entity_id TEXT NOT NULL,filename TEXT NOT NULL,content_type TEXT NOT NULL,size_bytes INTEGER NOT NULL,sha256 TEXT NOT NULL,object_key TEXT NOT NULL)')

    def parent(db, user, kind, record_id):
        if kind == 'order':
            permitted_order(db,record_id,user)
        elif kind == 'form':
            row=db.execute("SELECT owner_id FROM module_records WHERE organization_id=? AND kind='forms' AND id=?",(user['organization_id'],record_id)).fetchone()
            if not row or (user['role']!='admin' and row['owner_id']!=user['id']):
                raise HTTPException(404,'Form not found')

    def metadata(row):
        return {k:row[k] for k in ('id','entity_kind','entity_id','filename','content_type','size_bytes','sha256')}

    @app.put('/api/files/{file_id}')
    async def upload(file_id: UUID, request: Request, entity_kind: Literal['order','form'], entity_id: str=Query(min_length=1,max_length=128), filename: str=Query(min_length=1,max_length=200)):
        user=actor(request)
        if not re.fullmatch(r'[\w .()-]+',filename) or filename.startswith('.'):
            raise HTTPException(422,'Use a simple filename without path separators')
        content_type=request.headers.get('content-type','').split(';')[0]
        if content_type not in TYPES: raise HTTPException(415,'Only PDF, PNG and JPEG files are supported')
        with connect() as db: parent(db,user,entity_kind,entity_id)
        data=bytearray()
        async for chunk in request.stream():
            if len(data)+len(chunk)>MAX_BYTES: raise HTTPException(413,'File exceeds 10 MiB')
            data.extend(chunk)
        data=bytes(data)
        if not data.startswith(TYPES[content_type]): raise HTTPException(415,'File signature does not match its type')
        sha=hashlib.sha256(data).hexdigest()
        # Hash organization ID to prevent path injection through any identity source.
        key=hashlib.sha256(user['organization_id'].encode()).hexdigest()+'/'+str(file_id)
        values=(str(file_id),user['organization_id'],user['id'],entity_kind,entity_id,filename,content_type,len(data),sha,key)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            parent(db,user,entity_kind,entity_id)
            prior=db.execute('SELECT * FROM workspace_files WHERE id=?',(str(file_id),)).fetchone()
            if prior:
                if tuple(prior[k] for k in ('id','organization_id','owner_id','entity_kind','entity_id','filename','content_type','size_bytes','sha256','object_key'))!=values:
                    raise HTTPException(409,'File identifier already used')
                return metadata(prior)
            try: store.put(key,data,content_type)
            except Exception: raise HTTPException(503,'File storage unavailable; retry with the same file identifier') from None
            db.execute('INSERT INTO workspace_files VALUES (?,?,?,?,?,?,?,?,?,?)',values)
            return metadata(db.execute('SELECT * FROM workspace_files WHERE id=?',(str(file_id),)).fetchone())

    @app.get('/api/files')
    def listing(request: Request, entity_kind: Literal['order','form'], entity_id: str, offset: int=Query(0,ge=0)):
        user=actor(request)
        with connect() as db:
            parent(db,user,entity_kind,entity_id)
            rows=db.execute('SELECT * FROM workspace_files WHERE organization_id=? AND entity_kind=? AND entity_id=? ORDER BY id LIMIT 50 OFFSET ?',(user['organization_id'],entity_kind,entity_id,offset)).fetchall()
        return {'items':[metadata(r) for r in rows]}

    @app.get('/api/files/{file_id}')
    def download(file_id: UUID, request: Request):
        user=actor(request)
        with connect() as db:
            row=db.execute('SELECT * FROM workspace_files WHERE id=? AND organization_id=?',(str(file_id),user['organization_id'])).fetchone()
            if not row: raise HTTPException(404,'File not found')
            parent(db,user,row['entity_kind'],row['entity_id'])
        try:
            data=store.get(row['object_key'])
            if hashlib.sha256(data).hexdigest()!=row['sha256']: raise ValueError('Integrity mismatch')
        except Exception: raise HTTPException(503,'File unavailable or integrity check failed') from None
        # Files are downloads, never inline executable content. Scanning remains a launch gate.
        return Response(data,media_type=row['content_type'],headers={'Content-Disposition':'attachment; filename="download"','X-Content-Type-Options':'nosniff'})
