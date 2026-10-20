"""Loopback-only, synthetic WZOS responsive preview. Never deploy this server."""
import argparse
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
from urllib.parse import parse_qs
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'scripts' / 'mobile_preview'
sys.path.insert(0, str(ROOT))


class MobilePreview:
    """Keep the application unchanged; allow same-origin framing only in this harness."""
    def __init__(self, application):
        self.application = application

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.application(scope, receive, send)
        from starlette.responses import Response
        headers = dict(scope.get('headers', []))
        host = urlsplit('http://' + headers.get(b'host', b'').decode('latin-1')).hostname
        peer = (scope.get('client') or ('', 0))[0]
        if host not in {'127.0.0.1', 'localhost', '::1'} or peer not in {'127.0.0.1', '::1'}:
            return await Response('Local preview only', status_code=403)(scope, receive, send)
        # Read-only synthetic dispatch data belongs only to this loopback harness.
        # Production dispatch remains account-backed and is not changed here.
        if scope['path'] in {'/api/dispatch/my-assignments', '/api/dispatch/notifications'} and scope['method'] == 'GET':
            from starlette.responses import JSONResponse
            def result(body, status=200):
                return JSONResponse(body, status_code=status, headers={'Cache-Control': 'no-store', 'X-WZOS-Synthetic-Preview': '1'})
            origin = headers.get(b'origin')
            if (origin and origin != b'http://' + headers.get(b'host', b'')) or headers.get(b'sec-fetch-site') == b'cross-site':
                return await result({'detail': 'Same-origin preview only'}, 403)(scope, receive, send)
            identity = headers.get(b'x-preview-actor', b'').decode('latin-1')
            if identity not in {'core-admin', 'core-general', 'enterprise-admin', 'enterprise-general'}:
                return await result({'detail': 'Select a synthetic preview identity'}, 401)(scope, receive, send)
            if not identity.startswith('enterprise-'):
                return await result({'detail': 'My jobs requires Enterprise'}, 403)(scope, receive, send)
            if scope['path'].endswith('/notifications'):
                return await result({'pending_count': 0})(scope, receive, send)
            query = parse_qs(scope.get('query_string', b'').decode('latin-1'))
            phase = query.get('phase', ['upcoming'])[0]
            try:
                offset = int(query.get('offset', ['0'])[0])
                if offset < 0 or phase not in {'upcoming', 'finished', 'all'}:
                    raise ValueError()
            except ValueError:
                return await result({'detail': 'Invalid assignment filter'}, 422)(scope, receive, send)
            start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
            name = 'Jordan Lee' if identity.endswith('admin') else 'Casey Morgan'
            item = {'id': 'preview-assignment-' + identity, 'order_id': 'enterprise-sample',
                    'order_title': 'Granby Street markings', 'address': 'Granby Street, Norfolk, VA',
                    'starts_at': start.isoformat(), 'ends_at': (start + timedelta(hours=8)).isoformat(),
                    'status': 'accepted', 'role_title': 'Crew member', 'snapshot_state': 'dispatched',
                    'crew': [{'name': name, 'role_title': 'Crew member'}],
                    'notes': 'Synthetic preview assignment. No live dispatch or text is sent.'}
            total = 0 if phase == 'finished' else 1
            return await result({'items': [item] if total and offset == 0 else [], 'total': total,
                                 'offset': offset, 'limit': 25})(scope, receive, send)
        assets = {'/__simulator': ('index.html', 'text/html'),
                  '/__simulator/preview.css': ('preview.css', 'text/css'),
                  '/__simulator/preview.js': ('preview.js', 'application/javascript')}
        if scope['path'] in assets:
            filename, mime = assets[scope['path']]
            response = Response((ASSETS / filename).read_bytes(), media_type=mime, headers={
                'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
                'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; frame-src 'self'; frame-ancestors 'none'; base-uri 'none'",
                'X-Frame-Options': 'DENY'})
            return await response(scope, receive, send)

        async def local_send(message):
            if message['type'] == 'http.response.start' and scope['path'] == '/':
                result = []
                for name, value in message.get('headers', []):
                    if name.lower() == b'x-frame-options':
                        value = b'SAMEORIGIN'
                    elif name.lower() == b'content-security-policy':
                        value = re.sub(rb"frame-ancestors\s+[^;]+", b"frame-ancestors 'self'", value)
                    result.append((name, value))
                message = {**message, 'headers': result}
            await send(message)
        return await self.application(scope, receive, local_send)


def build_application():
    if os.environ.get('K_SERVICE') or os.environ.get('GAE_ENV'):
        raise RuntimeError('The simulator cannot run in a cloud runtime.')
    os.environ['WZOS_WORKSPACE_PREVIEW'] = '1'
    from services.workspace_preview.app import create_app
    from services.v2.knowledge.store import Store
    data = ROOT / '.local-data' / 'mobile-simulator'
    data.mkdir(parents=True, exist_ok=True)
    app = create_app(data / 'preview.sqlite', Store(data / 'sources', {}))
    return MobilePreview(app)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, choices=(8081, 8083), default=8083)
    args = parser.parse_args()
    import uvicorn
    print(f'WZOS mobile preview: http://127.0.0.1:{args.port}/__simulator', flush=True)
    uvicorn.run(build_application(), host='127.0.0.1', port=args.port, access_log=False)
