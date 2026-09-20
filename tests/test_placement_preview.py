import unittest
import asyncio
import httpx
from fastapi.testclient import TestClient
from services.v2.app import create_app
from services.v2.placement_preview import preview
from shared.placement_preview import PlacementPreviewRequest


def lookup(road, speed):
    return preview(PlacementPreviewRequest(scenario='stationary_shoulder',road_class=road,posted_speed_mph=speed))


class PlacementPreviewTests(unittest.TestCase):
    def test_spacing_boundaries_and_road_classes(self):
        cases = [('conventional',35,(100,200)),('conventional',40,(350,500)),
                 ('conventional',45,(350,500)),('undivided',50,(500,800)),
                 ('undivided',55,(500,800)),('divided_non_limited',50,(1000,1300)),
                 ('divided_non_limited',75,(1000,1300)),('limited_access',35,(1300,1500))]
        for road,speed,expected in cases:
            with self.subTest(road=road,speed=speed):
                result=lookup(road,speed)
                spacing=result['advance_warning_spacing_ft']
                self.assertEqual((spacing['minimum'],spacing['maximum']),expected)
                self.assertEqual(result['placements'],[])
                self.assertFalse(result['approved_for_field_use'])

    def test_buffer_rows_and_no_interpolation(self):
        for speed,expected in [(20,115),(25,155),(30,200),(35,250),(40,305),(45,360),
                               (50,425),(55,495),(60,570),(65,645),(70,730),(75,820)]:
            self.assertEqual(lookup('limited_access',speed)['buffer_space_ft']['minimum'],expected)
        for speed in (19,36,39,46,49,56,76):
            result=lookup('limited_access',speed)
            self.assertIsNone(result['buffer_space_ft'])
            self.assertEqual(result['status'],'unsupported_table_input')
        for speed in (36,39,46,49,60):
            self.assertIsNone(lookup('undivided',speed)['advance_warning_spacing_ft'])

    def test_api_validation_citation_and_local_boundary(self):
        with TestClient(create_app()) as client:
            payload={'scenario':'stationary_shoulder','road_class':'conventional','posted_speed_mph':35}
            result=client.post('/v2/placement/reference-preview',json=payload)
            self.assertEqual(result.status_code,200)
            self.assertEqual(result.json()['citation']['pdf_page'],157)
            self.assertEqual(result.json()['citation']['printed_page'],147)
            self.assertIn('Known Error',' '.join(result.json()['limitations']))
            for update in ({'posted_speed_mph':True},{'posted_speed_mph':'35'},
                           {'posted_speed_mph':0},{'scenario':'lane_closure'},
                           {'road_class':'unknown'},{'approved':True}):
                self.assertEqual(client.post('/v2/placement/reference-preview',json=payload|update).status_code,422)
        async def remote_check():
            transport=httpx.ASGITransport(app=create_app(),client=('203.0.113.1',1234))
            async with httpx.AsyncClient(transport=transport,base_url='http://test') as remote:
                self.assertEqual((await remote.post('/v2/placement/reference-preview',json=payload)).status_code,403)
        asyncio.run(remote_check())
