import contextlib
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts import verify_atlas_artifacts as verifier


class ArtifactVerifierTests(unittest.TestCase):
    def run_check(self, copied):
        source = {f'file{i}': {'size': '10', 'crc32c': 'abc', 'generation': '1'}
                  for i in range(10)}
        output = io.StringIO()
        with patch.object(verifier.subprocess, 'run', return_value=SimpleNamespace(stdout=b'test-token')), \
                patch.object(verifier, 'inventory', side_effect=[source, copied(source)]), \
                contextlib.redirect_stdout(output):
            result = verifier.main()
        self.assertNotIn('test-token', output.getvalue())
        return result, json.loads(output.getvalue())

    def test_matching_content_different_generations(self):
        result, report = self.run_check(lambda x: {k: dict(v, generation='2') for k, v in x.items()})
        self.assertEqual(result, 0)
        self.assertTrue(report['checksums_match'])
        self.assertEqual(report['bytes'], 100)

    def test_same_size_changed_checksum_rejected(self):
        result, report = self.run_check(lambda x: {k: dict(v, crc32c='changed') for k, v in x.items()})
        self.assertEqual(result, 1)
        self.assertFalse(report['checksums_match'])

    def test_missing_object_rejected(self):
        result, report = self.run_check(lambda x: {k: v for k, v in x.items() if k != 'file1'})
        self.assertEqual(result, 1)
        self.assertEqual(report['objects'], 9)


if __name__ == '__main__':
    unittest.main()
