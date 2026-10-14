"""Bounded, non-account-creating Firebase origin acceptance check.

No real password, email recipient, token or API-key value is logged. Success proves
provider-origin configuration, not a real user's successful authentication.
"""
import argparse
import json
import urllib.error
import urllib.parse
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(url, body=None, origin=None, form=False):
    headers = {}
    if origin:
        headers.update(Origin=origin, Referer=origin + '/')
    if body is not None:
        headers['Content-Type'] = ('application/x-www-form-urlencoded' if form
                                   else 'application/json')
        body = (urllib.parse.urlencode(body) if form else json.dumps(body)).encode()
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        response = urllib.request.build_opener(NoRedirect).open(req, timeout=30)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        raw = response.read(65537)
        if len(raw) > 65536:
            raise ValueError('Response exceeded size limit')
        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = {}
        return response.code, payload


def validation_reached(status, payload, expected):
    message = payload.get('error', {}).get('message', '')
    code = message.split(' : ')[0].split(':')[0].strip()
    return status == 400 and code in expected


def check(origin):
    parsed = urllib.parse.urlsplit(origin)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username
            or parsed.password or parsed.path or parsed.query or parsed.fragment):
        raise ValueError('Use an exact HTTPS origin without a path')
    status, config = request(origin + '/api/identities')
    key = config.get('auth_api_key')
    if status != 200 or config.get('mode') != 'verified_accounts' or not key:
        raise ValueError('Verified-account browser configuration is unavailable')
    actions = [
        ('signInWithPassword', {'email': 'invalid-email', 'password': '',
                                'returnSecureToken': True}, {'INVALID_EMAIL', 'MISSING_PASSWORD'}),
        ('signUp', {'email': 'invalid-email', 'password': '',
                    'returnSecureToken': True}, {'INVALID_EMAIL', 'MISSING_PASSWORD'}),
        ('sendOobCode', {'requestType': 'PASSWORD_RESET', 'email': 'invalid-email'},
         {'INVALID_EMAIL'}),
    ]
    results = []
    for action, body, expected in actions:
        url = ('https://identitytoolkit.googleapis.com/v1/accounts:' + action
               + '?key=' + urllib.parse.quote(key, safe=''))
        status, payload = request(url, body, origin)
        results.append({'check': action, 'status': status,
                        'passed': validation_reached(status, payload, expected)})
    refresh_url = ('https://securetoken.googleapis.com/v1/token?key='
                   + urllib.parse.quote(key, safe=''))
    status, payload = request(refresh_url, {'grant_type': 'refresh_token',
                                           'refresh_token': 'invalid-token'}, origin, True)
    results.append({'check': 'refresh', 'status': status,
                    'passed': validation_reached(status, payload, {'INVALID_REFRESH_TOKEN'})})
    url = ('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key='
           + urllib.parse.quote(key, safe=''))
    status, payload = request(url, actions[0][1], 'https://untrusted.example')
    reasons = {d.get('reason') for d in payload.get('error', {}).get('details', [])}
    results.append({'check': 'untrusted_origin', 'status': status,
                    'passed': status == 403 and 'API_KEY_HTTP_REFERRER_BLOCKED' in reasons})
    status, _ = request(origin + '/api/account')
    results.append({'check': 'protected_account', 'status': status, 'passed': status == 401})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', required=True)
    args = parser.parse_args()
    try:
        results = check(args.origin)
    except Exception:
        # Network exceptions can embed a key-bearing provider URL.
        print('Authentication origin check failed: network or configuration error; no credential output.')
        return 1
    print(json.dumps(results, indent=2))
    accepted = all(item['passed'] for item in results)
    print('AUTH_ORIGIN_GATE: ' + ('PASS' if accepted else 'FAIL'))
    return 0 if accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())
