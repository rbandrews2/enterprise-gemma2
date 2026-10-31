import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from services.workspace_preview.commerce_acceptance import create_app, validate_environment
from services.workspace_preview.storage import SQLiteStorage


class AcceptanceSurfaceTests(unittest.TestCase):
    def environment(self, role='webhook'):
        return {'K_SERVICE':'wzos-checkout-acceptance-'+role, 'WZOS_CHECKOUT_ACCEPTANCE':'1',
                'WZOS_STRIPE_MODE':'test', 'WZOS_COMMERCE_ENABLED':'1',
                'WZOS_DATABASE_URL':'postgresql:///wzos_checkout_acceptance',
                'WZOS_STRIPE_TEST_CATALOG':str(Path('knowledge/billing/acceptance-stripe-catalog.json').resolve()),
                'WZOS_STRIPE_TEST_RETURN_ORIGIN':'https://acceptance.example.test',
                'WZOS_STRIPE_API_KEY':'rk_test_synthetic', 'WZOS_STRIPE_WEBHOOK_SECRET':'whsec_synthetic',
                'WZOS_PURCHASE_ENCRYPTION_KEY':Fernet.generate_key().decode()}

    def test_startup_refuses_production_database_service_or_mode(self):
        for key, value in [('K_SERVICE','wzos-v2-accounts'), ('WZOS_DATABASE_URL','postgresql:///wzos'),
                           ('WZOS_STRIPE_MODE','live'), ('WZOS_CHECKOUT_ACCEPTANCE','0')]:
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                validate_environment({**self.environment(), key:value})

    def test_public_surface_has_no_checkout_receipt_or_account_routes(self):
        with tempfile.TemporaryDirectory() as root:
            storage = SQLiteStorage(Path(root)/'acceptance.sqlite')
            storage.initialize = lambda: None
            storage.close = lambda: None
            with patch.dict(os.environ, self.environment(), clear=True), \
                 patch('services.workspace_preview.commerce_acceptance.PostgreSQLStorage', return_value=storage):
                with TestClient(create_app()) as client:
                    for method, path in [('post','/api/account/checkout'), ('get','/api/account/purchases'),
                                         ('post','/api/account/organizations')]:
                        self.assertEqual(getattr(client, method)(path).status_code, 404)
                    self.assertEqual(client.post('/api/commerce/webhook', content=b'{}').status_code, 400)
                    self.assertEqual(client.get('/').headers['cache-control'], 'no-store')

    def test_private_control_requires_explicit_synthetic_buyer_after_iam(self):
        with tempfile.TemporaryDirectory() as root:
            storage = SQLiteStorage(Path(root)/'acceptance.sqlite')
            storage.initialize = lambda: None
            storage.close = lambda: None
            with patch.dict(os.environ, self.environment('control'), clear=True), \
                 patch('services.workspace_preview.commerce_acceptance.PostgreSQLStorage', return_value=storage):
                with TestClient(create_app()) as client:
                    self.assertEqual(client.post('/api/commerce/webhook', content=b'{}').status_code,404)
                    self.assertEqual(client.get('/api/account/commerce').status_code,401)
                    result=client.get('/api/account/commerce', headers={'X-WZOS-Authorization':'Bearer core'})
                    self.assertEqual(result.status_code,200)
                    self.assertEqual({x['id'] for x in result.json()['offers']}, {'core','enterprise'})
