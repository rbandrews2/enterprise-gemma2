import base64
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from scripts.validate_atlas_grounding_staging import require_token_lifetime, record_check


def token(expiry):
    payload = base64.urlsafe_b64encode(json.dumps({'exp':expiry}).encode()).decode().rstrip('=')
    return 'header.'+payload+'.signature'


class GroundingPreflightTests(unittest.TestCase):
    @patch('scripts.validate_atlas_grounding_staging.time.time', return_value=1000)
    def test_expired_and_near_expiry_rejected(self, now):
        for expiry in (900, 1000, 1419):
            with self.subTest(expiry=expiry), self.assertRaisesRegex(RuntimeError, 'insufficient'):
                require_token_lifetime(token(expiry), 'Operator')
        require_token_lifetime(token(1420), 'Operator')

    def test_invalid_expiry_does_not_reveal_token(self):
        for value in ('secret-token', token(None), token(True), token('5000'), token(float('nan'))):
            with self.subTest(value=value), self.assertRaises(RuntimeError) as error:
                require_token_lifetime(value, 'Operator')
            self.assertNotIn(value, str(error.exception))

    def test_failed_http_retains_only_safe_evidence(self):
        evidence = io.StringIO()
        response = SimpleNamespace(status_code=401, text='secret', headers={'Authorization':'secret'})
        with self.assertRaisesRegex(RuntimeError, 'HTTP 401'):
            record_check(evidence, 'private_app_access', response, 200)
        self.assertEqual(json.loads(evidence.getvalue()), {'stage':'private_app_access','status':401,'passed':False})
        record_check(evidence, 'stale_version_denial', SimpleNamespace(status_code=409), 409)
        self.assertEqual(len(evidence.getvalue().splitlines()), 2)
