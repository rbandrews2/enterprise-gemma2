"""Immutable, actor-scoped draft report snapshots, not approvals or delivery records."""
import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException, Request, Query
from pydantic import BaseModel, ConfigDict, Field
from services.workspace_preview.atlas_adapter import prepare_order

class SaveReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    expected_order_version: int = Field(ge=1, strict=True)

def register(app, connect, actor, report, knowledge):
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS report_snapshots (
            id TEXT PRIMARY KEY, order_id TEXT NOT NULL, organization_id TEXT NOT NULL,
            owner_id TEXT NOT NULL, order_version INTEGER NOT NULL, saved_at TEXT NOT NULL,
            payload TEXT NOT NULL, sha256 TEXT NOT NULL)""")

    def scope(order_id, request):
        selected = actor(request)
        current = report(order_id, request)  # Enforce edition and current job access.
        return selected, current

    def summary(row, current):
        saved = json.loads(row['payload'])
        changed = (saved['order'] != current['order'] or saved['checklist'] != current['checklist']
                   or saved['forms'] != current['forms'] or saved['forms_total'] != current['forms_total'])
        return {"id": row['id'], "order_version": row['order_version'], "saved_at": row['saved_at'],
                "sha256": row['sha256'], "basis_changed": changed, "approved_for_field_use": False}

    @app.post('/api/orders/{order_id}/reports')
    def save(order_id: str, body: SaveReport, request: Request):
        selected, current = scope(order_id, request)
        with connect() as db:
            prior = db.execute('SELECT * FROM report_snapshots WHERE id=?', (str(body.request_id),)).fetchone()
        if prior:
            if (prior['owner_id'] != selected['id'] or prior['organization_id'] != selected['organization_id']
                    or prior['order_id'] != order_id or prior['order_version'] != body.expected_order_version):
                raise HTTPException(409, 'Save identifier already used; refresh and try again')
            return summary(prior, current)
        if current['order']['version'] != body.expected_order_version:
            raise HTTPException(409, 'Work order changed. Refresh the report first')
        current['preparation'] = prepare_order(current['order'], knowledge)
        current['limitations'][0] = 'Saved draft snapshot, not an approved or complete report. Later changes require a new snapshot.'
        packed = json.dumps(current, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(packed.encode()).hexdigest()
        saved_at = datetime.now(timezone.utc).isoformat()
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            # The snapshot deliberately preserves the basis read above, even if newer input now exists.
            db.execute('INSERT INTO report_snapshots VALUES (?,?,?,?,?,?,?,?) ON CONFLICT DO NOTHING',
                       (str(body.request_id),order_id,selected['organization_id'],selected['id'],
                        body.expected_order_version,saved_at,packed,digest))
            row=db.execute('SELECT * FROM report_snapshots WHERE id=?',(str(body.request_id),)).fetchone()
            if row['owner_id'] != selected['id'] or row['organization_id'] != selected['organization_id'] or row['order_id'] != order_id or row['order_version'] != body.expected_order_version:
                raise HTTPException(409,'Save identifier conflict')
        return summary(row, report(order_id, request))

    @app.get('/api/orders/{order_id}/reports')
    def listing(order_id: str, request: Request, offset: int=Query(0,ge=0), limit: int=Query(20,ge=1,le=50)):
        selected,current=scope(order_id,request)
        params=(order_id,selected['organization_id'],selected['id'])
        where='order_id=? AND organization_id=? AND owner_id=?'
        with connect() as db:
            total=db.execute('SELECT COUNT(*) FROM report_snapshots WHERE '+where,params).fetchone()[0]
            rows=db.execute('SELECT * FROM report_snapshots WHERE '+where+' ORDER BY saved_at DESC,id LIMIT ? OFFSET ?',(*params,limit,offset)).fetchall()
        return {"items":[summary(row,current) for row in rows],"total":total}

    @app.get('/api/orders/{order_id}/reports/{snapshot_id}')
    def detail(order_id: str, snapshot_id: UUID, request: Request):
        selected,current=scope(order_id,request)
        with connect() as db:
            row=db.execute('SELECT * FROM report_snapshots WHERE id=? AND order_id=? AND organization_id=? AND owner_id=?',
                           (str(snapshot_id),order_id,selected['organization_id'],selected['id'])).fetchone()
        if not row: raise HTTPException(404,'Saved report not found')
        return {**summary(row,current),"report":json.loads(row['payload'])}
