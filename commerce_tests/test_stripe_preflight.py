"""A read-only preflight must reject mismatched prices, coupons and registrations."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('stripe_preflight',ROOT/'scripts/check_stripe_configuration.py')
preflight=importlib.util.module_from_spec(spec);spec.loader.exec_module(preflight)


class Result(dict):
    def to_dict(self):return copy.deepcopy(self)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.catalog=json.loads((ROOT/'knowledge/billing/v2-stripe-catalog.json').read_text())
        self.prices={};self.reads=[]
        for offer in self.catalog['offers'].values():
            for kind,field in [('setup','setup_cents'),('monthly','monthly_cents'),('additional_seat','additional_seat_monthly_cents')]:
                id_=offer[kind+'_price_id']
                self.prices[id_]=Result(id=id_,active=True,livemode=True,currency='usd',unit_amount=offer[field],tax_behavior='exclusive',
                    product={'id':offer['product_id'],'active':True,'tax_code':'txcd_10103001'},
                    recurring=None if kind=='setup' else {'interval':'month','interval_count':1})
        credit=self.catalog['core_upgrade_credit']
        self.coupon=Result(id=credit['coupon_id'],valid=True,livemode=True,currency='usd',amount_off=2000,duration='once',percent_off=None,
                           applies_to={'products':[credit['applies_to_product_id']]})
        self.registrations=Result(has_more=False,data=[{'country':'US','status':'active','country_options':{'us':{'state':'VA'}}}])
        def price(id_,options):self.reads.append(id_);return self.prices[id_]
        self.client=SimpleNamespace(v1=SimpleNamespace(prices=SimpleNamespace(retrieve=price),
            coupons=SimpleNamespace(retrieve=lambda id_:self.coupon),
            tax=SimpleNamespace(registrations=SimpleNamespace(list=lambda options:self.registrations))))

    def test_valid_preflight_is_read_only_and_does_not_claim_a_tax_calculation(self):
        result=preflight.inspect_catalog(self.client,self.catalog,'txcd_10103001')
        self.assertEqual(len(self.reads),6)
        self.assertTrue(result['virginia_registration_active'])
        self.assertFalse(result['tax_calculation_tested'])
        self.assertFalse(result['checkout_enabled'])

    def test_wrong_environment_classification_amount_interval_and_credit_fail(self):
        first=next(iter(self.prices))
        for field,value in [('livemode',False),('unit_amount',1),('recurring',{'interval':'month','interval_count':1}),('tax_behavior','inclusive')]:
            original=self.prices[first][field];self.prices[first][field]=value
            with self.assertRaises(ValueError):preflight.inspect_catalog(self.client,self.catalog,'txcd_10103001')
            self.prices[first][field]=original
        with self.assertRaises(ValueError):preflight.inspect_catalog(self.client,self.catalog,'txcd_10103101')
        self.coupon['duration']='forever'
        with self.assertRaises(ValueError):preflight.inspect_catalog(self.client,self.catalog,'txcd_10103001')

    def test_inactive_missing_wrong_state_and_incomplete_registration_lists_fail(self):
        for data in [[],[{'country':'US','status':'pending','country_options':{'us':{'state':'VA'}}}],
                     [{'country':'US','status':'active','country_options':{'us':{'state':'MD'}}}]]:
            self.registrations['data']=data
            with self.assertRaises(ValueError):preflight.inspect_catalog(self.client,self.catalog,'txcd_10103001')
        self.registrations['has_more']=True
        with self.assertRaises(ValueError):preflight.inspect_catalog(self.client,self.catalog,'txcd_10103001')


if __name__=='__main__':unittest.main()
