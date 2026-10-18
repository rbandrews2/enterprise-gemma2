"""Paid, organization-scoped Core upgrades on the existing Stripe subscription.

Provider writes occur only after an explicit admin confirmation. No second
subscription, browser-owned entitlements, or payment-success redirect fulfillment.
"""
import json
import time
from uuid import uuid4
from urllib.parse import urlsplit

from fastapi import HTTPException

from .purchase_lifecycle import resource_id


DDL = '''CREATE TABLE IF NOT EXISTS organization_upgrades (
organization_id TEXT PRIMARY KEY,request_id TEXT NOT NULL UNIQUE,
purchase_request_id TEXT NOT NULL,subscription_id TEXT NOT NULL UNIQUE,
customer_id TEXT NOT NULL,seats INTEGER NOT NULL,status TEXT NOT NULL,
payload TEXT NOT NULL,created_at INTEGER NOT NULL)'''


def recurring(offer, seats):
    return [item for item in offer.line_items(seats) if item['price'] != offer.setup_price_id]


def item_set(sub):
    items = sub.get('items', {})
    if items.get('has_more'):
        raise ValueError('Subscription item review required')
    return sorted([{'price': resource_id(i.get('price')), 'quantity': i.get('quantity')}
                   for i in items.get('data', [])], key=lambda i: i['price'])


