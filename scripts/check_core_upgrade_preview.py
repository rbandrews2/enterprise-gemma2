"""Non-persisted Stripe invoice preview; no customer/subscription/payment writes.

Uses the exact existing runtime secret binding in a private service snapshot.
The example address is synthetic (state/postcode only). Never prints credentials.
This is catalog/key/tax preview acceptance, not a paid subscription-transition test.
"""
import json
from pathlib import Path
import subprocess
import sys


def main():
    import stripe
    root = Path(sys.argv[1])
    service = json.loads((root / 'upgrade-current.json').read_text())
    container = service['spec']['template']['spec']['containers'][0]
    env = {item['name']: item for item in container['env']}
    ref = env['WZOS_STRIPE_API_KEY']['valueFrom']['secretKeyRef']
    assert ref['name'] == 'wzos-v2-stripe-api-keY'
    assert ref['key'].isdigit(), 'Require the existing pinned secret version'
    key = subprocess.check_output(['gcloud', 'secrets', 'versions', 'access', ref['key'],
        '--secret=' + ref['name'], '--project=enterprise-gemma2'], text=True).strip()
    assert key.startswith('rk_live_') and not any(c.isspace() for c in key)
    catalog = json.loads((root / 'source-final/knowledge/billing/v2-stripe-catalog.json').read_text())
    offer = catalog['offers']['enterprise']
    client = stripe.StripeClient(key, stripe_version='2026-08-26.dahlia',
        max_network_retries=0, http_client=stripe.RequestsClient(timeout=20))
    try:
        invoice = client.v1.invoices.create_preview({
            'currency': 'usd',
            'customer_details': {'address': {'country': 'US', 'state': 'VA', 'postal_code': '23219'}},
            'subscription_details': {'items': [{'price': offer['monthly_price_id'], 'quantity': 1}]},
            'invoice_items': [{'price': offer['setup_price_id'], 'quantity': 1}],
            'discounts': [{'coupon': catalog['core_upgrade_credit']['coupon_id']}],
            'automatic_tax': {'enabled': True},
        }).to_dict()
    except stripe.StripeError as exc:
        print('STRIPE_PREVIEW_FAILED', type(exc).__name__, 'http_status=', exc.http_status)
        return 1
    discount = sum(item['amount'] for item in invoice.get('total_discount_amounts', []))
    assert invoice['currency'] == 'usd' and invoice['livemode'] is True
    assert invoice['id'].startswith('upcoming_in_'), 'Expected non-persisted preview'
    assert discount == 2000, 'Approved one-time credit not reflected'
    assert invoice['automatic_tax']['status'] == 'complete', 'Tax preview incomplete'
    result = {'non_persisted_preview': True, 'customer_created': False,
        'subscription_modified': False, 'payment_attempted': False,
        'currency': invoice['currency'], 'total_cents': invoice['total'],
        'discount_cents': discount, 'automatic_tax_status': invoice['automatic_tax']['status']}
    with (root / 'upgrade-provider-preview.json').open('x', encoding='utf-8') as output:
        json.dump(result, output, indent=2)
    print('STRIPE_CATALOG_PREVIEW_PASS', json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
