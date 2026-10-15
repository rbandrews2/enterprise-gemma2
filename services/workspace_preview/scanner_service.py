"""Standalone private scanner API; no accounts, storage or database clients.

Requires Cloud Run IAM AND independently verified Google caller identity. No
production configuration or daemon process is started by importing this module.
"""
import asyncio
import hashlib
import os
import re
import threading
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from .clamd_scanner import ClamdScanner
from .scanner_transport import BoundedGoogleRequest, MAX_BYTES, scanner_origin


def verify_identity(token, audience):
    from google.oauth2.id_token import verify_oauth2_token
    return verify_oauth2_token(token, BoundedGoogleRequest(), audience=audience)


def create_app(*, audience=None, caller=None, verifier=verify_identity, scanner=None):
    audience = scanner_origin(audience or os.environ['WZOS_SCANNER_AUDIENCE'])
    caller = caller or os.environ['WZOS_SCANNER_CALLER']
    if not re.fullmatch(r'[a-z0-9-]+@[a-z0-9-]+\.iam\.gserviceaccount\.com', caller):
        raise ValueError('One explicit Google service-account caller required')
    if scanner is None:
        if os.getenv('WZOS_SCANNER_INSTANCE_DEADLINE'):
            from .scanner_runtime import SupervisedScanner
            scanner = SupervisedScanner()
        else:
            scanner = ClamdScanner()
    slots = threading.BoundedSemaphore(1)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, redirect_slashes=False)

    @app.middleware('http')
    async def no_store(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.get('/healthz')
    def health():
        return {'status': 'alive'}  # Not engine readiness or coverage.

    @app.post('/scan')
    async def scan(request: Request):
        authorization = request.headers.get('authorization', '')
        if not re.fullmatch(r'Bearer [A-Za-z0-9_.-]{16,8192}', authorization):
            raise HTTPException(401, 'Service identity required')
        if not slots.acquire(blocking=False):
            raise HTTPException(429, 'Scanner busy')
        try:
            try:
                claims = await run_in_threadpool(verifier, authorization[7:], audience)
                if (claims.get('email') != caller or claims.get('email_verified') is not True
                        or not claims.get('sub') or claims.get('aud') != audience
                        or claims.get('iss') not in ('accounts.google.com', 'https://accounts.google.com')):
                    raise ValueError('Caller mismatch')
            except Exception:
                raise HTTPException(403, 'Service identity rejected') from None
            try:
                request_id = str(UUID(request.headers.get('x-scan-request', '')))
                digest = request.headers.get('x-content-sha256', '')
                length = request.headers.get('content-length', '')
                if (not re.fullmatch(r'[0-9a-f]{64}', digest) or not re.fullmatch(r'[0-9]{1,8}', length)
                        or not 0 < int(length) <= MAX_BYTES
                        or request.headers.get('content-type') != 'application/octet-stream'
                        or request.headers.get('content-encoding')):
                    raise ValueError('Invalid scan request')
            except ValueError:
                raise HTTPException(400, 'Invalid scan request') from None
            data = bytearray()
            try:
                async with asyncio.timeout(5):
                    async for chunk in request.stream():
                        if len(data) + len(chunk) > int(length):
                            raise HTTPException(413, 'Scan size exceeded')
                        data.extend(chunk)
            except TimeoutError:
                raise HTTPException(408, 'Scan upload timed out') from None
            if len(data) != int(length) or hashlib.sha256(data).hexdigest() != digest:
                raise HTTPException(400, 'Scan integrity mismatch')
            try:
                result = await run_in_threadpool(scanner.scan, bytes(data))
                if (result.status not in ('clean', 'infected', 'error')
                        or (result.status != 'error' and not re.fullmatch(r'ClamAV [0-9][0-9A-Za-z.+~-]{0,63}/[0-9]{1,20}', result.engine))):
                    raise ValueError('Invalid engine result')
            except Exception:
                raise HTTPException(503, 'Scan unavailable') from None
            return {'version': 1, 'request_id': request_id, 'sha256': digest,
                    'byte_count': len(data), 'status': result.status,
                    'engine': result.engine if result.status != 'error' else ''}
        finally:
            slots.release()

    return app
