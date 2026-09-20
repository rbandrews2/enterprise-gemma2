import unittest
from types import SimpleNamespace
from shared.projects import ProjectDraft
from services.v2.placement import assess_placement


class PlacementReadinessTests(unittest.TestCase):
    def test_missing_inputs_and_empty_library(self):
        draft = ProjectDraft.model_validate({'name':'Example','intake':{'work_type':'line_striping',
            'location':{'address':'Example','locality':'Norfolk'},'requested_outputs':['annotated_image']}})
        result = assess_placement(draft, SimpleNamespace(topics=[]))
        states = {c['id']: c['status'] for c in result['checks']}
        self.assertEqual(states['authority'], 'missing')
        self.assertEqual(states['location'], 'missing')
        self.assertEqual(result['status'], 'missing_inputs')
        self.assertEqual(result['reference_candidate_count'], 0)
        self.assertFalse(result['can_generate_placements'])

    def test_complete_customer_claims_and_references_never_unlock_placements(self):
        draft = ProjectDraft.model_validate({'name':'Example','intake':{'work_type':'line_striping',
            'location':{'latitude':36.85,'longitude':-76.28,'road_authority':'VDOT'},
            'project_date':'2026-10-01','site':{'speed_limit_mph':35,'pedestrians_present':False,'intersections_present':False},
            'requested_outputs':['annotated_image']},'job_geometry':{'closure_type':'lane','duration_hours':2,
            'lane_width_ft':12,'available_sight_distance_ft':0,'travel_direction':'northbound',
            'geometry_source':'customer sketch','work_limits':[{'latitude':36.85,'longitude':-76.28},{'latitude':36.851,'longitude':-76.28}]}})
        result = assess_placement(draft, SimpleNamespace(topics=[SimpleNamespace(candidates=[object()])]))
        self.assertEqual(result['status'], 'review_required')
        self.assertEqual(result['reference_candidate_count'], 1)
        self.assertEqual(result['reviewed_rule_count'], 0)
        self.assertFalse(result['can_generate_placements'])
        self.assertFalse(result['approved_for_field_use'])
        states = {c['id']:c['status'] for c in result['checks']}
        self.assertEqual(states['sight_distance'],'reported_unverified')
        self.assertEqual(states['pedestrians'],'reported_unverified')
        self.assertEqual(states['approach_geometry'],'review_required')
