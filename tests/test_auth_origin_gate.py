import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('auth_origin_gate', Path(__file__).parents[1] / 'scripts/check_auth_origin.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class AuthOriginGateTests(unittest.TestCase):
    def test_expected_validation_is_accepted(self):
        self.assertTrue(gate.validation_reached(400, {'error': {'message': 'INVALID_EMAIL'}}, {'INVALID_EMAIL'}))

    def test_origin_denial_cannot_pass(self):
        self.assertFalse(gate.validation_reached(403, {'error': {'message': 'INVALID_EMAIL'}}, {'INVALID_EMAIL'}))

    def test_invalid_key_cannot_pass_as_input_validation(self):
        self.assertFalse(gate.validation_reached(400, {'error': {'message': 'API_KEY_INVALID'}}, {'INVALID_EMAIL'}))

    def test_success_cannot_pass_negative_probe(self):
        self.assertFalse(gate.validation_reached(200, {}, {'INVALID_EMAIL'}))

    def test_non_origin_is_rejected_before_network(self):
        for origin in ('http://app.workzoneos.org', 'https://app.workzoneos.org/path', 'https://user:password@example.org'):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                gate.check(origin)
