"""Twilio SMS transport and webhook signatures. No SDK dependency, no secrets in results.

Results distinguish what is known about the provider request:
accepted (Twilio created a message), rejected (Twilio refused it, never retried),
retryable (the request was not processed) and ambiguous (it may have been created;
never resent automatically because the Messages API has no idempotency key).
"""
import base64
import hashlib
import hmac
import os
from dataclasses import dataclass

import httpx

# Twilio error codes that mean the recipient has opted out of this sender.
OPTED_OUT_CODES = {'21610'}
CONFIG_NAMES = ('WZOS_TWILIO_ACCOUNT_SID', 'WZOS_TWILIO_AUTH_TOKEN', 'WZOS_PUBLIC_BASE_URL')
SENDER_NAMES = ('WZOS_TWILIO_MESSAGING_SERVICE_SID', 'WZOS_TWILIO_FROM_NUMBER')


@dataclass
class SendResult:
    outcome: str  # accepted | rejected | retryable | ambiguous
    sid: str | None = None
    provider_status: str | None = None
    error_code: str | None = None
    detail: str = ''


def signature(token, url, params):
    """X-Twilio-Signature for a form POST: HMAC-SHA1 over URL plus sorted key/value pairs."""
    data = url + ''.join(key + value for key, value in sorted(params))
    return base64.b64encode(hmac.new(token.encode(), data.encode(), hashlib.sha1).digest()).decode()


def valid_signature(token, url, params, supplied):
    return bool(token and supplied) and hmac.compare_digest(signature(token, url, params), supplied)


def settings():
    """Configuration readiness by name only; values are never returned."""
    missing = [name for name in CONFIG_NAMES if not os.getenv(name, '').strip()]
    if not any(os.getenv(name, '').strip() for name in SENDER_NAMES):
        missing.append(' or '.join(SENDER_NAMES))
    base = os.getenv('WZOS_PUBLIC_BASE_URL', '').strip().rstrip('/')
    if base and not base.startswith('https://'):
        missing.append('WZOS_PUBLIC_BASE_URL (must use https)')
    return {'missing': missing, 'base_url': base}


class TwilioProvider:
    api = 'https://api.twilio.com/2010-04-01'

    def __init__(self, account_sid, auth_token, base_url, messaging_service_sid='', from_number='', transport=None):
        self.account_sid, self.auth_token, self.base_url = account_sid, auth_token, base_url.rstrip('/')
        self.messaging_service_sid, self.from_number = messaging_service_sid, from_number
        self.transport = transport

    @classmethod
    def from_environment(cls):
        if settings()['missing']:
            return None
        return cls(os.environ['WZOS_TWILIO_ACCOUNT_SID'].strip(), os.environ['WZOS_TWILIO_AUTH_TOKEN'].strip(),
                   os.environ['WZOS_PUBLIC_BASE_URL'].strip(),
                   os.getenv('WZOS_TWILIO_MESSAGING_SERVICE_SID', '').strip(), os.getenv('WZOS_TWILIO_FROM_NUMBER', '').strip())

    def callback_url(self, outbox_id):
        return f'{self.base_url}/api/messaging/twilio/status?outbox={outbox_id}'

    def send(self, outbox_id, to, body):
        form = {'To': to, 'Body': body, 'StatusCallback': self.callback_url(outbox_id)}
        if self.messaging_service_sid:
            form['MessagingServiceSid'] = self.messaging_service_sid
        else:
            form['From'] = self.from_number
        url = f'{self.api}/Accounts/{self.account_sid}/Messages.json'
        try:
            with httpx.Client(timeout=httpx.Timeout(10.0, connect=5.0), transport=self.transport) as client:
                response = client.post(url, data=form, auth=(self.account_sid, self.auth_token))
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout):
            # No connection was established, so Twilio cannot have created a message.
            return SendResult('retryable', detail='Provider connection unavailable')
        except httpx.HTTPError:
            return SendResult('ambiguous', detail='Provider response not received')
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if response.status_code in (200, 201) and payload.get('sid'):
            return SendResult('accepted', sid=payload['sid'], provider_status=payload.get('status'))
        code = str(payload.get('code') or '') or None
        if response.status_code in (429, 503):
            return SendResult('retryable', error_code=code, detail=f'Provider busy ({response.status_code})')
        if response.status_code >= 500:
            return SendResult('ambiguous', error_code=code, detail=f'Provider error ({response.status_code})')
        # Twilio's message text can echo the number; keep only the code and HTTP status.
        return SendResult('rejected', error_code=code, detail=f'Provider refused the message ({response.status_code})')
