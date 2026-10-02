"""Short-lived, shared cancellation signals; no prompts, replies or credentials."""
import asyncio
import time

from fastapi import HTTPException

from .intelligence import ClientDisconnected, RequestCancelled, reply_until_disconnected


class AtlasRequests:
    deadline = 300
    def __init__(self, connect):
        self.connect = connect
        with connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS atlas_requests (
                id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, actor_id TEXT NOT NULL,
                state TEXT NOT NULL, expires_at BIGINT NOT NULL)''')
            db.execute('CREATE INDEX IF NOT EXISTS atlas_requests_expiry ON atlas_requests(expires_at)')

    def change(self, request_id, actor, action):
        now = int(time.time())
        with self.connect() as db:
            if action == 'read':
                row = db.execute('SELECT * FROM atlas_requests WHERE id=? AND expires_at>=?', (request_id, now)).fetchone()
                if not row or row['actor_id'] != actor['id'] or row['organization_id'] != actor['organization_id']:
                    raise HTTPException(404, 'Atlas request not found')
                return row['state']
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM atlas_requests WHERE expires_at<?', (now,))
            row = db.execute('SELECT * FROM atlas_requests WHERE id=?', (request_id,)).fetchone()
            if row and (row['actor_id'] != actor['id'] or row['organization_id'] != actor['organization_id']):
                raise HTTPException(404, 'Atlas request not found')
            if not row:
                if action not in ('start', 'cancel'):
                    raise HTTPException(404, 'Atlas request expired')
                count = db.execute('SELECT COUNT(*) FROM atlas_requests WHERE actor_id=? AND organization_id=?',
                                   (actor['id'], actor['organization_id'])).fetchone()[0]
                if count >= 64:
                    raise HTTPException(429, 'Too many recent Atlas requests; please wait')
                state = 'running' if action == 'start' else 'cancel_requested'
                db.execute('INSERT INTO atlas_requests VALUES(?,?,?,?,?)',
                           (request_id, actor['organization_id'], actor['id'], state, now + 600))
                return state
            state = row['state']
            if action == 'start':
                if state != 'cancel_requested':
                    raise HTTPException(409, 'Atlas request ID already used')
                # Cancellation can arrive before the original HTTP request.
                state = 'cancelled'
            elif action == 'cancel' and state == 'running':
                state = 'cancel_requested'
            elif action in ('completed', 'failed', 'cancelled') and state in ('running', 'cancel_requested'):
                state = 'cancelled' if state == 'cancel_requested' else action
            db.execute('UPDATE atlas_requests SET state=? WHERE id=?', (state, request_id))
            return state

    async def run(self, request, engine, payload, context, actor):
        async def change(action):
            return await asyncio.to_thread(self.change, str(payload.request_id), actor, action)

        state = await change('start')
        if state != 'running':
            raise RequestCancelled()

        async def cancelled():
            return await change('read') in ('cancel_requested', 'cancelled')

        terminal = 'failed'
        finalized = False
        try:
            # Hard outer bound also applies to providers that ignore their own deadline.
            async with asyncio.timeout(self.deadline):
                answer = await reply_until_disconnected(request, engine, payload, context, cancelled)
            state = await change('completed')
            finalized = True
            terminal = state
            if state == 'cancelled':
                raise RequestCancelled()
            return answer
        except ClientDisconnected:
            terminal = 'cancelled'
            raise
        finally:
            if not finalized:
                await change(terminal)
