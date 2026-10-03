from copy import deepcopy
from datetime import datetime, timezone, timedelta
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.validate_atlas_cold_start import zero_observation, run, PROJECT, MODEL_SERVICE, METRIC


class ColdStartTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 3, tzinfo=timezone.utc)
        self.revision = 'wzos-atlas-inference-00001-test'
        self.data = {'timeSeries': [
            {'resource': {'type': 'cloud_run_revision', 'labels': {
                'project_id': PROJECT, 'service_name': MODEL_SERVICE, 'revision_name': self.revision}},
             'metric': {'type': METRIC, 'labels': {'state': state}},
             'points': [{'interval': {'endTime': (self.now-timedelta(seconds=age)).isoformat()},
                         'value': {'int64Value': '0'}} for age in (90, 150)]}
            for state in ('active', 'idle')]}

    def test_zero_is_provisional(self):
        result = zero_observation(self.data, self.revision, self.now)
        self.assertTrue(result['startup_log_correlation_required'])

    def test_missing_and_partial_metrics_rejected(self):
        for data in ({}, {'timeSeries': self.data['timeSeries'][:1]},
                     {**self.data, 'nextPageToken': 'more'}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                zero_observation(data, self.revision, self.now)

    def test_nonzero_invalid_and_missing_values_rejected(self):
        for value in ({'int64Value': '1'}, {}, {'int64Value': True}, {'doubleValue': 0}):
            data = deepcopy(self.data); data['timeSeries'][1]['points'][0]['value'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                zero_observation(data, self.revision, self.now)

    def test_stale_future_and_unmatched_samples_rejected(self):
        for age in (-1, 300, 95):
            data = deepcopy(self.data)
            data['timeSeries'][0]['points'][0]['interval']['endTime'] = (self.now-timedelta(seconds=age)).isoformat()
            with self.subTest(age=age), self.assertRaises(ValueError):
                zero_observation(data, self.revision, self.now)

    def test_wrong_scope_and_duplicate_state_rejected(self):
        data = deepcopy(self.data); data['timeSeries'][0]['resource']['labels']['project_id'] = 'other'
        with self.assertRaises(ValueError): zero_observation(data, self.revision, self.now)
        data = deepcopy(self.data); data['timeSeries'].append(data['timeSeries'][0])
        with self.assertRaises(ValueError): zero_observation(data, self.revision, self.now)
        with self.assertRaises(ValueError): zero_observation(self.data, 'other-revision', self.now)

    @patch('scripts.validate_atlas_cold_start.gc')
    def test_disabled_fixture_and_existing_output_do_not_call_cloud(self, gc):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'evidence.jsonl'
            with self.assertRaises(ValueError): run({'disabled': True}, output)
            output.write_text('preserved')
            with self.assertRaises(FileExistsError): run({}, output)
            self.assertEqual(output.read_text(), 'preserved')
        gc.assert_not_called()
