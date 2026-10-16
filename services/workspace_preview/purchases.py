"""Local commerce foundation. Runtime integration remains disabled pending billing gates.

The provider must authenticate raw webhook signatures and retrieve authoritative
Checkout sessions. Browser success redirects and client metadata cannot fulfill.
Recurring lifecycle and production registration are separate release gates.
"""
import json
import secrets
from urllib.parse import urlsplit
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request
from .accounts import digest


@dataclass(frozen=True)
class Offer:
    id: str
    edition: str
    included_seats: int
    maximum_seats: int | None
    setup_cents: int
    monthly_cents: int
    additional_seat_monthly_cents: int
    setup_price_id: str
    monthly_price_id: str
    additional_seat_price_id: str

    def line_items(self, seats):
        if self.edition not in ('core','enterprise') or type(seats) is not int or not self.included_seats <= seats <= (self.maximum_seats or 100000):
            raise ValueError('Requested seats are outside this offer')
        ids=[self.setup_price_id,self.monthly_price_id,self.additional_seat_price_id]
        if any(not isinstance(p,str) or not p.startswith('price_') for p in ids) or len(set(ids))!=3:
            raise ValueError('Approved Stripe price mapping is not configured')
        items=[{'price':ids[0],'quantity':1},{'price':ids[1],'quantity':1}]
        extras=seats-self.included_seats
        if extras:items.append({'price':ids[2],'quantity':extras})
        return items

    def initial_amount(self, seats):
        return self.setup_cents+self.monthly_cents+(seats-self.included_seats)*self.additional_seat_monthly_cents


