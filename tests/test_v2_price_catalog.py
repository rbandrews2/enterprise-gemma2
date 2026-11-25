"""Validate the saved Stripe mapping against the existing purchase contract."""
import json
import unittest
from pathlib import Path

from services.workspace_preview.purchases import Offer

CATALOG = Path(__file__).resolve().parents[1] / 'knowledge/billing/v2-stripe-catalog.json'


class V2PriceCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads(CATALOG.read_text(encoding='utf-8'))

    def offer(self, edition):
        record = {k: v for k, v in self.catalog['offers'][edition].items() if k != 'product_id'}
        return Offer(id='v2-' + edition, edition=edition, **record)

    def test_included_capacity_does_not_bill_seat_addons(self):
        for edition, seats, amount in [('core', 15, 15800), ('enterprise', 25, 124800)]:
            with self.subTest(edition=edition):
                offer = self.offer(edition)
                self.assertEqual(offer.initial_amount(seats), amount)
                self.assertEqual(len(offer.line_items(seats)), 2)
                self.assertTrue(all(row['quantity'] == 1 for row in offer.line_items(seats)))

    def test_additional_capacity_is_incremental_and_core_is_bounded(self):
        core = self.offer('core')
        self.assertEqual(core.line_items(30)[2]['quantity'], 15)
        self.assertEqual(core.initial_amount(30), 20300)
        for seats in [0, 14, 31, True, 15.5]:
            with self.assertRaises(ValueError):
                core.line_items(seats)
        enterprise = self.offer('enterprise')
        self.assertEqual(enterprise.line_items(30)[2]['quantity'], 5)
        self.assertEqual(enterprise.initial_amount(30), 128300)

    def test_catalog_preparation_cannot_enable_checkout_or_monthly_discount(self):
        self.assertFalse(self.catalog['checkout_enabled'])
        credit = self.catalog['core_upgrade_credit']
        self.assertEqual((credit['amount_cents'], credit['duration']), (2000, 'once'))
        self.assertEqual(credit['applies_to_product_id'], self.catalog['offers']['enterprise']['product_id'])
        self.assertTrue(credit['requires_admin'])
        self.assertTrue(credit['requires_verified_billing_eligibility'])
        offers = self.catalog['offers']
        self.assertEqual(set(offers), {'core', 'enterprise', 'core_annual', 'enterprise_annual'})
        setup_prices = set()
        recurring_prices = []
        for edition in ('core', 'enterprise'):
            monthly, annual = offers[edition], offers[edition + '_annual']
            self.assertEqual(monthly['setup_price_id'], annual['setup_price_id'])
            setup_prices.add(monthly['setup_price_id'])
            for offer in (monthly, annual):
                recurring_prices.extend([offer['monthly_price_id'], offer['additional_seat_price_id']])
        self.assertEqual(len(setup_prices), 2)
        self.assertEqual(len(set(recurring_prices)), 8)
        self.assertTrue(setup_prices.isdisjoint(recurring_prices))


if __name__ == '__main__':
    unittest.main()
