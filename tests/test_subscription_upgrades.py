import copy
import hashlib
import hmac
import json
import os
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

from cryptography.fernet import Fernet
import test_seat_licensing as seats
from test_purchase_onboarding import ProviderFixture
from services.workspace_preview.purchases import Offer, Purchases
from services.workspace_preview.commerce_runtime import register


class UpgradeProvider(ProviderFixture):
    def __init__(self):
        super().__init__()
        self.updates = []
        self.results = {}
        self.ambiguous = False
        self.sub = {'id': 'sub_synthetic', 'customer': 'cus_synthetic', 'livemode': False,
                    'status': 'active', 'collection_method': 'charge_automatically',
                    'latest_invoice': {'id': 'in_core', 'status': 'paid', 'paid': True},
                    'items': {'data': [{'id': 'si_core', 'price': {'id': 'price_monthly'},
                               'quantity': 1, 'current_period_end': int(time.time())+3600}], 'has_more': False}}

    def retrieve_subscription(self, id_):
        return copy.deepcopy(self.sub)

    def preview_upgrade(self, subscription, customer, parameters):
        self.preview_parameters = copy.deepcopy(parameters)
        return {'currency': 'usd', 'amount_due': 102900, 'total_discount_amounts': [{'amount': 2000}]}

    def update_subscription(self, subscription, parameters, request_id):
        if request_id not in self.results:
            self.updates.append((subscription, copy.deepcopy(parameters), request_id))
            invoice = {'id': 'in_upgrade_'+request_id, 'status': 'open', 'paid': False,
                       'currency': 'usd', 'livemode': False, 'customer': 'cus_synthetic', 'billing_reason': 'subscription_update',
                       'hosted_invoice_url': 'https://invoice.stripe.com/i/synthetic',
                       'parent': {'subscription_details': {'subscription': subscription}},
                       'total_discount_amounts': [{'amount': 2000}],
                       'lines': {'data': [{'pricing': {'price_details': {'price': 'price_enterprise_setup'}},
                                          'quantity': 1}], 'has_more': False}}
            self.sub.update(latest_invoice=invoice, pending_update={'metadata': parameters['metadata']})
            self.results[request_id] = copy.deepcopy(self.sub)
        if self.ambiguous:
            raise TimeoutError('Synthetic response loss after provider accepted request')
        return copy.deepcopy(self.results[request_id])

    def settle(self):
        _, parameters, _ = self.updates[-1]
        self.sub['items'] = {'data': [{'id': 'si_enterprise_'+str(i), 'price': {'id': v['price']},
            'quantity': v['quantity'], 'current_period_end': int(time.time())+3600}
            for i, v in enumerate(parameters['items']) if not v.get('deleted')], 'has_more': False}
        self.sub.update(metadata=parameters['metadata'], pending_update=None)
        self.sub['latest_invoice'].update(status='paid', paid=True)


