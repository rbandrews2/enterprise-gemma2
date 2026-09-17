import unittest

from fastapi.testclient import TestClient
from pydantic import ValidationError

from services.v2.app import create_app
from services.v2.settings import Settings
from shared.intake import JobLocation


BASE = {"work_type": "line_striping", "location": {"address": "Example address, Virginia"},
        "requested_outputs": ["work_zone_setup"]}


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(Settings()))

    def assess(self, **changes):
        return self.client.post('/v2/intake/assess', json=BASE | changes)

    def test_unrequested_jsa_is_strong_recommendation(self):
        response = self.assess()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        jsa = body['form_recommendations'][0]
        self.assertEqual(jsa['priority'], 'strongly_recommended')
        self.assertFalse(jsa['customer_requested'])
        self.assertIsNone(jsa['legally_required'])
        self.assertEqual(jsa['basis'], 'wzos_product_policy')
        self.assertEqual(body['regulatory_requirements_status'], 'not_evaluated')
        self.assertFalse(body['approved_for_field_use'])

    def test_requested_jsa_not_duplicated(self):
        body = self.assess(requested_forms=['jsa']).json()
        self.assertEqual(len(body['form_recommendations']), 1)
        self.assertTrue(body['form_recommendations'][0]['customer_requested'])

    def test_coordinates_and_combined_location(self):
        coords = {'latitude': 37.54, 'longitude': -77.43}
        response = self.assess(location=coords)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['location_status'], 'unverified')
        body = self.assess(location=coords | {'address': 'Example address'}).json()
        self.assertIn('reconcile_location', {i['id'] for i in body['attention_items']})

    def test_invalid_locations(self):
        for location in [{}, {'address':' '}, {'latitude':37.54}, {'longitude':-77.43},
                         {'latitude':91,'longitude':0}, {'latitude':0,'longitude':181},
                         {'latitude':True,'longitude':-77.43}, {'address':'x','state':'NC'}]:
            with self.subTest(location=location):
                self.assertEqual(self.assess(location=location).status_code, 422)
        with self.assertRaises(ValidationError):
            JobLocation(latitude=float('nan'), longitude=-77.43)

    def test_unknown_hazards_are_not_assumed_absent(self):
        items = {i['id']: i for i in self.assess().json()['attention_items']}
        for item in ['pedestrians_present','intersections_present','work_period','speed_limit_mph','lane_count','traffic_notes']:
            self.assertEqual(items[item]['category'], 'missing_information')
        self.assertIn('striping_operation', items)

    def test_utility_night_and_pedestrian_context(self):
        body = self.assess(work_type='underground_utility', site={'work_period':'night','pedestrians_present':True}).json()
        ids = {i['id'] for i in body['attention_items']}
        self.assertTrue({'utility_work','excavation_planned','night_work','pedestrians_present'} <= ids)
        self.assertNotIn('striping_operation', ids)

    def test_supplied_data_does_not_unlock_unverified_placement(self):
        body = self.assess(site={'speed_limit_mph':35, 'lane_count':2, 'traffic_notes':'Customer reports heavy traffic',
                                'work_period':'day','pedestrians_present':False,'intersections_present':False}).json()
        ids = {i['id'] for i in body['attention_items']}
        self.assertNotIn('speed_limit_mph', ids)
        self.assertIn('verify_site_evidence', ids)
        self.assertIn('placement_engine', ids)
        self.assertEqual(body['requested_outputs'][0]['status'], 'not_implemented')

    def test_form_only_request_still_receives_jsa(self):
        body = self.assess(requested_outputs=['required_forms']).json()
        self.assertEqual(body['form_recommendations'][0]['form_id'], 'jsa')
        self.assertNotIn('placement_engine', {i['id'] for i in body['attention_items']})

    def test_all_deliverables_are_honestly_reported(self):
        outputs = ['work_zone_setup','required_forms','recommended_forms','annotated_image','traffic_overlay','pdf_package','email_delivery']
        body = self.assess(requested_outputs=outputs).json()
        self.assertEqual([item['output'] for item in body['requested_outputs']], outputs)
        self.assertTrue(all(item['status']=='not_implemented' for item in body['requested_outputs']))

    def test_invalid_output_and_context(self):
        for change in [{'requested_outputs':[]}, {'requested_outputs':['work_zone_setup']*2},
                       {'requested_outputs':['invented']}, {'work_type':'other'},
                       {'site':{'lane_count':True}}, {'site':{'speed_limit_mph':-1}},
                       {'site':{'pedestrians_present':'false'}}, {'approved_for_field_use':True}]:
            with self.subTest(change=change):
                self.assertEqual(self.assess(**change).status_code, 422)
        self.assertEqual(self.assess(work_type='other',work_description='Bridge inspection').status_code,200)


if __name__ == '__main__':
    unittest.main()
