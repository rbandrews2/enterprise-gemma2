"""Cloud adapter contracts with a synthetic bucket; never reads real objects."""
import hashlib
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from google.api_core.exceptions import NotFound, PreconditionFailed
from services.workspace_preview.files import GoogleFiles, MAX_BYTES


class GoogleFilesTests(unittest.TestCase):
    def setUp(self):
        self.bucket = Mock()
        self.bucket.iam_configuration = SimpleNamespace(
            uniform_bucket_level_access_enabled=True, public_access_prevention='enforced')
        self.client = Mock()
        self.client.bucket.return_value = self.bucket
        self.store = GoogleFiles('synthetic-private-bucket', self.client)
        self.blob = self.bucket.blob.return_value

    def test_private_bucket_requirements_fail_closed(self):
        for uniform, prevention in ((False, 'enforced'), (True, 'inherited')):
            self.bucket.iam_configuration.uniform_bucket_level_access_enabled = uniform
            self.bucket.iam_configuration.public_access_prevention = prevention
            with self.assertRaises(ValueError):
                GoogleFiles('synthetic-private-bucket', self.client)

    def test_create_only_upload_and_digest_metadata(self):
        self.store.put('org/file', b'synthetic', 'application/pdf')
        self.assertEqual(self.blob.metadata, {'sha256': hashlib.sha256(b'synthetic').hexdigest()})
        self.blob.upload_from_string.assert_called_once_with(
            b'synthetic', content_type='application/pdf', if_generation_match=0, timeout=30)

    def test_identical_retry_and_conflicting_retry(self):
        self.blob.upload_from_string.side_effect = PreconditionFailed('synthetic collision')
        self.blob.size = len(b'synthetic')
        self.store.put('org/file', b'synthetic', 'application/pdf')
        self.blob.reload.assert_called_once_with(timeout=20)
        # reload replaces client-side metadata with the actual stored object's digest.
        def differing_metadata(**kwargs):
            self.blob.metadata = {'sha256': 'different'}
        self.blob.reload.side_effect = differing_metadata
        with self.assertRaisesRegex(ValueError, 'Object conflict'):
            self.store.put('org/file', b'synthetic', 'application/pdf')

    def test_read_pins_observed_generation(self):
        self.blob.size, self.blob.generation = 9, 123
        self.blob.download_as_bytes.return_value = b'synthetic'
        self.assertEqual(self.store.get('org/file'), b'synthetic')
        self.blob.download_as_bytes.assert_called_once_with(if_generation_match=123, timeout=30)

    def test_oversize_never_downloaded(self):
        self.blob.size = MAX_BYTES + 1
        with self.assertRaises(ValueError):
            self.store.get('org/file')
        self.blob.download_as_bytes.assert_not_called()

    def test_generation_change_fails_instead_of_reading_replacement(self):
        self.blob.size, self.blob.generation = 9, 123
        self.blob.download_as_bytes.side_effect = PreconditionFailed('generation changed')
        with self.assertRaises(PreconditionFailed):
            self.store.get('org/file')
        self.blob.download_as_bytes.assert_called_once()

    def test_delete_missing_is_idempotent_but_other_errors_propagate(self):
        self.blob.delete.side_effect = NotFound('already absent')
        self.store.delete('org/file')
        self.blob.delete.side_effect = RuntimeError('storage unavailable')
        with self.assertRaises(RuntimeError):
            self.store.delete('org/file')


if __name__ == '__main__':
    unittest.main()
