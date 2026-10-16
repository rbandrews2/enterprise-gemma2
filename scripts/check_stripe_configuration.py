"""Read-only Stripe catalog/tax preflight. Never creates sessions or payments.

The approved tax code must be chosen by the operator after classification review.
This verifies configured registrations, not legal taxability or a tax calculation.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def inspect_catalog(client, catalog, approved_tax_code):
    if not approved_tax_code.startswith('txcd_'):
        raise ValueError('An explicitly approved product tax code is required')
    count=0
    for offer in catalog['offers'].values():
        for kind in ('setup','monthly','additional_seat'):
            price_id=offer[kind+'_price_id']
            price=client.v1.prices.retrieve(price_id,{'expand':['product']}).to_dict()
            product=price.get('product',{})
            amount=offer[{'setup':'setup_cents','monthly':'monthly_cents',
                          'additional_seat':'additional_seat_monthly_cents'}[kind]]
            if (price.get('id')!=price_id or price.get('active') is not True
                    or price.get('livemode') is not catalog['livemode']
                    or price.get('currency')!='usd' or type(price.get('unit_amount')) is not int
                    or price['unit_amount']!=amount or not isinstance(product,dict)
                    or product.get('id')!=offer['product_id'] or product.get('active') is not True):
                raise ValueError('Stripe catalog does not match the approved edition mapping')
            recurring=price.get('recurring')
            if kind=='setup':
                if recurring is not None:raise ValueError('Setup must be a one-time price')
            elif not recurring or recurring.get('interval')!='month' or recurring.get('interval_count')!=1:
                raise ValueError('Recurring prices must bill monthly')
            tax_code=product.get('tax_code')
            if isinstance(tax_code,dict):tax_code=tax_code.get('id')
            if tax_code!=approved_tax_code:
                raise ValueError('Product tax classification has not been applied and verified')
            if price.get('tax_behavior')!='exclusive':
                raise ValueError('Price tax behavior requires explicit review')
            count+=1
    credit=catalog['core_upgrade_credit']
    coupon=client.v1.coupons.retrieve(credit['coupon_id'],{'expand':['applies_to']}).to_dict()
    if (coupon.get('id')!=credit['coupon_id'] or coupon.get('valid') is not True
            or coupon.get('livemode') is not catalog['livemode']
            or coupon.get('currency')!='usd' or coupon.get('amount_off')!=2000
            or coupon.get('duration')!='once' or coupon.get('percent_off') is not None
            or coupon.get('applies_to',{}).get('products')!=[credit['applies_to_product_id']]):
        raise ValueError('Upgrade credit does not match the approved once-only edition restriction')
    registrations=client.v1.tax.registrations.list({'status':'active','limit':100}).to_dict()
    if registrations.get('has_more'):raise ValueError('Registration list requires a bounded pagination review')
    virginia=any(row.get('status')=='active' and row.get('country')=='US'
                 and row.get('country_options',{}).get('us',{}).get('state')=='VA'
                 for row in registrations.get('data',[]))
    if not virginia:raise ValueError('No active Virginia Stripe Tax registration was verified')
    return {'prices_verified':count,'upgrade_coupon_verified':True,'virginia_registration_active':True,
            'product_tax_code':approved_tax_code,'tax_calculation_tested':False,
            'checkout_enabled':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approved-tax-code',required=True)
    parser.add_argument('--live',action='store_true',help='Explicitly read the live catalog')
    args=parser.parse_args()
    catalog=json.loads((ROOT/'knowledge/billing/v2-stripe-catalog.json').read_text())
    key=os.getenv('WZOS_STRIPE_API_KEY','')
    if args.live is not catalog['livemode'] or not key.startswith('rk_live_' if args.live else 'rk_test_'):
        print('Stripe preflight blocked: explicit catalog mode and matching restricted key required.',file=sys.stderr)
        return 2
    try:
        from stripe import StripeClient, RequestsClient
        client=StripeClient(key,stripe_version='2026-08-26.dahlia',max_network_retries=0,
                            http_client=RequestsClient(timeout=15))
        result=inspect_catalog(client,catalog,args.approved_tax_code)
    except ValueError as exc:
        print('Stripe preflight blocked: '+str(exc),file=sys.stderr)
        return 1
    except Exception:
        # SDK exceptions can contain request data; never echo them to shell logs.
        print('Stripe preflight unavailable. Check restricted permissions and configuration privately.',file=sys.stderr)
        return 1
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=='__main__':raise SystemExit(main())
