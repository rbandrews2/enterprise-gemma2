"""Signature-gated callback relay; no user UI, database, or message-send endpoint.

Deploy separately from the private workspace. Pin both origins in configuration;
never derive signature URLs or upstream targets from client forwarding headers.
"""
import os
from urllib.parse import parse_qsl, urlsplit

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

from services.workspace_preview.sms_provider import valid_signature

CALLBACK_PATHS = ('/api/messaging/twilio/status', '/api/messaging/twilio/inbound')
MAX_BYTES = 16384


def origin(value, *, private=False):
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username
            or parsed.password or parsed.port or parsed.path not in ('', '/')
            or parsed.query or parsed.fragment
            or (private and not parsed.hostname.endswith('.run.app'))):
        raise ValueError('Expected a pinned HTTPS origin')
    return value.rstrip('/')


def identity_token(audience):
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2.id_token import fetch_id_token
    return fetch_id_token(GoogleRequest(), audience)


def create_app(*, public_origin=None, upstream=None, auth_token=None,
               account_sid=None, token_provider=identity_token, transport=None):
    public_origin = origin(public_origin or os.environ['WZOS_PUBLIC_BASE_URL'])
    upstream = origin(upstream or os.environ['WZOS_TWILIO_PRIVATE_UPSTREAM'], private=True)
    auth_token = (auth_token or os.environ['WZOS_TWILIO_AUTH_TOKEN']).strip()
    account_sid = (account_sid or os.environ['WZOS_TWILIO_ACCOUNT_SID']).strip()
    if not auth_token or not account_sid:
        raise ValueError('Twilio callback credentials required')
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, redirect_slashes=False)

    @app.middleware('http')
    async def headers(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.get('/healthz')
    def health():
        return {'status': 'ok'}

    def forward(path, query, raw, supplied):
        try:
            token = token_provider(upstream)
            if not token:
                return Response(status_code=503)
            with httpx.Client(timeout=httpx.Timeout(10, connect=5),
                              transport=transport, follow_redirects=False,
                              trust_env=False) as client:
                result = client.post(upstream + path + query, content=raw, headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Twilio-Signature': supplied,
                    'X-Serverless-Authorization': 'Bearer ' + token,
                })
        except Exception:
            # SDK/provider failures can include credentials or request content.
            # Do not echo exception text or retry a mutation inside the relay.
            return Response(status_code=503)
        if result.status_code == 204:
            return Response(status_code=204)
        if result.status_code == 200:
            # Only the existing inbound handler returns XML; never relay arbitrary
            # response bodies, cookies or redirect destinations from the backend.
            return Response('<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
                            media_type='application/xml')
        return Response(status_code=502)

    async def callback(request: Request):
        if request.headers.get('content-type', '').split(';')[0].strip().lower() != 'application/x-www-form-urlencoded':
            raise HTTPException(415, 'Form callback required')
        supplied = request.headers.get('X-Twilio-Signature', '')
        if not supplied:
            raise HTTPException(403, 'Invalid signature')
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > MAX_BYTES:
                raise HTTPException(413, 'Callback too large')
            raw.extend(chunk)
        try:
            params = parse_qsl(raw.decode('utf-8'), keep_blank_values=True,
                               max_num_fields=256)
            query = request.scope.get('query_string', b'').decode('ascii')
        except (UnicodeError, ValueError):
            raise HTTPException(400, 'Invalid callback') from None
        query = '?' + query if query else ''
        if not valid_signature(auth_token, public_origin + request.url.path + query, params, supplied):
            raise HTTPException(403, 'Invalid signature')
        # Prevent ambiguous/mismatched account claims before acquiring an IAM token.
        accounts = [value for name, value in params if name == 'AccountSid']
        if accounts != [account_sid]:
            raise HTTPException(403, 'Invalid account')
        return await run_in_threadpool(forward, request.url.path, query, bytes(raw), supplied)

    for path in CALLBACK_PATHS:
        app.add_api_route(path, callback, methods=['POST'])
    return app


def application():
    return create_app()
