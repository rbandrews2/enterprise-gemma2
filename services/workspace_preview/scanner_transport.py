"""Private Cloud Run scanner client. No retries, URL input or stored credentials."""
import hashlib
import json
import os
import re
import threading
from time import monotonic
from urllib.parse import urlsplit
from uuid import uuid4

import httpx

MAX_BYTES = 10 * 1024 * 1024


def scanner_origin(value):
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or not parsed.hostname.endswith('.run.app')
            or parsed.username or parsed.password or parsed.port or parsed.path not in ('', '/')
            or parsed.query or parsed.fragment or re.search(r'[\s\\]', value)):
        raise ValueError('Exact private scanner HTTPS run.app origin required')
    return value.rstrip('/')


class BoundedGoogleRequest:
    """Bound Google's metadata/certificate HTTP operations independently."""
    def __call__(self, *args, **kwargs):
        from google.auth.transport.requests import Request
        kwargs['timeout'] = 5
        return Request()(*args, **kwargs)


def identity_token(audience):
    from google.oauth2.id_token import fetch_id_token
    return fetch_id_token(BoundedGoogleRequest(), audience)


class RemoteScanner:
    slots = threading.BoundedSemaphore(1)

    def __init__(self, *, token_provider=identity_token, transport=None):
        self.url = os.getenv('WZOS_SCANNER_URL', '').strip()
        self.configured = bool(self.url)
        self.token_provider, self.transport = token_provider, transport

    def scan(self, data):
        from .security import ScanResult
        if not self.configured:
            return ScanResult('unavailable')
        if not isinstance(data, bytes) or not 0 < len(data) <= MAX_BYTES or not self.slots.acquire(blocking=False):
            return ScanResult('error')
        try:
            # The private service can spend its first request starting the
            # signature-checked engine. Its request limit is 60 seconds.
            deadline = monotonic() + 70
            origin = scanner_origin(self.url)
            from .archive_policy import zip_complete
            if not zip_complete(data):
                return ScanResult('error')
            token = self.token_provider(origin)
            if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{16,8192}', token):
                return ScanResult('error')
            request_id, digest = str(uuid4()), hashlib.sha256(data).hexdigest()
            with httpx.Client(transport=self.transport, follow_redirects=False, trust_env=False,
                              timeout=httpx.Timeout(65, connect=5)) as client:
                with client.stream('POST', origin + '/scan', content=data, headers={
                    'Authorization': 'Bearer ' + token,
                    # Cloud Run consumes this header, preserving Authorization for
                    # independent application token verification.
                    'X-Serverless-Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/octet-stream',
                    'X-Scan-Request': request_id, 'X-Content-SHA256': digest,
                }) as response:
                    if (response.status_code != 200 or response.headers.get('content-encoding')
                            or response.headers.get('content-type', '').split(';')[0] != 'application/json'):
                        return ScanResult('error')
                    raw = bytearray()
                    for part in response.iter_raw():
                        if monotonic() > deadline:
                            return ScanResult('error')
                        raw.extend(part)
                        if len(raw) > 4096:
                            return ScanResult('error')
            result = json.loads(raw)
            if monotonic() > deadline:
                return ScanResult('error')
            if (not isinstance(result, dict) or set(result) != {'version', 'request_id', 'sha256', 'byte_count', 'status', 'engine'}
                    or type(result['version']) is not int or result['version'] != 1
                    or result['request_id'] != request_id or result['sha256'] != digest
                    or type(result['byte_count']) is not int or result['byte_count'] != len(data)
                    or result['status'] not in ('clean', 'infected', 'error')
                    or not isinstance(result['engine'], str)):
                return ScanResult('error')
            if result['status'] != 'error' and not re.fullmatch(r'ClamAV [0-9][0-9A-Za-z.+~-]{0,63}/[0-9]{1,20}', result['engine']):
                return ScanResult('error')
            return ScanResult(result['status'], result['engine'] if result['status'] != 'error' else '')
        except Exception:
            # Do not expose exceptions containing identity tokens or file bytes.
            return ScanResult('error')
        finally:
            self.slots.release()
