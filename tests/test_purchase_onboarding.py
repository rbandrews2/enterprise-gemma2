import hashlib
import hmac
import json
import os
import unittest
from uuid import uuid4
from cryptography.fernet import Fernet
import test_seat_licensing as seat_fixture
from services.workspace_preview.purchases import Offer, Purchases


class ProviderFixture:
    def __init__(self):
        self.sessions={};self.calls=0;self.retrievals=0
    def create_session(self, request_id, email, items):
        self.calls+=1;id_='cs_synthetic_'+request_id.replace('-','')
        self.sessions.setdefault(id_,{'id':id_,'livemode':False,'status':'complete','mode':'subscription','currency':'usd','amount_total':15800,'payment_status':'unpaid','customer_details':{'email':email},'line_items':{'data':[{'price':{'id':i['price']},'quantity':i['quantity']} for i in items],'has_more':False},'url':'https://checkout.stripe.com/synthetic'})
        return self.sessions[id_]
    def retrieve_session(self, session_id):
        self.retrievals+=1;return self.sessions[session_id]
    def verify_event(self, body, signature):
        if not hmac.compare_digest(signature,hmac.new(b'synthetic-only',body,hashlib.sha256).hexdigest()):raise ValueError('Invalid signature')
        return json.loads(body)


class PurchaseOnboardingTests(seat_fixture.SeatLicensingTests):
    # Reuse the account fixture and seat regression coverage; no provider/network calls.
    def setUp(self):
        super().setUp()
        self.provider=ProviderFixture()
        self.offer=Offer('core','core',15,30,9900,5900,300,'price_synthetic_setup','price_synthetic_monthly','price_synthetic_extra')
        self.purchases=Purchases(self.accounts,self.provider,[self.offer],Fernet(Fernet.generate_key()))
        self.purchases.register_private_receipts(self.client.app)

    def checkout(self, seats=15):
        self.purchase_id=str(uuid4())
        self.session_id=self.purchases.checkout(self.purchase_id,'buyer@example.test','core',seats)['session_id']
        return self.session_id

    def event(self, kind='checkout.session.completed', id_=None, mode=False):
        body=json.dumps({'id':id_ or 'evt_'+uuid4().hex,'livemode':mode,'type':kind,'data':{'object':{'id':self.session_id}}}).encode()
        signature=hmac.new(b'synthetic-only',body,hashlib.sha256).hexdigest()
        return body,signature

    def test_purchase_to_verified_activation_and_core_seats(self):
        self.checkout()
        pending=self.purchases.webhook(*self.event());self.assertTrue(pending['pending'])
        self.assertNotIn('activation_code',self.purchases.receipt(self.session_id,self.claims['buyer']))
        self.provider.sessions[self.session_id]['payment_status']='paid'
        self.assertTrue(self.purchases.webhook(*self.event('checkout.session.async_payment_succeeded'))['fulfilled'])
        r=self.client.get('/api/account/purchases/'+self.session_id,headers=self.headers())
        self.assertEqual(r.status_code,200);receipt=r.json()
        activated=self.client.post('/api/account/organizations',headers=self.headers(),json={'name':'Paid Core organization','activation_code':receipt['activation_code']})
        self.assertEqual(activated.status_code,200,activated.text);self.org=activated.json()['id']
        self.assertEqual((self.status()['edition'],self.status()['seat_limit'],self.status()['seats_used']),('core',15,1))

    def test_duplicate_event_and_distinct_event_for_same_session_issue_one_code(self):
        self.checkout();self.provider.sessions[self.session_id]['payment_status']='paid'
        event=self.event();self.purchases.webhook(*event)
        first=self.purchases.receipt(self.session_id,self.claims['buyer'])['activation_code']
        self.assertTrue(self.purchases.webhook(*event)['duplicate'])
        self.purchases.webhook(*self.event('checkout.session.async_payment_succeeded'))
        self.assertEqual(self.purchases.receipt(self.session_id,self.claims['buyer'])['activation_code'],first)
        with self.db.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM activation_codes').fetchone()[0],1)
            row=db.execute('SELECT sealed_code FROM purchase_requests').fetchone()
            self.assertNotIn(first,row['sealed_code'])

    def test_signature_mode_and_unrecognized_session_do_not_issue_access(self):
        self.checkout();event=self.event()
        with self.assertRaises(ValueError):self.purchases.webhook(event[0],'forged')
        self.assertEqual(self.provider.retrievals,0)
        with self.assertRaises(ValueError):self.purchases.webhook(*self.event(mode=True))
        with self.db.connect() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM activation_codes').fetchone()[0],0)

    def test_price_quantity_amount_and_email_mismatch_rejected(self):
        for mutation in ('price','quantity','amount','email'):
            with self.subTest(mutation=mutation):
                self.checkout();s=self.provider.sessions[self.session_id];s['payment_status']='paid'
                if mutation=='price':s['line_items']['data'][0]['price']['id']='price_unapproved'
                if mutation=='quantity':s['line_items']['data'][0]['quantity']=9
                if mutation=='amount':s['amount_total']=1
                if mutation=='email':s['customer_details']['email']='other@example.test'
                with self.assertRaises(ValueError):self.purchases.webhook(*self.event())
        with self.db.connect() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM activation_codes').fetchone()[0],0)

    def test_checkout_retry_cannot_change_seats_or_buyer(self):
        self.checkout();retry=self.purchases.checkout(self.purchase_id,'buyer@example.test','core',15)
        self.assertEqual(retry['session_id'],self.session_id);self.assertEqual(self.provider.calls,1)
        for email,seats in [('other@example.test',15),('buyer@example.test',16)]:
            with self.assertRaises(Exception) as error:self.purchases.checkout(self.purchase_id,email,'core',seats)
            self.assertEqual(error.exception.status_code,409)

    def test_receipts_require_verified_purchaser_and_cannot_read_other_purchase(self):
        self.checkout()
        url='/api/account/purchases/'+self.session_id
        self.assertEqual(self.client.get(url).status_code,401)
        self.assertEqual(self.client.get(url,headers=self.headers('other')).status_code,404)
        self.claims['buyer']['email_verified']=False
        self.assertEqual(self.client.get(url,headers=self.headers()).status_code,403)

    def test_core_extra_seats_and_invalid_configuration(self):
        self.checkout(17);self.assertEqual(self.provider.sessions[self.session_id]['line_items']['data'][-1]['quantity'],2)
        with self.assertRaises(ValueError):self.purchases.checkout(str(uuid4()),'buyer@example.test','core',31)
        broken=Offer('bad','core',15,30,9900,5900,300,None,None,None)
        with self.assertRaises(ValueError):broken.line_items(15)
        with self.assertRaises(ValueError):Purchases(self.accounts,self.provider,[self.offer],self.purchases.cipher,livemode=True)

    def test_encryption_failure_rolls_back_activation_and_event(self):
        self.checkout();self.provider.sessions[self.session_id]['payment_status']='paid'
        class BrokenCipher:
            def encrypt(self, value):raise RuntimeError('Synthetic encryption failure')
        self.purchases.cipher=BrokenCipher()
        with self.assertRaises(RuntimeError):self.purchases.webhook(*self.event())
        with self.db.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM activation_codes').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM purchase_events').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT status FROM purchase_requests').fetchone()[0],'pending')


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'),'Dedicated PostgreSQL test database not configured')
class PostgreSQLPurchaseOnboardingTests(PurchaseOnboardingTests):
    storage=seat_fixture.PostgreSQLSeatLicensingTests.storage
