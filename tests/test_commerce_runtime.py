import hashlib
import hmac
import json
import os
import unittest
from unittest.mock import patch
from uuid import uuid4
from cryptography.fernet import Fernet
import test_seat_licensing as seats
from test_purchase_onboarding import ProviderFixture
from services.workspace_preview.purchases import Purchases, Offer
from services.workspace_preview.commerce_runtime import register, configured_purchases


class CommerceRuntimeTests(seats.SeatLicensingTests):
    def setUp(self):
        super().setUp()
        self.provider = ProviderFixture()
        self.subscription = {'id':'sub_synthetic','customer':'cus_synthetic','livemode':False,
            'status':'active','latest_invoice':{'id':'in_synthetic','status':'paid','paid':True},
            'items':{'data':[{'price':{'id':'price_monthly'},'quantity':1}], 'has_more':False}}
        self.provider.retrieve_subscription = lambda id_: self.subscription
        self.offer = Offer('core','core',15,30,9900,5900,300,'price_setup','price_monthly','price_extra')
        self.purchases = Purchases(self.accounts,self.provider,[self.offer],Fernet(Fernet.generate_key()),recurring_lifecycle=True)
        register(self.client.app,self.accounts,self.purchases)

    def buy(self):
        body={'request_id':str(uuid4()),'offer_id':'core','seats':15}
        result=self.client.post('/api/account/checkout',headers=self.headers(),json=body)
        self.assertEqual(result.status_code,200,result.text)
        self.session_id=result.json()['session_id']
        self.provider.sessions[self.session_id].update(payment_status='paid',subscription='sub_synthetic',customer='cus_synthetic')
        return body

    def event(self,kind='checkout.session.completed',obj=None,id_=None):
        obj=obj or {'id':self.session_id}
        raw=json.dumps({'id':id_ or 'evt_'+uuid4().hex,'livemode':False,'type':kind,'data':{'object':obj}}).encode()
        signature=hmac.new(b'synthetic-only',raw,hashlib.sha256).hexdigest()
        return self.client.post('/api/commerce/webhook',content=raw,headers={'stripe-signature':signature})

    def receipt(self,user='buyer'):
        return self.client.get('/api/account/purchases/'+self.session_id,headers=self.headers(user))

    def test_authenticated_purchase_and_private_activation_end_to_end(self):
        self.assertEqual(self.client.get('/api/account/commerce').status_code,401)
        offers=self.client.get('/api/account/commerce',headers=self.headers()).json()
        self.assertTrue(offers['enabled']);self.assertNotIn('monthly_price_id',offers['offers'][0])
        body=self.buy()
        self.assertEqual(self.client.post('/api/account/checkout',json=body).status_code,401)
        self.assertEqual(self.provider.sessions[self.session_id]['customer_details']['email'],'buyer@example.test')
        self.assertEqual(self.receipt().json()['status'],'pending')
        self.assertTrue(self.event().json()['fulfilled'])
        self.assertEqual(self.receipt('other').status_code,404)
        code=self.receipt().json()['activation_code']
        created=self.client.post('/api/account/organizations',headers=self.headers(),json={'name':'Paid company','activation_code':code})
        self.assertEqual(created.status_code,200,created.text);self.org=created.json()['id']
        self.assertEqual(self.status()['seat_limit'],15)
        self.assertFalse(self.client.get('/api/account/commerce',headers=self.headers()).json()['enabled'])
        self.assertEqual(self.client.post('/api/account/checkout',headers=self.headers(),json={**body,'request_id':str(uuid4())}).status_code,409)

    def test_subscription_failure_recovery_cancellation_and_stale_invoice(self):
        self.buy();self.assertEqual(self.event().status_code,200)
        code=self.receipt().json()['activation_code']
        self.org=self.client.post('/api/account/organizations',headers=self.headers(),json={'name':'Subscription company','activation_code':code}).json()['id']
        invoice={'id':'in_old','parent':{'subscription_details':{'subscription':'sub_synthetic'}}}
        self.subscription.update(status='past_due',latest_invoice={'status':'open','paid':False})
        result=self.event('invoice.payment_failed',invoice,id_='evt_failure')
        self.assertEqual(result.status_code,200,result.text)
        self.assertTrue(self.event('invoice.payment_failed',invoice,id_='evt_failure').json()['duplicate'])
        self.assertEqual(self.client.get('/api/account/license',headers=self.headers()).status_code,403)
        self.assertEqual(self.receipt().status_code,403)
        self.subscription.update(status='active',latest_invoice={'status':'paid','paid':True})
        # A delayed failure notification observes the current paid subscription.
        self.assertEqual(self.event('invoice.payment_failed',invoice).status_code,200)
        self.assertEqual(self.client.get('/api/account/license',headers=self.headers()).status_code,200)
        self.subscription['status']='canceled'
        self.assertEqual(self.event('customer.subscription.deleted',{'id':'sub_synthetic'}).status_code,200)
        self.assertEqual(self.client.get('/api/account/license',headers=self.headers()).status_code,403)

    def test_wrong_subscription_customer_price_and_unpaid_latest_invoice_never_activate(self):
        self.buy()
        for field,value in [('customer','cus_other'),('status','canceled'),('latest_invoice',{'status':'open','paid':False}),('items',{'data':[]})]:
            original=self.subscription[field];self.subscription[field]=value
            self.assertEqual(self.event().status_code,400)
            self.subscription[field]=original
        with self.db.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM activation_codes').fetchone()[0],0)

    def test_failure_before_redemption_blocks_activation_but_not_identity(self):
        self.buy();self.assertEqual(self.event().status_code,200)
        code=self.receipt().json()['activation_code']
        self.subscription['status']='canceled'
        self.event('customer.subscription.deleted',{'id':'sub_synthetic'})
        response=self.client.post('/api/account/organizations',headers=self.headers(),json={'name':'Cancelled purchase','activation_code':code})
        self.assertEqual(response.status_code,403)
        self.assertEqual(self.client.get('/api/account',headers=self.headers()).status_code,200)

    def test_member_cannot_purchase_or_spoof_purchasing_email(self):
        self.create();token=self.invite('member');self.join('member',token)
        self.assertEqual(self.client.get('/api/account/commerce',headers=self.headers('member')).json(),{'enabled':False,'offers':[]})
        body={'request_id':str(uuid4()),'offer_id':'core','seats':15}
        self.assertEqual(self.client.post('/api/account/checkout',headers=self.headers('member'),json=body).status_code,409)
        self.assertEqual(self.client.post('/api/account/checkout',headers=self.headers('other'),json={**body,'email':'buyer@example.test'}).status_code,422)

    def test_invalid_signature_unknown_subscription_and_concurrent_update(self):
        self.buy();self.event()
        self.assertEqual(self.client.post('/api/commerce/webhook',content=b'{}',headers={'stripe-signature':'forged'}).status_code,400)
        self.assertTrue(self.event('customer.subscription.updated',{'id':'sub_unowned'}).json()['ignored'])
        original=self.provider.retrieve_subscription
        def concurrent(id_):
            with self.db.connect() as db:db.execute('UPDATE purchase_subscriptions SET version=version+1')
            return original(id_)
        self.provider.retrieve_subscription=concurrent
        self.assertEqual(self.event('customer.subscription.updated',{'id':'sub_synthetic'}).status_code,409)

    def test_reload_cannot_create_a_second_subscription_for_the_same_identity(self):
        body=self.buy()
        retry=self.client.post('/api/account/checkout',headers=self.headers(),json={**body,'request_id':str(uuid4())})
        self.assertEqual(retry.status_code,200,retry.text)
        self.assertEqual(retry.json()['session_id'],self.session_id)
        self.assertEqual(self.provider.calls,1)
        changed=self.client.post('/api/account/checkout',headers=self.headers(),json={**body,'request_id':str(uuid4()),'seats':16})
        self.assertEqual(changed.status_code,409)

    def test_runtime_is_disabled_without_explicit_configuration(self):
        with patch.dict(os.environ,{'WZOS_COMMERCE_ENABLED':'0'}):
            self.assertIsNone(configured_purchases(self.accounts))
        with patch.dict(os.environ,{'WZOS_COMMERCE_ENABLED':'1','WZOS_STRIPE_MODE':'live','WZOS_STRIPE_TAX_VERIFIED':'0'}):
            with self.assertRaisesRegex(RuntimeError,'tax configuration'):configured_purchases(self.accounts)

    def test_checkout_pause_preserves_pending_fulfillment_and_billing_enforcement(self):
        self.buy()
        with patch.dict(os.environ, {'WZOS_COMMERCE_CHECKOUT_PAUSED':'1'}):
            self.assertEqual(self.client.get('/api/account/commerce',headers=self.headers()).json(),{'enabled':False,'offers':[]})
            response=self.client.post('/api/account/checkout',headers=self.headers(),json={
                'request_id':str(uuid4()),'offer_id':'core','seats':15})
            self.assertEqual(response.status_code,503)
            self.assertEqual(self.provider.calls,1)
            self.assertEqual(self.event().status_code,200)
            code=self.receipt().json()['activation_code']
            created=self.client.post('/api/account/organizations',headers=self.headers(),json={
                'name':'Already paid company','activation_code':code})
            self.assertEqual(created.status_code,200,created.text)
            self.org=created.json()['id']
            self.subscription['status']='canceled'
            self.assertEqual(self.event('customer.subscription.deleted',{'id':'sub_synthetic'}).status_code,200)
            self.assertEqual(self.client.get('/api/account/license',headers=self.headers()).status_code,403)
            self.subscription['status']='active'
            self.assertEqual(self.event('customer.subscription.updated',{'id':'sub_synthetic'}).status_code,200)
            self.assertEqual(self.client.get('/api/account/license',headers=self.headers()).status_code,200)
        # Removing the pause restores offers for an unrelated new customer.
        self.assertTrue(self.client.get('/api/account/commerce',headers=self.headers('other')).json()['enabled'])


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'),'Dedicated PostgreSQL test database not configured')
class PostgreSQLCommerceRuntimeTests(CommerceRuntimeTests):
    storage=seats.PostgreSQLSeatLicensingTests.storage
