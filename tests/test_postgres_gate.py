import unittest
from unittest.mock import patch
from scripts.run_postgres_gate import gate_passed, main


class PostgreSQLGateRunnerTests(unittest.TestCase):
    def test_success_with_skips_cannot_pass_database_gate(self):
        result = unittest.TestResult()
        result.testsRun = 20
        self.assertTrue(gate_passed(result))
        result.skipped.append((self, 'Database not configured'))
        self.assertTrue(result.wasSuccessful())
        self.assertFalse(gate_passed(result))

    def test_failure_and_empty_runs_cannot_pass(self):
        result = unittest.TestResult()
        self.assertFalse(gate_passed(result))
        result.testsRun = 1
        result.errors.append((self, 'synthetic failure'))
        self.assertFalse(gate_passed(result))

    def test_missing_configuration_stops_before_discovery(self):
        with patch.dict('os.environ', {'WZOS_TEST_DATABASE_URL': ''}), \
                patch('scripts.run_postgres_gate.unittest.defaultTestLoader.discover') as discover:
            self.assertEqual(main(), 2)
            discover.assert_not_called()
