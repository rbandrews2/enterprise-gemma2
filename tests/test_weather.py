import copy
import json
import os
import re
import unittest
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

import httpx

from services.workspace_preview.weather import NWS, now, alerts_normalized, sms_blocker, background_enabled
from tests import test_dispatch as fixture


def hazard(base=None):
    moment = base or now()
    return {'id': 'urn:test:nws:warning', 'event': 'Severe Thunderstorm Warning',
            'headline': 'Synthetic severe weather', 'description': 'Synthetic source details',
            'instruction': 'Synthetic test only', 'severity': 'Severe', 'active': True,
            'sent': moment.isoformat(), 'effective': (moment-timedelta(minutes=1)).isoformat(),
            'expires': (moment+timedelta(hours=1)).isoformat(), 'source': 'National Weather Service'}


class ProviderTests(unittest.TestCase):
    def test_background_coverage_is_explicitly_organization_scoped(self):
        with patch.dict(os.environ,{'WZOS_WEATHER_BACKGROUND_ENABLED':'1','WZOS_WEATHER_MONITORED_ORGANIZATIONS':'pilot-org'}):
            self.assertTrue(background_enabled('pilot-org'))
            self.assertFalse(background_enabled('another-org'))

    def provider(self, error=False, forecast_error=False, malicious=False):
        calls = []
        a = hazard()
        def handle(request):
            calls.append(str(request.url))
            if error:
                return httpx.Response(503)
            path = request.url.path
            if path.startswith('/points/'):
                return httpx.Response(200, json={'properties': {'forecastHourly': 'https://evil.test/secret' if malicious else 'https://api.weather.gov/gridpoints/AKQ/1,2/forecast/hourly', 'observationStations': 'https://api.weather.gov/gridpoints/AKQ/1,2/stations', 'relativeLocation': {'properties': {'city': 'Synthetic city', 'state': 'VA'}}}})
            if path.endswith('/hourly'):
                if forecast_error:
                    return httpx.Response(503)
                return httpx.Response(200, json={'properties': {'updateTime': now().isoformat(), 'periods': [{'startTime': (now()-timedelta(hours=1)).isoformat(), 'endTime': (now()+timedelta(hours=1)).isoformat(), 'temperature': 70, 'temperatureUnit': 'F', 'shortForecast': 'Cloudy'}]}})
            if path == '/alerts/active':
                return httpx.Response(200, json={'features': [{'properties': {**a, 'status': 'Actual', 'scope': 'Public'}}]})
            if path.endswith('/stations'):
                return httpx.Response(200, json={'features': [{'id': 'https://api.weather.gov/stations/TEST'}]})
            return httpx.Response(200, json={'properties': {'timestamp': now().isoformat(), 'temperature': {'value': 20, 'unitCode': 'wmoUnit:degC'}, 'windSpeed': {'value': 10, 'unitCode': 'wmoUnit:m_s-1'}, 'windGust': {'value': None}, 'precipitationLastHour': {'value': 25.4, 'unitCode': 'wmoUnit:mm'}}})
        return NWS(httpx.MockTransport(handle)), calls

    def test_real_units_null_gusts_and_cache(self):
        provider, calls = self.provider()
        data = provider.current(36.8, -76.2)
        self.assertEqual(data['temperature_f'], 68)
        self.assertEqual(data['wind_mph'], 22.4)
        self.assertEqual(data['precipitation_inches'], 1)
        self.assertIsNone(data['gust_mph'])
        self.assertEqual(len(data['alerts']), 1)
        self.assertEqual(data['basis'], 'observation')
        count = len(calls)
        self.assertEqual(provider.current(36.8, -76.2), data)
        self.assertEqual(len(calls), count)

    def test_outage_never_creates_readings_and_backs_off(self):
        provider, calls = self.provider(error=True)
        self.assertEqual(provider.current(1., 2.)['status'], 'unavailable')
        self.assertNotIn('temperature_f', provider.current(1., 2.))
        self.assertEqual(len(calls), 1)

    def test_real_stale_cache_retains_original_time(self):
        provider, _ = self.provider()
        data = provider.current(1., 2.)
        provider.cache[(1., 2.)] = (-10000, data)
        provider.transport = httpx.MockTransport(lambda r: httpx.Response(503))
        stale = provider.current(1., 2.)
        self.assertEqual(stale['status'], 'stale')
        self.assertEqual(stale['source_time'], data['source_time'])

    def test_forecast_outage_does_not_drop_official_alerts(self):
        provider, _ = self.provider(forecast_error=True)
        self.assertEqual(len(provider.current(1., 2.)['alerts']), 1)

    def test_foreign_response_links_not_requested(self):
        provider, calls = self.provider(malicious=True)
        provider.current(1., 2.)
        self.assertTrue(all(url.startswith('https://api.weather.gov/') for url in calls))

    def test_test_private_future_and_expired_alerts_excluded(self):
        p = {**hazard(), 'status': 'Actual', 'scope': 'Public'}
        for field, value in [('status', 'Test'), ('scope', 'Private'), ('effective', (now()+timedelta(days=1)).isoformat()), ('expires', (now()-timedelta(days=1)).isoformat())]:
            self.assertEqual(alerts_normalized([{'properties': {**p, field: value}}]), [])


