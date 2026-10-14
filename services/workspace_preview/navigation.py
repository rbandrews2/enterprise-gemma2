"""Read-only Google routing for permitted jobs; no tracking or attendance mutation."""
import json
import os
import re
import threading
import time
from collections import deque
from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

ENDPOINT = 'https://routes.googleapis.com/directions/v2:computeRoutes'
MASK = ('routes.distanceMeters,routes.duration,routes.staticDuration,'
        'routes.polyline.encodedPolyline,routes.legs.steps.distanceMeters,'
        'routes.legs.steps.navigationInstruction.instructions,fallbackInfo')


class Origin(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    address: str | None = Field(default=None, min_length=1, max_length=250)
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False, strict=True)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False, strict=True)

    @model_validator(mode='after')
    def one_location(self):
        if self.address is not None:
            if self.latitude is not None or self.longitude is not None:
                raise ValueError('Use an address or coordinates, not both')
        elif self.latitude is None or self.longitude is None:
            raise ValueError('Origin requires an address or both coordinates')
        return self

    def waypoint(self):
        return {'address': self.address} if self.address else {
            'location': {'latLng': {'latitude': self.latitude, 'longitude': self.longitude}}}


class RouteRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    order_id: UUID | None = None
    assignment_id: UUID | None = None
    destination: str | None = Field(default=None, min_length=1, max_length=250)
    origin: Origin

    @model_validator(mode='after')
    def one_target(self):
        if sum(value is not None for value in (self.order_id, self.assignment_id, self.destination)) != 1:
            raise ValueError('Select exactly one job, assignment or destination')
        if self.destination is not None:
            self.destination = self.destination.strip()
            if not self.destination:
                raise ValueError('Enter a destination address')
        return self


class Routes:
    def __init__(self, transport=None):
        self.transport = transport
        self.key = os.getenv('WZOS_GOOGLE_ROUTES_API_KEY', '').strip()
        self.enabled = os.getenv('WZOS_NAVIGATION_ROUTES_ENABLED') == '1' and bool(self.key)

    def compute(self, origin, destination):
        if not self.enabled:
            raise HTTPException(503, 'In-app routing is not configured yet. Use Open in Navigation.')
        try:
            with httpx.Client(timeout=httpx.Timeout(20, connect=5), transport=self.transport,
                              follow_redirects=False, trust_env=False) as client:
                with client.stream('POST', ENDPOINT, headers={
                    'X-Goog-Api-Key': self.key, 'X-Goog-FieldMask': MASK,
                }, json={'origin': origin.waypoint(), 'destination': {'address': destination},
                         'travelMode': 'DRIVE', 'routingPreference': 'TRAFFIC_AWARE',
                         'computeAlternativeRoutes': False, 'languageCode': 'en-US',
                         'units': 'IMPERIAL'}) as response:
                    if response.status_code == 429:
                        raise HTTPException(503, 'Routing provider quota reached. Try later.')
                    if response.status_code != 200:
                        raise HTTPException(502, 'Routing provider unavailable. No route was confirmed.')
                    raw = bytearray()
                    for chunk in response.iter_bytes():
                        if len(raw) + len(chunk) > 262144:
                            raise ValueError('Response too large')
                        raw.extend(chunk)
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError('Invalid response')
            routes = data.get('routes', [])
            if not isinstance(routes, list):
                raise ValueError('Invalid routes')
            if not routes:
                return {'status': 'empty', 'message': 'No driving route returned for these locations.'}
            route = routes[0]
            distance = route['distanceMeters']
            if type(distance) is not int or not 0 <= distance <= 100000000:
                raise ValueError('Invalid distance')
            def seconds(value):
                if not isinstance(value, str) or not re.fullmatch(r'\d+(?:\.\d{1,9})?s', value):
                    raise ValueError('Invalid duration')
                result = float(value[:-1])
                if result > 2678400:
                    raise ValueError('Invalid duration')
                return result
            duration = seconds(route['duration'])
            static = seconds(route.get('staticDuration', route['duration']))
            line = route['polyline']['encodedPolyline']
            if not isinstance(line, str) or not re.fullmatch(r'[?-~]{1,20000}', line):
                raise ValueError('Invalid route line')
            steps = [step for leg in route.get('legs', []) for step in leg.get('steps', [])]
            directions = []
            for step in steps[:200]:
                instruction = step.get('navigationInstruction', {}).get('instructions', '')
                meters = step.get('distanceMeters', 0)
                if not isinstance(instruction, str) or type(meters) is not int or meters < 0:
                    raise ValueError('Invalid direction')
                directions.append({'instruction': instruction[:1000], 'distance_meters': meters})
            return {'status': 'ready', 'distance_meters': distance, 'duration_seconds': duration,
                    'static_duration_seconds': static, 'encoded_polyline': line,
                    'directions': directions, 'directions_truncated': len(steps) > 200,
                    'traffic_fallback': bool(data.get('fallbackInfo')), 'provider': 'Google Maps',
                    'calculated_at': datetime.now(timezone.utc).isoformat()}
        except HTTPException:
            raise
        except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
            raise HTTPException(502, 'Route could not be confirmed. Try again or use Open in Navigation.') from None