class Purchases:
    def __init__(self, accounts, provider, offers, cipher, *, livemode=False, require_automatic_tax=False, recurring_lifecycle=False):
        if livemode and not (recurring_lifecycle and require_automatic_tax):
            raise ValueError('Production commerce requires recurring lifecycle acceptance before enabling')
        if getattr(provider, 'livemode', livemode) is not livemode:
            raise ValueError('Provider mode does not match the commerce environment')
        self.accounts,self.provider,self.offers,self.cipher=accounts,provider,{o.id:o for o in offers},cipher
        self.livemode=livemode
        self.require_automatic_tax=require_automatic_tax
        self.single_purchase_identity=False
        with accounts.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS purchase_requests (id TEXT PRIMARY KEY,email TEXT NOT NULL,offer_id TEXT NOT NULL,edition TEXT NOT NULL CHECK(edition IN ('core','enterprise')),seats INTEGER NOT NULL CHECK(seats>0),expected_items TEXT NOT NULL,expected_cents INTEGER NOT NULL,session_id TEXT UNIQUE,status TEXT NOT NULL,activation_hash TEXT UNIQUE,sealed_code TEXT)")
            db.execute('CREATE TABLE IF NOT EXISTS purchase_events (event_id TEXT PRIMARY KEY,session_id TEXT NOT NULL,processed_at TEXT NOT NULL)')
        self.lifecycle = None
        if recurring_lifecycle:
            from .purchase_lifecycle import PurchaseLifecycle
            self.lifecycle = PurchaseLifecycle(self)
            accounts.licensing.billing_check = self.lifecycle.check_activation
            accounts.billing_check = self.lifecycle.check_organization

    def checkout(self, request_id, email, offer_id, seats):
        from uuid import UUID
        UUID(request_id)
        email=email.strip().lower()
        self.accounts.licensing.validate(seats,email)
        offer=self.offers.get(offer_id)
        if not offer:raise ValueError('Unknown offer')
        items=offer.line_items(seats);encoded=json.dumps(items,sort_keys=True)
        with self.accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            previous=db.execute('SELECT * FROM purchase_requests WHERE id=?',(request_id,)).fetchone()
            if not previous and self.single_purchase_identity:
                previous=db.execute('SELECT * FROM purchase_requests WHERE email=? ORDER BY id LIMIT 1',(email,)).fetchone()
                if previous:
                    request_id=previous['id']
            if previous:
                if (previous['email'],previous['offer_id'],previous['seats'],previous['expected_items'])!=(email,offer_id,seats,encoded):
                    raise HTTPException(409,'Checkout retry differs from its original request')
            else:
                db.execute('INSERT INTO purchase_requests VALUES (?,?,?,?,?,?,?,NULL,?,NULL,NULL)',(request_id,email,offer_id,offer.edition,seats,encoded,offer.initial_amount(seats),'pending'))
        # Provider idempotency key must be request_id. Network work is outside DB locks.
        result=(self.provider.retrieve_session(previous['session_id']) if previous and previous['session_id'] else self.provider.create_session(request_id,email,items))
        if not isinstance(result.get('id'),str) or not result['id'].startswith('cs_'):
            raise ValueError('Provider returned invalid checkout session')
        url=result.get('url')
        if url:
            parsed=urlsplit(url)
            if parsed.scheme!='https' or parsed.hostname not in ('checkout.stripe.com','checkout.superiorllc.org') or parsed.username or parsed.password or parsed.port not in (None,443):
                raise ValueError('Unexpected checkout destination')
        with self.accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current=db.execute('SELECT session_id FROM purchase_requests WHERE id=?',(request_id,)).fetchone()
            if current['session_id'] not in (None,result['id']):raise HTTPException(409,'Provider session mismatch')
            db.execute('UPDATE purchase_requests SET session_id=? WHERE id=?',(result['id'],request_id))
        return {'session_id':result['id'],'checkout_url':url,'status':previous['status'] if previous else 'pending'}

    def webhook(self, raw_body, signature):
        if len(raw_body)>1024*1024 or not signature or len(signature)>8192:raise ValueError('Invalid webhook envelope')
        event=self.provider.verify_event(raw_body,signature)
        if event.get('livemode') is not self.livemode:raise ValueError('Unexpected payment mode')
        if not isinstance(event.get('id'),str) or not event['id'].startswith('evt_'):raise ValueError('Invalid event identifier')
        kind=event.get('type')
        if self.lifecycle and kind in self.lifecycle.events:
            return self.lifecycle.handle(event)
        if kind not in ('checkout.session.completed','checkout.session.async_payment_succeeded','checkout.session.async_payment_failed'):
            return {'ignored':True}
        session_id=event['data']['object']['id']
        if not isinstance(event.get('id'),str) or not event['id'].startswith('evt_'):raise ValueError('Invalid event identifier')
        session=self.provider.retrieve_session(session_id)
        if session.get('id')!=session_id or session.get('livemode') is not self.livemode:raise ValueError('Session identity/mode mismatch')
        if session.get('payment_status')!='paid':
            return {'pending':True,'activation_issued':False}
        billing = None
        if self.lifecycle:
            with self.accounts.connect() as db:
                pending = db.execute('SELECT * FROM purchase_requests WHERE session_id=?', (session_id,)).fetchone()
                if not pending:raise ValueError('Unrecognized checkout session')
                duplicate = db.execute('SELECT session_id FROM purchase_events WHERE event_id=?', (event['id'],)).fetchone()
                if duplicate:
                    if duplicate['session_id'] != session_id:raise ValueError('Event identity mismatch')
                    return {'duplicate':True,'fulfilled':pending['status']=='fulfilled'}
            billing = self.lifecycle.initial(session, pending)
        with self.accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM purchase_requests WHERE session_id=?',(session_id,)).fetchone()
            if not row:raise ValueError('Unrecognized checkout session')
            prior=db.execute('SELECT session_id FROM purchase_events WHERE event_id=?',(event['id'],)).fetchone()
            if prior:
                if prior['session_id']!=session_id:raise ValueError('Event identity mismatch')
                return {'fulfilled':row['status']=='fulfilled','duplicate':True}
            expected=json.loads(row['expected_items'])
            received=[{'price':i['price']['id'],'quantity':i['quantity']} for i in session.get('line_items',{}).get('data',[])]
            if session.get('line_items',{}).get('has_more') or sorted(received,key=lambda i:i['price'])!=sorted(expected,key=lambda i:i['price']):
                raise ValueError('Paid line items do not match the approved purchase')
            if session.get('status')!='complete' or session.get('mode')!='subscription' or session.get('currency')!='usd':
                raise ValueError('Paid amount/session mismatch')
            if self.require_automatic_tax:
                tax=session.get('automatic_tax',{}); totals=session.get('total_details',{})
                tax_cents=totals.get('amount_tax')
                if (tax.get('enabled') is not True or tax.get('status')!='complete'
                        or type(tax_cents) is not int or tax_cents<0
                        or type(session.get('amount_subtotal')) is not int
                        or session['amount_subtotal']!=row['expected_cents']
                        or totals.get('amount_discount')!=0 or totals.get('amount_shipping')!=0
                        or type(session.get('amount_total')) is not int
                        or session['amount_total']!=row['expected_cents']+tax_cents):
                    raise ValueError('Paid tax calculation or subtotal mismatch')
            elif session.get('amount_total')!=row['expected_cents']:
                raise ValueError('Paid amount/session mismatch')
            if session.get('customer_details',{}).get('email','').lower()!=row['email']:
                raise ValueError('Purchasing identity mismatch')
            if row['status']!='fulfilled':
                code=secrets.token_urlsafe(32);hash_=digest(code)
                # Seal before persistence. Failure rolls back the entire fulfillment.
                sealed=self.cipher.encrypt(code.encode()).decode()
                edition=row['edition']
                expiry=(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()
                db.execute('INSERT INTO activation_codes VALUES (?,?,?,?,?)',(hash_,edition,expiry,None,None))
                self.accounts.licensing.attach_activation(db,hash_,row['seats'],row['email'])
                db.execute('UPDATE purchase_requests SET status=?,activation_hash=?,sealed_code=? WHERE id=?',('fulfilled',hash_,sealed,row['id']))
                if billing:
                    db.execute('INSERT INTO purchase_subscriptions VALUES (?,?,?,?,?,1)', (row['id'],*billing))
            db.execute('INSERT INTO purchase_events VALUES (?,?,?)',(event['id'],session_id,datetime.now(timezone.utc).isoformat()))
        return {'fulfilled':True,'activation_issued':True}

    def receipt(self, session_id, verified_identity):
        with self.accounts.connect() as db:
            row=db.execute('SELECT * FROM purchase_requests WHERE session_id=? AND email=?',(session_id,verified_identity['email'])).fetchone()
        if not row:raise HTTPException(404,'Purchase unavailable for this verified account')
        result={'status':row['status'],'seats':row['seats'],'edition':row['edition']}
        if row['status']=='fulfilled':
            if self.lifecycle:
                with self.accounts.connect() as db:
                    self.lifecycle.check_activation(db,row['activation_hash'])
            result['activation_code']=self.cipher.decrypt(row['sealed_code'].encode()).decode()
        return result

    def register_private_receipts(self, app):
        @app.get('/api/account/purchases/{session_id}')
        def purchase_receipt(session_id: str, request: Request):
            # Verify Google identity/email before reading any purchase/delivery data.
            return self.receipt(session_id, self.accounts.identity(request))


class StripeProvider:
    """SDK adapter; caller supplies only server-owned prices and secrets."""
    def __init__(self, restricted_key, webhook_secret, *, livemode=False,
                 automatic_tax=False, tax_configuration_verified=False):
        from stripe import StripeClient, RequestsClient
        prefix='rk_live_' if livemode else 'rk_test_'
        if (not isinstance(restricted_key,str) or not restricted_key.startswith(prefix)
                or len(restricted_key)>512 or any(c.isspace() for c in restricted_key)):
            raise ValueError('A restricted Stripe key matching the environment is required')
        if not isinstance(webhook_secret,str) or not webhook_secret.startswith('whsec_') or any(c.isspace() for c in webhook_secret):
            raise ValueError('Stripe webhook signing configuration is required')
        if automatic_tax and not tax_configuration_verified:
            raise ValueError('Verify tax registration and product classification before automatic tax')
        self.livemode,self.automatic_tax=livemode,automatic_tax
        self.client=StripeClient(restricted_key,stripe_version='2026-08-26.dahlia',
                                 max_network_retries=0,http_client=RequestsClient(timeout=15))
        self.webhook_secret=webhook_secret

    def create_session(self, request_id, email, line_items):
        suffix=''.join(chr(97+int(c,16)) for c in request_id.replace('-','')[:8])
        parameters={
            'mode':'subscription','customer_email':email,'line_items':line_items,
            'client_reference_id':request_id,
            'success_url':'https://app.workzoneos.org/?purchase={CHECKOUT_SESSION_ID}',
            'cancel_url':'https://workzoneos.org/#purchase',
            'integration_identifier':'wzos_checkout_'+suffix,
        }
        if self.automatic_tax:parameters['automatic_tax']={'enabled':True}
        result=self.client.v1.checkout.sessions.create(parameters,options={'idempotency_key':'wzos-checkout-'+request_id})
        return result.to_dict()

    def retrieve_session(self, session_id):
        return self.client.v1.checkout.sessions.retrieve(session_id,{'expand':['line_items']}).to_dict()

    def retrieve_subscription(self, subscription_id):
        return self.client.v1.subscriptions.retrieve(subscription_id,{'expand':['latest_invoice']}).to_dict()

    def verify_event(self, raw_body, signature):
        from stripe import Webhook, SignatureVerificationError
        try:
            return Webhook.construct_event(raw_body,signature,self.webhook_secret,tolerance=300).to_dict()
        except SignatureVerificationError as exc:
            raise ValueError('Invalid webhook signature') from exc
