import copy
import json
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

import httpx
from fastapi import HTTPException
from services.workspace_preview.navigation import Routes, Origin, ENDPOINT, MASK
from tests import test_dispatch as fixture


ROUTE = {'routes': [{'distanceMeters': 2400, 'duration': '300s', 'staticDuration': '240s',
                    'polyline': {'encodedPolyline': '_p~iF~ps|U_ulLnnqC_mqNvxq`@'},
                    'legs': [{'steps': [{'distanceMeters': 2400,
                         'navigationInstruction': {'instructions': 'Head toward Norfolk'}}]}]}]}


class ProviderTests(unittest.TestCase):
    def run_provider(self, response=None, status=200, handler=None):
        calls = []
        def answer(request):
            calls.append(request)
            return handler(request) if handler else httpx.Response(status, json=response)
        with patch.dict(os.environ, {'WZOS_NAVIGATION_ROUTES_ENABLED': '1',
                                     'WZOS_GOOGLE_ROUTES_API_KEY': 'synthetic-private-key'}):
            provider = Routes(httpx.MockTransport(answer))
            result = provider.compute(Origin(latitude=36.8, longitude=-76.2), 'Norfolk, VA')
        return result, calls

    def test_fixed_endpoint_narrow_fields_single_request_and_normalized_traffic(self):
        result, calls = self.run_provider(ROUTE)
        self.assertEqual(len(calls), 1)
        self.assertEqual(str(calls[0].url), ENDPOINT)
        self.assertEqual(calls[0].headers['X-Goog-FieldMask'], MASK)
        sent = json.loads(calls[0].content)
        self.assertEqual(sent['routingPreference'], 'TRAFFIC_AWARE')
        self.assertFalse(sent['computeAlternativeRoutes'])
        self.assertEqual(result['duration_seconds'], 300)
        self.assertEqual(result['static_duration_seconds'], 240)
        self.assertEqual(result['directions'][0]['instruction'], 'Head toward Norfolk')
        self.assertNotIn('synthetic-private-key', json.dumps(result))

    def test_empty_fallback_and_direction_bound(self):
        self.assertEqual(self.run_provider({})[0]['status'], 'empty')
        data = copy.deepcopy(ROUTE); data['fallbackInfo'] = {'reason': 'fallback'}
        data['routes'][0]['legs'][0]['steps'] *= 201
        result, _ = self.run_provider(data)
        self.assertTrue(result['traffic_fallback']); self.assertTrue(result['directions_truncated'])
        self.assertEqual(len(result['directions']), 200)

    def test_provider_failures_do_not_retry_or_leak_details(self):
        for status in (301, 403, 429, 500):
            with self.subTest(status=status), self.assertRaises(HTTPException) as caught:
                self.run_provider({'error': 'synthetic-private-key'}, status)
            self.assertEqual(caught.exception.status_code, 503 if status == 429 else 502)
            self.assertNotIn('synthetic-private-key', str(caught.exception.detail))
        def timeout(request):
            raise httpx.ReadTimeout('synthetic-private-key', request=request)
        with self.assertRaises(HTTPException) as caught:
            self.run_provider(handler=timeout)
        self.assertEqual(caught.exception.status_code, 502)

    def test_oversized_and_invalid_responses(self):
        bad = [[], {'routes': {}}, {'routes': None}]
        for field, value in [('distanceMeters', True), ('duration', 'infinitys'),
                             ('polyline', {'encodedPolyline': '<script>'})]:
            data = copy.deepcopy(ROUTE); data['routes'][0][field] = value; bad.append(data)
        bad.append({'x': 'a' * 262145})
        for data in bad:
            with self.subTest(data=str(data)[:80]), self.assertRaises(HTTPException) as caught:
                self.run_provider(data)
            self.assertEqual(caught.exception.status_code, 502)


