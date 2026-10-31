"""Staging isolation guards. No Stripe calls or customer data."""
import os
import unittest
from unittest.mock import patch
from services.workspace_preview.purchases import StripeProvider
from services.workspace_preview.commerce_runtime import configured_purchases


class StagingConfigurationTests(unittest.TestCase):
    def test_explicit_test_origin_is_used_for_both_returns(self):
        provider = StripeProvider('rk_test_synthetic', 'whsec_synthetic',
                                  test_return_origin='https://checkout-test.example.test/')
        with patch.object(provider.client.v1.checkout.sessions, 'create') as create:
            provider.create_session('11111111-1111-4111-8111-111111111111', 'buyer@example.test', [])
            payload = create.call_args.args[0]
        self.assertEqual(payload['success_url'], 'https://checkout-test.example.test/?purchase={CHECKOUT_SESSION_ID}')
        self.assertEqual(payload['cancel_url'], 'https://checkout-test.example.test/?checkout=cancelled')

    def test_live_checkout_cannot_use_test_return(self):
        with self.assertRaises(ValueError):
            StripeProvider('rk_live_synthetic', 'whsec_synthetic', livemode=True,
                           test_return_origin='https://checkout-test.example.test')

    def test_test_returns_reject_production_and_unsafe_urls(self):
        for origin in ('https://app.workzoneos.org', 'https://clock.superiorllc.org',
                       'http://checkout-test.example.test', 'https://user:pass@example.test',
                       'https://example.test/path', 'https://example.test?next=x',
                       'https://example.test/#fragment', 'https://example.test:8443',
                       ' https://example.test'):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                StripeProvider('rk_test_synthetic', 'whsec_synthetic', test_return_origin=origin)

    def test_live_configuration_refuses_test_catalog_before_reading_it(self):
        with patch.dict(os.environ, {'WZOS_COMMERCE_ENABLED':'1', 'WZOS_STRIPE_MODE':'live',
                                    'WZOS_STRIPE_TEST_CATALOG':'does-not-exist.json'}):
            with self.assertRaisesRegex(RuntimeError, 'forbidden'):
                configured_purchases(None)
