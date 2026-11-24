import json
import unittest
from unittest.mock import MagicMock, patch
from google.api_core.exceptions import NotFound, PreconditionFailed
from services.v2.knowledge.research_cloud import execute


class CloudResearchTests(unittest.TestCase):
    def bucket(self):
        bucket = MagicMock()
        blobs = {}
        def blob(name):
            if name not in blobs:
                blobs[name] = MagicMock()
                blobs[name].generation = 7
            return blobs[name]
        bucket.blob.side_effect = blob
        bucket.list_blobs.return_value = []
        blob('lease.json').reload.side_effect = NotFound('missing')
        blob('state.json').reload.side_effect = NotFound('missing')
        return bucket, blobs

    def test_lease_race_skips_without_work(self):
        bucket, blobs = self.bucket()
        blobs['lease.json'].upload_from_string.side_effect = PreconditionFailed('race')
        self.assertEqual(execute(bucket)['status'], 'already_running')
        bucket.list_blobs.assert_not_called()
        blobs['lease.json'].delete.assert_not_called()

    def test_active_lease_skips(self):
        bucket, blobs = self.bucket()
        blobs['lease.json'].reload.side_effect = None
        blobs['lease.json'].download_as_bytes.return_value = json.dumps({'expires': 10**12}).encode()
        self.assertEqual(execute(bucket)['status'], 'already_running')
        blobs['lease.json'].upload_from_string.assert_not_called()

    @patch('services.v2.knowledge.research_cloud.run')
    def test_candidates_before_baseline_and_lease_cleanup(self, run):
        bucket, blobs = self.bucket()
        def complete(root, *args, **kwargs):
            (root / 'state.json').write_text('{}')
            directory = root / 'candidates' / 'urlhash' / 'contenthash'
            directory.mkdir(parents=True)
            (directory / 'source.pdf').write_bytes(b'%PDF-test')
            return {'status': 'completed', 'results': []}
        run.side_effect = complete
        self.assertEqual(execute(bucket)['status'], 'completed')
        blobs['candidates/urlhash/contenthash/source.pdf'].upload_from_filename.assert_called_once()
        blobs['state.json'].upload_from_filename.assert_called_once()
        blobs['lease.json'].delete.assert_called_once_with(if_generation_match=7)

    @patch('services.v2.knowledge.research_cloud.run')
    def test_failed_upload_does_not_advance_baseline(self, run):
        bucket, blobs = self.bucket()
        run.return_value = {'status': 'completed', 'results': []}
        bucket.blob('latest.json').upload_from_string.side_effect = RuntimeError('outage')
        with self.assertRaises(RuntimeError):
            execute(bucket)
        blobs['state.json'].upload_from_filename.assert_not_called()
        blobs['lease.json'].delete.assert_called_once()
