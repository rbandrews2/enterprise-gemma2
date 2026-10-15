"""Bounded synthetic pilot using existing operator impersonation, never IAM writes.

This tests the app principal, not the web runtime's metadata-token path.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request
from uuid import uuid4

CALLER = 'wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def token(audience):
    result = subprocess.run(['gcloud', 'auth', 'print-identity-token',
                             '--project=enterprise-gemma2',
                             '--impersonate-service-account=' + CALLER,
                             '--audiences=' + audience, '--include-email', '--quiet'],
                            capture_output=True, timeout=45)
    if result.returncode or not re.fullmatch(rb'[A-Za-z0-9_.-]{16,8192}\s*', result.stdout):
        raise ValueError('EXISTING_IMPERSONATION_UNAVAILABLE')
    return result.stdout.decode().strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'https://wzos-v2-scanner-[a-z0-9.-]+\.run\.app', args.url):
        raise ValueError('Unexpected pilot origin')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    identity = token(args.url)
    results = {}
    for name, data, authenticated, corrupt, expected in (
        ('anonymous', b'pilot', False, False, 403),
        ('clean', b'%PDF-1.7\nSynthetic pilot only\n%%EOF\n', True, False, 'clean'),
        ('detection', b'X5O!P%@AP[4' + b'\\PZX54(P^)7CC)7}' +
         b'$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*', True, False, 'infected'),
        ('integrity_mismatch', b'synthetic', True, True, 400),
    ):
        request_id = str(uuid4())
        digest = hashlib.sha256(data).hexdigest()
        headers = {'Content-Type': 'application/octet-stream',
                   'X-Scan-Request': request_id,
                   'X-Content-SHA256': '0' * 64 if corrupt else digest}
        if authenticated:
            headers.update(Authorization='Bearer ' + identity,
                           **{'X-Serverless-Authorization': 'Bearer ' + identity})
        request = urllib.request.Request(args.url + '/scan', data=data, headers=headers)
        try:
            with opener.open(request, timeout=65) as response:
                raw = response.read(4097)
                assert response.status == 200 and len(raw) <= 4096
                result = json.loads(raw)
                assert result['request_id'] == request_id and result['sha256'] == digest
                assert result['byte_count'] == len(data) and result['status'] == expected
                assert re.fullmatch(r'ClamAV [0-9][0-9A-Za-z.+~-]{0,63}/[0-9]{1,20}', result['engine'])
                results[name] = {'http': 200, 'status': result['status'], 'traceability': True}
        except urllib.error.HTTPError as error:
            assert error.code == expected
            results[name] = {'http': error.code}
    # Persist only bounded statuses, never headers, tokens, raw errors or file bytes.
    with Path(args.output).open('x', encoding='utf-8') as output:
        json.dump({'principal': CALLER, 'results': results, 'accepted': True}, output)
    print('PRIVATE_SCANNER_PILOT_PASS')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('PRIVATE_SCANNER_PILOT_FAILED ' + type(error).__name__)
        raise SystemExit(1)
