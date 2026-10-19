"""Inert acceptance-policy checks: no cloud, audio or provider calls."""
from copy import deepcopy
import unittest

from scripts.check_field_voice_workflow import assess


class ReviewDraftAcceptanceTests(unittest.TestCase):
    def report(self, name='Aero boards', count=4, warning=True):
        return {'production_quantities': [
            {'item_name': 'drums', 'quantity': 50},
            {'item_name': name, 'quantity': count}],
            'incidents': [{'time_mentioned': 'noon'}],
            'unresolved': ([f'Confirm equipment: "{name}" may mean "arrow boards". '
                            'Review the item name before sending.'] if warning else [])}

    def test_flagged_heard_label_and_count_are_preserved(self):
        report = self.report()
        original = deepcopy(report)
        assess('traffic-devices', report)
        self.assertEqual(report, original)

    def test_correct_name_requires_no_equipment_warning(self):
        assess('traffic-devices', self.report('arrow boards', warning=False))

    def test_ambiguous_label_without_warning_fails(self):
        with self.assertRaises(RuntimeError):
            assess('traffic-devices', self.report(warning=False))

    def test_generic_warning_is_insufficient(self):
        report = self.report()
        report['unresolved'] = ['Check the report.']
        with self.assertRaises(RuntimeError):
            assess('traffic-devices', report)

    def test_wrong_count_still_fails(self):
        with self.assertRaises(RuntimeError):
            assess('traffic-devices', self.report(count=3))

    def test_unrelated_equipment_still_fails(self):
        with self.assertRaises(RuntimeError):
            assess('traffic-devices', self.report('barriers'))

    def test_missing_incident_time_still_fails(self):
        report = self.report()
        report['incidents'][0]['time_mentioned'] = None
        with self.assertRaises(RuntimeError):
            assess('traffic-devices', report)


if __name__ == '__main__':
    unittest.main()
