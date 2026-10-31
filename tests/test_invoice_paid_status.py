import unittest

from services.workspace_preview.purchase_lifecycle import invoice_is_paid


class InvoicePaidStatusTests(unittest.TestCase):
    def test_current_and_legacy_paid_invoices(self):
        self.assertTrue(invoice_is_paid({'status': 'paid'}))
        self.assertTrue(invoice_is_paid({'status': 'paid', 'paid': True}))

    def test_unpaid_missing_and_contradictory_data_are_denied(self):
        for invoice in (None, 'in_unexpanded', {}, {'paid': True},
                        {'status': 'open'}, {'status': 'void'},
                        {'status': 'paid', 'paid': False},
                        {'status': 'paid', 'paid': None},
                        {'status': 'paid', 'paid': 1}):
            with self.subTest(invoice=invoice):
                self.assertFalse(invoice_is_paid(invoice))
