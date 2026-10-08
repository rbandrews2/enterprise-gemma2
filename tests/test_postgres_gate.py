import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from scripts.run_postgres_gate import discover_suite, gate_passed, main


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
                patch('scripts.run_postgres_gate.discover_suite') as discover:
            self.assertEqual(main(), 2)
            discover.assert_not_called()

    def test_discovery_in_clean_non_package_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tests = root / 'tests'
            tests.mkdir()
            (tests / 'test_gate_discovery_fixture.py').write_text(
                'import unittest\nclass Fixture(unittest.TestCase):\n'
                '    def test_discovered(self):\n        self.assertTrue(True)\n', encoding='utf-8')
            self.assertFalse((tests / '__init__.py').exists())
            suite = discover_suite(root)
            result = unittest.TestResult()
            suite.run(result)
            self.assertEqual(result.testsRun, 1)
            self.assertTrue(gate_passed(result), result.errors)
