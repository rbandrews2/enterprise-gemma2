"""Explicit SDK gate: requires requirements-commerce.txt; never contacts Stripe."""
import hashlib
import hmac
import json
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

from services.workspace_preview.purchases import StripeProvider


class StripeSDKTests(unittest.TestCase):
    def test_environment_and_restricted_key_guard(self):
        for key in ['sk_live_synthetic','rk_live_synthetic','rk_test_ contains_space']:
            with self.assertRaises(ValueError):StripeProvider(key,'whsec_synthetic')
        with self.assertRaises(ValueError):StripeProvider('rk_test_synthetic','missing')
        with self.assertRaises(ValueError):
            StripeProvider('rk_test_synthetic','whsec_synthetic',automatic_tax=True)

    def test_checkout_uses_fixed_urls_idempotency_and_explicit_tax_opt_in(self):
        request_id=str(uuid4());items=[{'price':'price_synthetic','quantity':1}]
        with patch('stripe.StripeClient') as client:
            provider=StripeProvider('rk_test_synthetic','whsec_synthetic',automatic_tax=True,tax_configuration_verified=True)
            provider.create_session(request_id,'buyer@example.test',items)
            params=client.return_value.v1.checkout.sessions.create.call_args.args[0]
            options=client.return_value.v1.checkout.sessions.create.call_args.kwargs['options']
            self.assertEqual(params['automatic_tax'],{'enabled':True})
            self.assertEqual(params['client_reference_id'],request_id)
            self.assertEqual(params['mode'],'subscription')
            self.assertEqual(params['line_items'],items)
            self.assertTrue(params['success_url'].startswith('https://app.workzoneos.org/'))
            self.assertEqual(options['idempotency_key'],'wzos-checkout-'+request_id)
            self.assertNotIn('payment_method_types',params)
            self.assertEqual(client.call_args.kwargs['max_network_retries'],0)

    def test_real_sdk_authenticates_exact_raw_bytes_and_rejects_forgery_and_expiry(self):
        secret='whsec_synthetic_only'
        provider=StripeProvider('rk_test_synthetic',secret)
        body=json.dumps({'id':'evt_synthetic','object':'event','type':'checkout.session.completed',
                         'livemode':False,'data':{'object':{'id':'cs_synthetic'}}}).encode()
        def signature(raw,timestamp):
            digest=hmac.new(secret.encode(),str(timestamp).encode()+b'.'+raw,hashlib.sha256).hexdigest()
            return f't={timestamp},v1={digest}'
        now=int(time.time());header=signature(body,now)
        self.assertEqual(provider.verify_event(body,header)['id'],'evt_synthetic')
        for raw,sig in [(body+b' ',header),(body,'t=1,v1=forged'),(body,signature(body,now-3600))]:
            with self.assertRaises(ValueError):provider.verify_event(raw,sig)


if __name__=='__main__':unittest.main()
