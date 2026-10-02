import unittest

from services.workspace_preview.atlas_adapter import select_references


def ref(name, text=None):
    return {'source_id': name, 'revision': 'a' * 64, 'page': None,
            'section': 'Paragraph 1', 'text': text or name,
            'applicability_note': '2024 schedule contracts only', 'review_status': 'unreviewed'}


class ReferenceSelectionTests(unittest.TestCase):
    def setUp(self):
        self.topics = [
            {'id': 'traffic_control', 'candidates': [ref('general')]},
            {'id': 'worker_safety', 'candidates': [ref('osha')]},
            {'id': 'advance_warning', 'candidates': [ref('warning')]},
            {'id': 'striping', 'candidates': [ref('base704'), ref('conditional2024')]},
            {'id': 'marking_materials', 'candidates': [ref('materials'), ref('beads')]},
        ]

    def test_marking_not_starved_by_earlier_generic_topics(self):
        rows = select_references(self.topics, 'Review this pavement marking job', 'line_striping')
        self.assertEqual([r['source_id'] for r in rows], ['base704', 'conditional2024', 'osha'])
        self.assertEqual(rows[1]['applicability_note'], '2024 schedule contracts only')
        self.assertEqual(rows[1]['review_status'], 'unreviewed')

    def test_specific_question_precedes_general_operation(self):
        rows = select_references(self.topics, 'Which materials for pavement marking?', 'line_striping')
        self.assertEqual([r['source_id'] for r in rows], ['materials', 'base704', 'osha'])

    def test_operation_default_and_empty_library(self):
        self.assertEqual(select_references(self.topics, 'Review this job', 'line_striping')[0]['source_id'], 'base704')
        self.assertEqual(select_references([], 'Marking materials', 'line_striping'), [])

    def test_duplicates_do_not_consume_slots_and_metadata_is_not_mutated(self):
        self.topics[3]['candidates'] = [ref('base704'), ref('base704')]
        rows = select_references(self.topics, 'Pavement marking', 'line_striping')
        self.assertEqual([r['source_id'] for r in rows], ['base704', 'osha', 'general'])
        self.assertEqual(len(self.topics[3]['candidates']), 2)

    def test_unrelated_work_preserves_general_fallback(self):
        rows = select_references(self.topics, 'Review warning setup', 'other')
        self.assertEqual([r['source_id'] for r in rows], ['general', 'osha', 'warning'])
