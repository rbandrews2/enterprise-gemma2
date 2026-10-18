"""Authoritative recurring state for purchases owned by this application."""
from fastapi import HTTPException

DDL = '''CREATE TABLE IF NOT EXISTS purchase_subscriptions (
request_id TEXT PRIMARY KEY,subscription_id TEXT NOT NULL UNIQUE,
customer_id TEXT NOT NULL,status TEXT NOT NULL,
access_enabled INTEGER NOT NULL CHECK(access_enabled IN (0,1)),version INTEGER NOT NULL)'''


def resource_id(value):
    return value.get('id') if isinstance(value, dict) else value


class PurchaseLifecycle:
    events = {'invoice.paid', 'invoice.payment_failed', 'customer.subscription.created',
              'customer.subscription.updated', 'customer.subscription.deleted'}

    def __init__(self, purchases):
        self.purchases = purchases
        with purchases.accounts.connect() as db:
            db.execute(DDL)

    def inspect(self, subscription_id, customer_id, expected):
        if not isinstance(subscription_id, str) or not subscription_id.startswith('sub_'):
            raise ValueError('Subscription identity required')
        sub = self.purchases.provider.retrieve_subscription(subscription_id)
        if (sub.get('id') != subscription_id or sub.get('livemode') is not self.purchases.livemode
                or resource_id(sub.get('customer')) != customer_id
                or not isinstance(customer_id, str) or not customer_id.startswith('cus_')):
            raise ValueError('Subscription ownership mismatch')
        upgrade, keep_core = None, False
        upgrades = getattr(self.purchases, 'upgrades', None)
        if upgrades:
            expected, keep_core, upgrade = upgrades.observation(sub, expected)
        items = sub.get('items', {})
        actual = [{'price': item['price']['id'], 'quantity': item['quantity']}
                  for item in items.get('data', [])]
        matching = not items.get('has_more') and sorted(actual, key=lambda x:x['price']) == sorted(expected, key=lambda x:x['price'])
        invoice = sub.get('latest_invoice')
        paid = isinstance(invoice, dict) and invoice.get('status') == 'paid' and invoice.get('paid') is True
        status = str(sub.get('status', 'unknown'))[:40] if matching else 'price_review_required'
        access = int(matching and status == 'active' and (paid or keep_core))
        if access and keep_core and not paid:
            status = 'upgrade_pending_core'
        return status, access, upgrade

    def observe(self, subscription_id, customer_id, expected):
        status, access, _ = self.inspect(subscription_id, customer_id, expected)
        return status, access

    def initial(self, session, request):
        import json
        offer = self.purchases.offers[request['offer_id']]
        expected = [item for item in json.loads(request['expected_items']) if item['price'] != offer.setup_price_id]
        sub_id, customer = resource_id(session.get('subscription')), resource_id(session.get('customer'))
        status, access = self.observe(sub_id, customer, expected)
        if not access:
            raise ValueError('An active paid subscription is required before activation')
        return sub_id, customer, status, access

    def handle(self, event):
        import json
        obj = event['data']['object']
        if event['type'].startswith('invoice.'):
            # Current API invoices link the subscription through parent details.
            sub_id = resource_id(obj.get('parent', {}).get('subscription_details', {}).get('subscription'))
        else:
            sub_id = obj.get('id')
        with self.purchases.accounts.connect() as db:
            row = db.execute('SELECT * FROM purchase_subscriptions WHERE subscription_id=?', (sub_id,)).fetchone()
            if not row:
                return {'ignored': True}
            if db.execute('SELECT event_id FROM purchase_events WHERE event_id=?', (event['id'],)).fetchone():
                return {'duplicate': True}
            request = db.execute('SELECT * FROM purchase_requests WHERE id=?', (row['request_id'],)).fetchone()
        offer = self.purchases.offers[request['offer_id']]
        expected = [item for item in json.loads(request['expected_items']) if item['price'] != offer.setup_price_id]
        status, access, upgrade = self.inspect(sub_id, row['customer_id'], expected)
        with self.purchases.accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT event_id FROM purchase_events WHERE event_id=?', (event['id'],)).fetchone():
                return {'duplicate': True}
            current = db.execute('SELECT version FROM purchase_subscriptions WHERE subscription_id=?', (sub_id,)).fetchone()
            if current['version'] != row['version']:
                raise HTTPException(409, 'Concurrent billing update; retry delivery')
            if upgrade:
                self.purchases.upgrades.apply(db, upgrade)
            db.execute('UPDATE purchase_subscriptions SET status=?,access_enabled=?,version=version+1 WHERE subscription_id=?', (status, access, sub_id))
            from .accounts import now
            db.execute('INSERT INTO purchase_events VALUES (?,?,?)', (event['id'], request['session_id'], now()))
        return {'billing_updated': True}

    @staticmethod
    def check_activation(db, activation_hash):
        row = db.execute('SELECT s.access_enabled,s.status,s.request_id FROM purchase_subscriptions s JOIN purchase_requests p ON p.id=s.request_id WHERE p.activation_hash=?', (activation_hash,)).fetchone()
        if row and not row['access_enabled']:
            raise HTTPException(403, 'Your subscription needs attention. Contact WZOS support.')
        if row and row['status'] == 'upgrade_pending_core':
            import json
            import time
            upgrade = db.execute('SELECT payload FROM organization_upgrades WHERE purchase_request_id=?', (row['request_id'],)).fetchone()
            if not upgrade or json.loads(upgrade['payload'])['old_period_end'] <= time.time():
                raise HTTPException(403, 'Your paid Core period has ended. Contact WZOS billing support.')

    def check_organization(self, db, organization):
        grant = db.execute('SELECT activation_hash FROM organization_entitlements WHERE organization_id=?', (organization,)).fetchone()
        if grant:
            self.check_activation(db, grant['activation_hash'])