class NavigationTests(unittest.TestCase):
    # Reuse the established account/dispatch fixture without inheriting its test methods.
    make_storage = fixture.DispatchTests.make_storage
    organization = fixture.DispatchTests.organization
    h = fixture.DispatchTests.h
    profile = fixture.DispatchTests.profile
    qualify = fixture.DispatchTests.qualify
    requirements = fixture.DispatchTests.requirements
    propose = fixture.DispatchTests.propose
    approve = fixture.DispatchTests.approve

    def setUp(self):
        self.calls = []
        self.route_provider = Routes()
        self.route_provider.enabled = True
        def compute(origin, destination):
            self.calls.append((origin.waypoint(), destination))
            return {'status': 'ready', 'distance_meters': 100, 'directions': []}
        self.route_provider.compute = compute
        with patch('services.workspace_preview.navigation.Routes', return_value=self.route_provider):
            fixture.DispatchTests.setUp(self)

    def route(self, user='admin', org=None, **changes):
        return self.client.post('/api/navigation/route', headers=self.h(user, org),
            json={'order_id': self.order, 'origin': {'address': 'Norfolk station'}, **changes})

    def test_own_orders_admin_member_and_core_are_supported(self):
        self.assertEqual(self.route().status_code, 200)
        for user, org in [('member', self.org), ('coreadmin', self.core)]:
            r = self.client.post('/api/orders', headers=self.h(user, org), json={
                'request_id': str(uuid4()), 'title': 'Own job', 'work_type': 'line_striping',
                'address': 'Public site, Virginia', 'locality': 'Norfolk'})
            self.assertEqual(r.status_code, 201, r.text)
            result = self.route(user, org, order_id=r.json()['id'])
            self.assertEqual(result.status_code, 200, result.text)
            self.assertEqual(result.json()['destination_basis'], 'work_order')

    def test_private_order_and_tenant_access_block_provider(self):
        for user, org in [('member', self.org), ('rival', self.rival), ('admin', self.rival)]:
            self.assertIn(self.route(user, org).status_code, (403, 404))
        self.assertEqual(self.calls, [])
        self.assertIn(self.client.get('/api/navigation/config').status_code, (401, 403))

    def test_own_assignment_uses_frozen_destination_and_revocation(self):
        self.requirements(); self.approve(self.propose())
        assignment = self.client.get('/api/dispatch/my-assignments', headers=self.h('member')).json()['items'][0]
        with self.app.state.accounts.connect() as db:
            row = db.execute('SELECT payload FROM preview_orders WHERE id=?', (self.order,)).fetchone()
            payload = json.loads(row['payload']); payload['address'] = 'Private changed address'
            db.execute('UPDATE preview_orders SET payload=? WHERE id=?', (json.dumps(payload), self.order))
        body = {'order_id': None, 'assignment_id': assignment['id']}
        result = self.route('member', **body)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['destination'], 'Granby Street, Norfolk, VA')
        self.assertEqual(result.json()['destination_basis'], 'dispatched_snapshot')
        self.assertEqual(self.route('other', **body).status_code, 404)
        self.assertEqual(self.route('coreadmin', self.core, **body).status_code, 403)
        with self.app.state.accounts.connect() as db:
            db.execute("UPDATE dispatch_assignments SET status='cancelled' WHERE id=?", (assignment['id'],))
        self.assertEqual(self.route('member', **body).status_code, 404)
        self.assertEqual(len(self.calls), 1)

    def test_input_validation_precedes_provider(self):
        for changes in ({'origin': {}}, {'origin': {'latitude': 91, 'longitude': 0}},
                        {'origin': {'latitude': True, 'longitude': 0}},
                        {'origin': {'address': 'x', 'latitude': 0, 'longitude': 0}},
                        {'origin': {'address': 'x' * 251}}, {'destination': 'arbitrary'},
                        {'assignment_id': str(uuid4())}, {'order_id': None}):
            self.assertEqual(self.route(**changes).status_code, 422, changes)
        self.assertEqual(self.calls, [])

    def test_rate_bound_and_failure_release(self):
        for _ in range(6):
            self.assertEqual(self.route().status_code, 200)
        denied = self.route()
        self.assertEqual(denied.status_code, 429)
        self.assertEqual(denied.headers['Retry-After'], '60')
        self.assertEqual(len(self.calls), 6)

    def test_disabled_is_explicit_and_does_not_expose_key(self):
        self.route_provider.enabled = False
        def disabled(*args):
            raise HTTPException(503, 'In-app routing is not configured')
        self.route_provider.compute = disabled
        config = self.client.get('/api/navigation/config', headers=self.h())
        self.assertFalse(config.json()['routes_enabled'])
        self.assertFalse(config.json()['background_navigation'])
        self.assertEqual(self.route().status_code, 503)
        self.assertEqual(self.calls, [])


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'), 'Dedicated PostgreSQL database not configured')
class PostgreSQLNavigationTests(NavigationTests):
    def make_storage(self, root):
        from tests.test_form_submissions import PostgreSQLFormSubmissionTests
        return PostgreSQLFormSubmissionTests.make_storage(self, root)