class WeatherTests(unittest.TestCase):
    make_storage = fixture.DispatchTests.make_storage
    organization = fixture.DispatchTests.organization
    h = fixture.DispatchTests.h
    profile = fixture.DispatchTests.profile
    qualify = fixture.DispatchTests.qualify
    requirements = fixture.DispatchTests.requirements
    propose = fixture.DispatchTests.propose
    approve = fixture.DispatchTests.approve

    def setUp(self):
        fixture.DispatchTests.setUp(self)
        self.service = self.app.state.weather
        self.data = {'status': 'ready', 'alerts': [hazard()]}
        self.service.provider.current = lambda *args: copy.deepcopy(self.data)

    def configure(self, user='admin', org=None, order=None, **change):
        return self.client.put('/api/weather/sites/'+(order or self.order), headers=self.h(user, org), json={
            'latitude': 36.8, 'longitude': -76.2, 'radius_meters': 350, 'expected_version': 0,
            'monitoring': True, 'starts_at': (now()-timedelta(minutes=1)).isoformat(), 'ends_at': (now()+timedelta(hours=1)).isoformat(), **change})

    def test_admin_version_coordinate_validation_and_tenant_boundaries(self):
        self.assertEqual(self.configure(user='member').status_code, 403)
        self.assertEqual(self.configure(user='rival',org=self.rival).status_code, 404)
        self.assertEqual(self.configure(latitude=91.).status_code, 422)
        self.assertEqual(self.configure().status_code, 200)
        self.assertEqual(self.configure().status_code, 409)
        self.assertEqual(self.client.get('/api/weather/sites',headers=self.h('member')).json()['items'], [])
        self.assertEqual(len(self.client.get('/api/weather/sites',headers=self.h()).json()['items']),1)

    def test_core_weather_and_no_anonymous_access(self):
        self.assertEqual(self.client.post('/api/weather/current',json={'latitude':1.,'longitude':2.}).status_code,401)
        response=self.client.post('/api/weather/current',headers=self.h('coreadmin',self.core),json={'latitude':1.,'longitude':2.})
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.client.post('/api/weather/current',headers=self.h('coreadmin',self.core),json={'latitude':1.,'longitude':2.}).status_code,429)

    def test_durable_notice_dedup_ack_and_supersession(self):
        self.assertEqual(self.configure().status_code,200)
        self.assertEqual(self.service.poll(self.org)['notices'],1)
        self.assertEqual(self.service.poll(self.org)['notices'],0)
        notices=self.client.get('/api/weather/notices',headers=self.h()).json()['items']
        self.assertEqual(len(notices),1)
        rid=notices[0]['id']
        self.assertEqual(self.client.post('/api/weather/notices/'+rid+'/ack',headers=self.h('member')).status_code,404)
        self.assertEqual(self.client.post('/api/weather/notices/'+rid+'/ack',headers=self.h()).status_code,200)
        self.data['alerts'][0]['headline']='Updated synthetic warning'
        self.assertEqual(self.service.poll(self.org)['notices'],1)
        self.assertEqual(sum(not n['superseded'] for n in self.client.get('/api/weather/notices',headers=self.h()).json()['items']),1)
        self.data['alerts']=[]
        self.assertEqual(self.service.poll(self.org)['notices'],1)

    def test_outage_does_not_resolve_or_duplicate_warning(self):
        self.configure();self.service.poll(self.org)
        self.data={'status':'unavailable','alerts':[]}
        self.assertEqual(self.service.poll(self.org)['unavailable'],1)
        notices=self.client.get('/api/weather/notices',headers=self.h()).json()['items']
        self.assertEqual(len(notices),1)
        self.assertTrue(notices[0]['alert']['active'])

    def test_alert_that_expires_in_cache_does_not_create_new_warning(self):
        self.configure()
        self.data['alerts'][0]['expires']=(now()-timedelta(seconds=1)).isoformat()
        self.assertEqual(self.service.poll(self.org)['notices'],0)

    def test_assignment_recipient_and_revocation_at_sms_send(self):
        self.requirements();self.approve(self.propose())
        with patch('services.workspace_preview.weather.now',return_value=fixture.START):
            self.data={'status':'ready','alerts':[hazard(fixture.START)]}
            self.assertEqual(self.configure(starts_at=(fixture.START-timedelta(hours=1)).isoformat(),ends_at=(fixture.END+timedelta(hours=1)).isoformat()).status_code,200)
            self.service.poll(self.org)
            member=self.client.get('/api/weather/notices',headers=self.h('member')).json()['items']
            self.assertEqual(len(member),1)
            with self.service.connect() as db:
                row={'reference_id':member[0]['id'],'organization_id':self.org,'recipient_id':'member','created_by':'admin'}
                with patch.dict(os.environ,{'WZOS_WEATHER_SMS_ENABLED':'1'}):
                    self.assertIsNone(sms_blocker(db,row))
                    db.execute("UPDATE dispatch_assignments SET status='cancelled' WHERE organization_id=? AND user_id='member'",(self.org,))
                    self.assertEqual(sms_blocker(db,row),'weather_notice_superseded')
            self.assertEqual(self.client.get('/api/weather/notices',headers=self.h('member')).json()['items'],[])

    def test_future_window_inactive_site_and_removed_admin_make_no_notices(self):
        self.configure(starts_at=(now()+timedelta(hours=2)).isoformat(),ends_at=(now()+timedelta(hours=3)).isoformat())
        self.assertEqual(self.service.poll(self.org)['checked'],0)
        self.configure(expected_version=1)
        with self.service.connect() as db:
            db.execute("UPDATE memberships SET active=0 WHERE organization_id=? AND user_id='admin'",(self.org,))
        self.assertEqual(self.service.poll(self.org)['notices'],0)

    def test_weather_sms_reuses_verification_allowlist_optout_and_dedup(self):
        contact=self.client.get('/api/messaging/sms/contact',headers=self.h()).json()
        response=self.client.put('/api/messaging/sms/contact',headers=self.h(),json={'request_id':str(uuid4()),'expected_version':contact['version'],'phone':fixture.PHONE,'consent':True,'consent_version':contact['current_consent_version']})
        self.assertEqual(response.status_code,200,response.text)
        code=re.search(r'code: (\d{6})',self.provider.sent[-1]['body']).group(1)
        self.assertEqual(self.client.post('/api/messaging/sms/contact/verify',headers=self.h(),json={'code':code}).status_code,200)
        self.configure()
        with patch.dict(os.environ,{'WZOS_WEATHER_SMS_ENABLED':'1'}):
            self.service.poll(self.org)
            sent=len(self.provider.sent)
            self.assertEqual(sent,2)
            self.service.poll(self.org)
            self.assertEqual(len(self.provider.sent),sent)
            version=self.client.get('/api/messaging/sms/contact',headers=self.h()).json()['version']
            self.assertEqual(self.client.post('/api/messaging/sms/contact/opt-out',headers=self.h(),json={'expected_version':version}).status_code,200)
            self.data['alerts'][0]['headline']='Updated after opt-out'
            self.service.poll(self.org)
            self.assertEqual(len(self.provider.sent),sent)


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'), 'Dedicated PostgreSQL database not configured')
class PostgreSQLWeatherTests(WeatherTests):
    def make_storage(self, root):
        from tests.test_organization_hub import PostgreSQLOrganizationHubTests
        return PostgreSQLOrganizationHubTests.make_storage(self, root)