class SubscriptionUpgrades:
    def __init__(self, purchases, coupon_id):
        self.purchases, self.accounts, self.provider = purchases, purchases.accounts, purchases.provider
        self.coupon_id = coupon_id
        with self.accounts.connect() as db:
            db.execute(DDL)

    def actor(self, request):
        user = self.accounts.actor(request)
        if user['role'] != 'admin':
            raise HTTPException(403, 'Organization administrator access required')
        return user

    def owned(self, db, user):
        row = db.execute('''SELECT p.*,s.subscription_id,s.customer_id,
            s.version AS billing_version,s.access_enabled,e.seat_limit
            FROM organization_entitlements e
            JOIN purchase_requests p ON p.activation_hash=e.activation_hash
            JOIN purchase_subscriptions s ON s.request_id=p.id
            WHERE e.organization_id=?''', (user['organization_id'],)).fetchone()
        if not row or row['edition'] != 'core' or not row['access_enabled']:
            raise HTTPException(409, 'This organization needs a verified paid Core subscription before an online upgrade. Contact WZOS billing support.')
        return dict(row)

    def status(self, user):
        with self.accounts.connect() as db:
            row = db.execute('SELECT * FROM organization_upgrades WHERE organization_id=?',
                             (user['organization_id'],)).fetchone()
        if row:
            payload = json.loads(row['payload'])
            return {'status': row['status'], 'seats': row['seats'],
                    'request_id': row['request_id'], 'payment_url': payload.get('payment_url'),
                    'quote': payload.get('quote')}
        return {'status': 'available' if user['edition'] == 'core' else 'not_applicable'}

    def quote(self, user, seats):
        if user['edition'] != 'core':
            raise HTTPException(409, 'Only Core organizations can use this upgrade')
        target = self.purchases.offers['enterprise']
        target.line_items(seats)
        stamp = int(time.time())
        with self.accounts.connect() as db:
            owned = self.owned(db, user)
            used = self.accounts.licensing.status(db, user['organization_id'])['seats_used']
            prior = db.execute('SELECT * FROM organization_upgrades WHERE organization_id=?',
                               (user['organization_id'],)).fetchone()
        if seats < max(target.included_seats, used, owned['seat_limit']):
            raise HTTPException(409, 'Keep at least the existing purchased and active login allowance')
        if prior and prior['status'] != 'quoted':
            return self.status(user)
        core = self.purchases.offers['core']
        sub = self.provider.retrieve_subscription(owned['subscription_id'])
        expected = recurring(core, owned['seats'])
        invoice = sub.get('latest_invoice') or {}
        if (sub.get('id') != owned['subscription_id'] or sub.get('livemode') is not self.purchases.livemode
                or resource_id(sub.get('customer')) != owned['customer_id']
                or sub.get('status') != 'active' or sub.get('collection_method') != 'charge_automatically'
                or sub.get('pending_update') or sub.get('schedule') or sub.get('cancel_at_period_end')
                or sub.get('cancel_at') or sub.get('pause_collection') or sub.get('discounts')
                or item_set(sub) != sorted(expected, key=lambda i: i['price'])
                or not isinstance(invoice, dict) or invoice.get('status') != 'paid' or invoice.get('paid') is not True):
            raise HTTPException(409, 'Settle or review the existing subscription before upgrading')
        if self.purchases.require_automatic_tax and sub.get('automatic_tax', {}).get('enabled') is not True:
            raise HTTPException(409, 'Subscription tax configuration requires billing review')
        items = sub['items']['data']
        if any(not isinstance(i.get('id'), str) or not i['id'].startswith('si_') for i in items):
            raise ValueError('Subscription item identity required')
        request_id = str(uuid4())
        changes = []
        for item in items:
            if resource_id(item['price']) == core.monthly_price_id:
                changes.append({'id': item['id'], 'price': target.monthly_price_id, 'quantity': 1})
            else:
                changes.append({'id': item['id'], 'deleted': True})
        if seats > target.included_seats:
            changes.append({'price': target.additional_seat_price_id, 'quantity': seats-target.included_seats})
        params = {'items': changes, 'add_invoice_items': [{'price': target.setup_price_id, 'quantity': 1}],
                  'discounts': [{'coupon': self.coupon_id}], 'proration_date': stamp,
                  'proration_behavior': 'always_invoice', 'payment_behavior': 'pending_if_incomplete',
                  'metadata': {'wzos_upgrade_request': request_id}}
        preview = self.provider.preview_upgrade(owned['subscription_id'], owned['customer_id'], params)
        if (preview.get('currency') != 'usd' or type(preview.get('amount_due')) is not int
                or preview['amount_due'] < 0
                or sum(d['amount'] for d in preview.get('total_discount_amounts', [])) != 2000):
            raise ValueError('Upgrade amount/credit requires review')
        if self.purchases.require_automatic_tax and preview.get('automatic_tax', {}).get('status') != 'complete':
            raise ValueError('Upgrade tax calculation incomplete')
        quote = {'amount_due_cents': preview['amount_due'], 'currency': 'usd', 'credit_cents': 2000,
                 'setup_cents': target.setup_cents, 'monthly_cents': target.monthly_cents +
                 (seats-target.included_seats)*target.additional_seat_monthly_cents,
                 'seats': seats, 'expires_at': stamp+600, 'proration_date': stamp}
        period_end = min(int(i.get('current_period_end', 0)) for i in items)
        if period_end <= stamp:
            raise ValueError('Current paid service period is required')
        payload = {'parameters': params, 'quote': quote, 'old_invoice': invoice['id'],
                   'old_period_end': period_end, 'expected_items': recurring(target, seats),
                   'billing_version': owned['billing_version']}
        with self.accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            latest = self.owned(db, user)
            if latest['billing_version'] != owned['billing_version']:
                raise HTTPException(409, 'Billing changed; request a fresh estimate')
            current = db.execute('SELECT status FROM organization_upgrades WHERE organization_id=?',
                                 (user['organization_id'],)).fetchone()
            if current and current['status'] != 'quoted':
                raise HTTPException(409, 'An upgrade is already in progress')
            db.execute('''INSERT INTO organization_upgrades VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(organization_id) DO UPDATE SET request_id=excluded.request_id,
                seats=excluded.seats,status=excluded.status,payload=excluded.payload,created_at=excluded.created_at''',
                (user['organization_id'], request_id, owned['id'], owned['subscription_id'],
                 owned['customer_id'], seats, 'quoted', json.dumps(payload), stamp))
        return {'status': 'quoted', 'request_id': request_id, 'quote': quote}

    def confirm(self, user, request_id):
        with self.accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM organization_upgrades WHERE organization_id=? AND request_id=?',
                             (user['organization_id'], request_id)).fetchone()
            if not row:
                raise HTTPException(409, 'Request a fresh upgrade estimate')
            if row['status'] in ('applied', 'pending'):
                return self.status(user)
            owned = self.owned(db, user)
            payload = json.loads(row['payload'])
            stamp = int(time.time())
            if (row['status'] == 'quoted' and
                    (payload['quote']['expires_at'] <= stamp or owned['billing_version'] != payload['billing_version'])):
                raise HTTPException(409, 'Estimate expired or billing changed; request a fresh estimate')
            if stamp-row['created_at'] >= 23*3600:
                raise HTTPException(409, 'This upgrade needs billing review before another payment attempt')
            if row['status'] not in ('quoted', 'submitting'):
                raise HTTPException(409, 'This upgrade needs billing review')
            db.execute('UPDATE organization_upgrades SET status=? WHERE organization_id=?',
                       ('submitting', user['organization_id']))
        # An ambiguous network failure keeps submitting and the SAME idempotency key.
        sub = self.provider.update_subscription(row['subscription_id'], payload['parameters'], request_id)
        if (sub.get('id') != row['subscription_id'] or resource_id(sub.get('customer')) != row['customer_id']
                or sub.get('livemode') is not self.purchases.livemode):
            raise ValueError('Upgrade subscription ownership mismatch')
        invoice = sub.get('latest_invoice') or {}
        if not isinstance(invoice, dict) or not str(invoice.get('id', '')).startswith('in_'):
            raise ValueError('Upgrade invoice confirmation required')
        url = invoice.get('hosted_invoice_url')
        if url:
            parsed = urlsplit(url)
            if (parsed.scheme != 'https' or parsed.hostname != 'invoice.stripe.com' or parsed.username
                    or parsed.password or parsed.port not in (None, 443)):
                raise ValueError('Unexpected invoice destination')
        with self.accounts.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current = db.execute('SELECT status,payload FROM organization_upgrades WHERE organization_id=? AND request_id=?',
                                 (user['organization_id'], request_id)).fetchone()
            if current['status'] != 'applied':
                data = json.loads(current['payload']);data.update(invoice_id=invoice['id'], payment_url=url)
                db.execute('UPDATE organization_upgrades SET status=?,payload=? WHERE organization_id=?',
                           ('pending', json.dumps(data), user['organization_id']))
        # Only a verified webhook grants Enterprise; an HTTP success is not payment.
        return self.status(user)

    def observation(self, sub, expected):
        """Prepare a grant for the lifecycle transaction, or preserve paid Core only."""
        with self.accounts.connect() as db:
            row = db.execute('SELECT * FROM organization_upgrades WHERE subscription_id=?', (sub['id'],)).fetchone()
        if not row or row['status'] == 'quoted':
            return expected, False, None
        data = json.loads(row['payload'])
        if resource_id(sub.get('customer')) != row['customer_id']:
            raise ValueError('Upgrade customer mismatch')
        if row['status'] == 'applied':
            return data['expected_items'], False, None
        invoice = sub.get('latest_invoice') or {}
        marker = sub.get('metadata', {}).get('wzos_upgrade_request')
        pending = sub.get('pending_update') or {}
        lines = invoice.get('lines', {}) if isinstance(invoice, dict) else {}
        setup_price = self.purchases.offers['enterprise'].setup_price_id
        setup_present = not lines.get('has_more') and any(
            (resource_id(line.get('price')) or line.get('pricing', {}).get('price_details', {}).get('price')) == setup_price
            and line.get('quantity') == 1 for line in lines.get('data', []))
        if (marker == row['request_id'] and not pending and sub.get('status') == 'active'
                and item_set(sub) == sorted(data['expected_items'], key=lambda i: i['price'])
                and isinstance(invoice, dict) and invoice.get('status') == 'paid' and invoice.get('paid') is True
                and invoice.get('currency') == 'usd' and invoice.get('livemode') is self.purchases.livemode
                and resource_id(invoice.get('customer')) == row['customer_id'] and setup_present
                and invoice.get('billing_reason') == 'subscription_update'
                and invoice.get('id') != data['old_invoice']
                and resource_id(invoice.get('parent', {}).get('subscription_details', {}).get('subscription')) == sub['id']
                and sum(d['amount'] for d in invoice.get('total_discount_amounts', [])) == 2000):
            if data.get('invoice_id') and invoice['id'] != data['invoice_id']:
                raise ValueError('Paid upgrade invoice mismatch')
            return data['expected_items'], False, dict(row)
        pending_ours = pending.get('metadata', {}).get('wzos_upgrade_request') == row['request_id']
        expired_ours = (not pending and data.get('invoice_id') == invoice.get('id')
                        and invoice.get('status') == 'void') if isinstance(invoice, dict) else False
        keep_core = (sub.get('status') == 'active' and data['old_period_end'] > time.time()
                     and isinstance(invoice, dict) and (pending_ours or expired_ours)
                     and invoice.get('status') in ('open', 'void')
                     and (not data.get('invoice_id') or invoice.get('id') == data['invoice_id']))
        expired = {**dict(row), 'transition': 'expired'} if expired_ours and row['status'] in ('submitting', 'pending') else None
        return expected, bool(keep_core), expired

    def apply(self, db, row):
        if not row:
            return
        current = db.execute('SELECT status,request_id FROM organization_upgrades WHERE organization_id=?',
                             (row['organization_id'],)).fetchone()
        if current['request_id'] != row['request_id'] or current['status'] not in ('submitting', 'pending'):
            raise HTTPException(409, 'Concurrent upgrade reconciliation; retry delivery')
        if row.get('transition') == 'expired':
            db.execute('UPDATE organization_upgrades SET status=? WHERE organization_id=?', ('review_required', row['organization_id']))
            self.accounts.audit(db, row['organization_id'], 'stripe', 'enterprise_upgrade_expired', row['request_id'])
            return
        used = self.accounts.licensing.status(db, row['organization_id'])['seats_used']
        if used > row['seats']:
            raise ValueError('Active seats exceed paid upgrade')
        db.execute('UPDATE organizations SET edition=? WHERE id=?', ('enterprise', row['organization_id']))
        db.execute('UPDATE organization_entitlements SET seat_limit=? WHERE organization_id=?', (row['seats'], row['organization_id']))
        db.execute('UPDATE organization_upgrades SET status=? WHERE organization_id=?', ('applied', row['organization_id']))
        self.accounts.audit(db, row['organization_id'], 'stripe', 'enterprise_upgrade_paid', row['request_id'])