class SubscriptionUpgradeTests(unittest.TestCase):
    storage = seats.SeatLicensingTests.storage
    headers = seats.SeatLicensingTests.headers
    invite = seats.SeatLicensingTests.invite
    join = seats.SeatLicensingTests.join
    status = seats.SeatLicensingTests.status

    def setUp(self):
        seats.SeatLicensingTests.setUp(self)
        enabled = patch.dict(os.environ, {'WZOS_CORE_UPGRADES_ENABLED': '1', 'WZOS_COMMERCE_CHECKOUT_PAUSED': '0'})
        enabled.start();self.addCleanup(enabled.stop)
        self.provider = UpgradeProvider()
        core = Offer('core', 'core', 15, 30, 9900, 5900, 300, 'price_setup', 'price_monthly', 'price_extra')
        enterprise = Offer('enterprise', 'enterprise', 25, None, 99900, 24900, 700,
                           'price_enterprise_setup', 'price_enterprise_monthly', 'price_enterprise_extra')
        self.purchases = Purchases(self.accounts, self.provider, [core, enterprise],
                                   Fernet(Fernet.generate_key()), recurring_lifecycle=True)
        register(self.client.app, self.accounts, self.purchases)
        result = self.client.post('/api/account/checkout', headers=self.headers(),
            json={'request_id': str(uuid4()), 'offer_id': 'core', 'seats': 15})
        self.session = result.json()['session_id']
        self.provider.sessions[self.session].update(payment_status='paid', subscription='sub_synthetic', customer='cus_synthetic')
        self.assertEqual(self.event('checkout.session.completed', {'id': self.session}).status_code, 200)
        code = self.client.get('/api/account/purchases/'+self.session, headers=self.headers()).json()['activation_code']
        result = self.client.post('/api/account/organizations', headers=self.headers(),
                                  json={'name': 'Synthetic Core', 'activation_code': code})
        self.org = result.json()['id']

    def event(self, kind='customer.subscription.updated', obj=None, event_id=None):
        body = json.dumps({'id': event_id or 'evt_'+uuid4().hex, 'livemode': False, 'type': kind,
                           'data': {'object': obj or {'id': 'sub_synthetic'}}}).encode()
        signature = hmac.new(b'synthetic-only', body, hashlib.sha256).hexdigest()
        return self.client.post('/api/commerce/webhook', content=body, headers={'stripe-signature': signature})

    def quote(self, seats=25, user='buyer'):
        return self.client.post('/api/account/upgrade/quote', headers=self.headers(user), json={'seats': seats})

    def confirm(self, quote):
        return self.client.post('/api/account/upgrade/confirm', headers=self.headers(),
            json={'request_id': quote['request_id'], 'confirmed': True})

    def test_quote_has_credit_and_no_provider_write(self):
        result = self.quote()
        self.assertEqual(result.status_code, 200, result.text)
        q = result.json()['quote']
        self.assertEqual((q['credit_cents'], q['setup_cents'], q['monthly_cents'], q['seats']), (2000, 99900, 24900, 25))
        self.assertEqual(self.provider.updates, [])
        self.assertEqual(self.status()['edition'], 'core')

    def test_paid_webhook_atomically_grants_enterprise_and_keeps_purchase_history(self):
        q = self.quote(30).json()
        self.assertEqual(self.confirm(q).status_code, 200)
        self.assertEqual(self.status()['edition'], 'core')
        self.provider.settle()
        event_id = 'evt_paid_upgrade'
        result = self.event(event_id=event_id)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual((self.status()['edition'], self.status()['seat_limit']), ('enterprise', 30))
        self.assertTrue(self.event(event_id=event_id).json()['duplicate'])
        with self.db.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM purchase_subscriptions').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT edition FROM purchase_requests').fetchone()[0], 'core')
            self.assertEqual(db.execute('SELECT COUNT(*) FROM access_audit WHERE action=?', ('enterprise_upgrade_paid',)).fetchone()[0], 1)
        self.assertEqual(self.confirm(q).json()['status'], 'applied')
        self.assertEqual(len(self.provider.updates), 1)

    def test_unpaid_upgrade_retains_only_paid_core_and_cannot_duplicate_credit(self):
        q = self.quote().json();self.confirm(q)
        self.assertEqual(self.event('invoice.payment_failed', self.provider.sub['latest_invoice']).status_code, 200)
        self.assertEqual(self.status()['edition'], 'core')
        self.assertEqual(self.quote(30).json()['status'], 'pending')
        self.confirm(q)
        self.assertEqual(len(self.provider.updates), 1)
        parameters = self.provider.updates[0][1]
        self.assertEqual(parameters['payment_behavior'], 'pending_if_incomplete')
        self.assertEqual(parameters['proration_date'], q['quote']['proration_date'])
        self.assertEqual(parameters['discounts'], [{'coupon': 'wzos_v2_core_upgrade_20_once_20261016'}])

    def test_expired_pending_invoice_does_not_revoke_previously_paid_core(self):
        q = self.quote().json();self.confirm(q)
        self.provider.sub['pending_update'] = None
        self.provider.sub['latest_invoice']['status'] = 'void'
        self.assertEqual(self.event().status_code, 200)
        self.assertEqual(self.status()['edition'], 'core')

    def test_lost_provider_response_retries_same_idempotency_key(self):
        q = self.quote().json();self.provider.ambiguous = True
        self.assertEqual(self.confirm(q).status_code, 503)
        self.provider.ambiguous = False
        self.assertEqual(self.confirm(q).status_code, 200)
        self.assertEqual(len(self.provider.updates), 1)

    def test_members_other_orgs_and_anonymous_cannot_access_billing(self):
        self.assertEqual(self.join('member', self.invite('member')).status_code, 200)
        self.assertEqual(self.quote(user='member').status_code, 403)
        self.assertEqual(self.quote(user='other').status_code, 403)
        self.assertEqual(self.client.get('/api/account/upgrade', headers=self.headers('member')).status_code, 403)
        self.assertEqual(self.client.post('/api/account/upgrade/quote', json={'seats': 25}).status_code, 401)
        self.assertEqual(self.provider.updates, [])

    def test_confirmation_required_and_old_quote_cannot_be_used(self):
        a = self.quote().json();b = self.quote(30).json()
        self.assertEqual(self.confirm(a).status_code, 409)
        self.assertEqual(self.client.post('/api/account/upgrade/confirm', headers=self.headers(),
            json={'request_id': b['request_id'], 'confirmed': False}).status_code, 422)
        self.assertEqual(self.provider.updates, [])

    def test_expired_quote_or_renewal_requires_new_estimate(self):
        q = self.quote().json()
        with patch('services.workspace_preview.subscription_upgrades.time.time', return_value=q['quote']['expires_at']+1):
            self.assertEqual(self.confirm(q).status_code, 409)
        q = self.quote().json();self.event()
        self.assertEqual(self.confirm(q).status_code, 409)
        self.assertEqual(self.provider.updates, [])

    def test_wrong_prices_customer_or_credit_never_grant(self):
        q = self.quote().json();self.confirm(q);self.provider.settle()
        original = copy.deepcopy(self.provider.sub)
        self.provider.sub['latest_invoice']['total_discount_amounts'] = []
        self.assertEqual(self.event().status_code, 200)
        with self.db.connect() as db:
            self.assertEqual(db.execute('SELECT edition FROM organizations WHERE id=?', (self.org,)).fetchone()[0], 'core')
        self.provider.sub = copy.deepcopy(original);self.provider.sub['customer'] = 'cus_foreign'
        self.assertEqual(self.event().status_code, 400)
        self.provider.sub = copy.deepcopy(original);self.provider.sub['items']['data'][0]['price']['id'] = 'price_wrong'
        self.assertEqual(self.event().status_code, 200)
        with self.db.connect() as db:
            self.assertEqual(db.execute('SELECT edition FROM organizations WHERE id=?', (self.org,)).fetchone()[0], 'core')

    def test_renewal_enforces_enterprise_prices_after_upgrade(self):
        self.confirm(self.quote().json());self.provider.settle();self.event()
        self.provider.sub['latest_invoice'] = {'id': 'in_renewal', 'status': 'open', 'paid': False}
        self.provider.sub['status'] = 'past_due';self.event()
        self.assertEqual(self.client.get('/api/account/license', headers=self.headers()).status_code, 403)
        self.provider.sub['latest_invoice'].update(status='paid', paid=True);self.provider.sub['status'] = 'active';self.event()
        self.assertEqual(self.status()['edition'], 'enterprise')

    def test_pause_blocks_new_payments_but_preserves_paid_fulfillment(self):
        q = self.quote().json();self.confirm(q);self.provider.settle()
        with patch.dict(os.environ, {'WZOS_CORE_UPGRADES_ENABLED': '0'}):
            self.assertEqual(self.confirm(q).status_code, 503)
            self.assertEqual(self.event().status_code, 200)
        self.assertEqual(self.status()['edition'], 'enterprise')

    def test_pending_upgrade_cannot_mask_unrelated_failure_or_expired_core_period(self):
        q = self.quote().json();self.confirm(q)
        self.provider.sub['latest_invoice']['id'] = 'in_unrelated'
        self.event()
        self.assertEqual(self.client.get('/api/account/license', headers=self.headers()).status_code, 403)

    def test_pending_upgrade_cannot_extend_expired_core_service(self):
        q = self.quote().json();self.confirm(q)
        with patch('services.workspace_preview.subscription_upgrades.time.time', return_value=time.time()+7200):
            self.assertEqual(self.event().status_code, 200)
        self.assertEqual(self.client.get('/api/account/license', headers=self.headers()).status_code, 403)

    def test_missing_setup_line_or_foreign_paid_invoice_never_grants(self):
        q = self.quote().json();self.confirm(q);self.provider.settle()
        self.provider.sub['latest_invoice']['lines'] = {'data': [], 'has_more': False}
        self.event()
        with self.db.connect() as db:
            self.assertEqual(db.execute('SELECT edition FROM organizations WHERE id=?', (self.org,)).fetchone()[0], 'core')

    def test_quote_rejects_unpaid_pending_and_scheduled_subscriptions(self):
        original = copy.deepcopy(self.provider.sub)
        for key, value in [('status', 'past_due'), ('pending_update', {'expires_at': int(time.time())+100}),
                           ('schedule', 'sub_sched_synthetic'), ('discounts', ['di_existing'])]:
            self.provider.sub[key] = value
            self.assertEqual(self.quote().status_code, 409)
            self.provider.sub = copy.deepcopy(original)
        self.assertEqual(self.provider.updates, [])

    def test_expired_invoice_requires_review_and_cannot_charge_again(self):
        q = self.quote().json();self.confirm(q)
        self.provider.sub['pending_update'] = None
        self.provider.sub['latest_invoice']['status'] = 'void'
        self.event()
        self.assertEqual(self.quote().json()['status'], 'review_required')
        self.assertEqual(self.confirm(q).status_code, 409)
        self.assertEqual(self.status()['edition'], 'core')
        self.assertEqual(len(self.provider.updates), 1)


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'), 'Dedicated PostgreSQL test database not configured')
class PostgreSQLSubscriptionUpgradeTests(SubscriptionUpgradeTests):
    storage = seats.PostgreSQLSeatLicensingTests.storage