def register(app, connect, actor, permitted_row, *, accounts=False, provider=None):
    provider = provider or Routes()
    lock, history, concurrent = threading.Lock(), {}, threading.BoundedSemaphore(4)

    def limit(user):
        now = time.monotonic()
        with lock:
            for key in list(history):
                while history[key] and history[key][0] <= now - 60:
                    history[key].popleft()
                if not history[key]:
                    del history[key]
            keys = [(('actor', user['organization_id'], user['id']), 6),
                    (('org', user['organization_id']), 20), (('process',), 60)]
            if len(history) > 2000 or any(len(history.get(k, ())) >= cap for k, cap in keys):
                raise HTTPException(429, 'Too many route requests. Wait a minute before trying again.',
                                    headers={'Retry-After': '60'})
            for key, _ in keys:
                history.setdefault(key, deque()).append(now)

    @app.get('/api/navigation/config')
    def config(request: Request):
        actor(request)
        return {'routes_enabled': provider.enabled,
                'maps_enabled': bool(os.getenv('WZOS_GOOGLE_MAPS_BROWSER_KEY', '').strip()),
                'background_navigation': False, 'offline_routes': False}

    @app.post('/api/navigation/route')
    def route(body: RouteRequest, request: Request):
        user = actor(request)
        if body.destination is not None:
            return compute(user, body.origin, body.destination, 'entered_address')
        with connect() as db:
            if body.assignment_id:
                if not accounts or user['edition'] != 'enterprise':
                    raise HTTPException(403, 'Assigned navigation requires Enterprise access')
                row = db.execute("""SELECT p.payload FROM dispatch_assignments a
                    JOIN dispatch_plans p ON p.id=a.plan_id AND p.organization_id=a.organization_id
                    WHERE a.id=? AND a.organization_id=? AND a.user_id=?
                    AND a.status IN ('sent','accepted') AND p.status='sent'""",
                    (str(body.assignment_id), user['organization_id'], user['id'])).fetchone()
                if not row:
                    raise HTTPException(404, 'Assignment not available for this user')
                try:
                    details = json.loads(row['payload']).get('delivery_snapshot', {})
                except (ValueError, AttributeError):
                    raise HTTPException(409, 'Confirm the dispatched job destination before routing') from None
                basis = 'dispatched_snapshot'
            else:
                row = permitted_row(db, str(body.order_id), user)
                try:
                    details = json.loads(row['payload'])
                except ValueError:
                    raise HTTPException(409, 'Confirm the job destination before routing') from None
                basis = 'work_order'
            destination = details.get('address') if isinstance(details, dict) else None
            if not isinstance(destination, str) or not destination.strip() or len(destination) > 500:
                raise HTTPException(409, 'Save or confirm the job destination before routing')
            destination = destination.strip()
        return compute(user, body.origin, destination, basis)

    def compute(user, origin, destination, basis):
        if not provider.enabled:
            return provider.compute(origin, destination)
        limit(user)
        if not concurrent.acquire(blocking=False):
            raise HTTPException(429, 'Routing is busy. Try again shortly.')
        try:
            return {**provider.compute(origin, destination), 'destination': destination,
                    'destination_basis': basis}
        finally:
            concurrent.release()
