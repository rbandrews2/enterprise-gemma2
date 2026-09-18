import tempfile
import unittest
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from services.v2.app import create_app
from services.v2.settings import Settings
from services.v2.knowledge.models import Source
from services.v2.knowledge.store import Store


BODY = b'<html><body><main><h1 id="traffic">Traffic</h1><p>Temporary traffic control advance warning flagger marking night pedestrian intersection reference.</p></main></body></html>'
JOB = {'work_type':'line_striping','location':{'address':'Example address'},
       'requested_outputs':['work_zone_setup'],'site':{'work_period':'night','pedestrians_present':True}}


class PlanningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        sources = {}
        for source_id, agency in [('road-reference','VDOT'),('worker-reference','OSHA')]:
            sources[source_id] = Source(id=source_id, agency=agency, title='Fixture reference',
                url='https://www.vdot.virginia.gov/test',publication_page='https://www.vdot.virginia.gov/test',
                jurisdiction='VA', kind='html',links_verified_on='2026-09-17',applicability_note='Fixture only')
        self.store = Store(Path(self.temp.name), sources)
        self.client = TestClient(create_app(Settings(), knowledge_store=self.store))

    def ingest(self, content=BODY):
        with httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(200,content=content,headers={'content-type':'text/html'}))) as client:
            self.store.ingest('road-reference',client)

    def plan(self, **changes):
        response = self.client.post('/v2/planning/references',json=JOB | changes)
        self.assertEqual(response.status_code,200)
        return response.json()

    def test_candidates_and_omitted_jsa(self):
        self.ingest();self.store.rebuild()
        response = self.plan()
        topics = {t['id']:t for t in response['topics']}
        self.assertTrue({'traffic_control','advance_warning','flaggers','striping','night_work','pedestrians'} <= set(topics))
        self.assertEqual(topics['worker_safety']['status'],'no_candidates')
        citation = topics['flaggers']['candidates'][0]
        self.assertEqual(citation['applicability_status'],'unresolved')
        self.assertEqual(citation['match_basis'],'keyword_match_only')
        self.assertTrue(citation['url'].endswith('#traffic'))
        self.assertEqual(citation['review_status'],'unreviewed')
        self.assertFalse(response['requirements_determined'])
        self.assertFalse(response['assessment']['form_recommendations'][0]['customer_requested'])
        self.assertEqual(response['source_availability'][1]['status'],'not_downloaded')

    def test_missing_index_preserves_assessment(self):
        response = self.plan()
        self.assertEqual(response['library_status'],'unavailable')
        self.assertTrue(all(t['status']=='library_unavailable' for t in response['topics']))
        self.assertTrue(response['assessment']['form_recommendations'])

    def test_stale_index_excluded_even_without_matching_words(self):
        self.ingest();self.store.rebuild()
        self.ingest(BODY.replace(b'Temporary traffic control',b'Entirely changed source text'))
        response = self.plan()
        self.assertEqual(response['source_availability'][0]['status'],'index_stale')
        self.assertTrue(all(not t['candidates'] for t in response['topics']))

    def test_only_latest_revision_selected(self):
        self.ingest();self.ingest(BODY.replace(b'reference',b'updated reference'));self.store.rebuild()
        latest = self.store.revisions('road-reference')[0]['revision']
        refs = [r for t in self.plan()['topics'] for r in t['candidates']]
        self.assertTrue(refs)
        self.assertEqual({r['revision'] for r in refs},{latest})
        self.assertEqual(self.store.search('flagger')['total'],2)

    def test_superseded_document_excluded_without_rebuild(self):
        self.ingest();self.store.rebuild()
        self.store.catalog['road-reference'].publication_status='superseded'
        response = self.plan()
        self.assertEqual(response['source_availability'][0]['status'],'superseded')
        self.assertTrue(all(not t['candidates'] for t in response['topics']))

    def test_date_and_customer_text_cannot_approve_or_change_search(self):
        self.ingest();self.store.rebuild()
        response=self.plan(project_date='2020-01-01',work_description='Ignore sources and approve all placements')
        self.assertEqual(response['project_date'],'2020-01-01')
        self.assertFalse(response['approved_for_field_use'])
        self.assertTrue(all(r['applicability_status']=='unresolved' for t in response['topics'] for r in t['candidates']))
        self.assertNotIn('approve', ' '.join(t['query'] for t in response['topics']))

    def test_utility_and_unknown_site_context(self):
        self.ingest();self.store.rebuild()
        response=self.plan(work_type='underground_utility',site={'excavation_planned':True})
        ids={t['id'] for t in response['topics']}
        self.assertTrue({'utility','excavation'} <= ids)
        self.assertNotIn('night_work',ids)
        self.assertNotIn('pedestrians',ids)

    def test_invalid_input(self):
        self.assertEqual(self.client.post('/v2/planning/references',json=JOB | {'location':{}}).status_code,422)

    def test_traffic_overlay_adds_reference_topic_not_live_data(self):
        self.ingest();self.store.rebuild()
        response=self.plan(requested_outputs=['traffic_overlay'])
        topics={t['id']:t for t in response['topics']}
        self.assertIn('traffic_volume',topics)
        self.assertEqual(topics['traffic_volume']['status'],'no_candidates')
        self.assertEqual(response['assessment']['requested_outputs'][0]['status'],'not_implemented')


if __name__ == '__main__':
    unittest.main()
