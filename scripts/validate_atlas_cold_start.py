"""Operator-only, one-request cold-start observation; never provisions or retries.

Requires fresh explicit zero-instance metrics. Missing/stale metrics fail closed.
Successful HTTP is provisional until startup logs establish a new instance during
the request. Run with the existing trial budget and independent cleanup guard.
"""
import argparse
from datetime import datetime, timezone, timedelta
import json
import math
from pathlib import Path
import time
from uuid import uuid4

import requests

try:
    from .validate_managed_accounts import gc, ORIGIN, SERVICE, PROJECT
    from .validate_atlas_grounding_staging import require_token_lifetime
except ImportError:
    from validate_managed_accounts import gc, ORIGIN, SERVICE, PROJECT
    from validate_atlas_grounding_staging import require_token_lifetime

MODEL_SERVICE = 'wzos-atlas-inference'
METRIC = 'run.googleapis.com/container/instance_count'


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timezone required')
    return parsed


def zero_observation(data, revision, now):
    """Require two matching zero samples for both active and idle states.

    Deliberately conservative: absence is unknown, not zero. No aggregation hides
    nonzero state/revision samples. Monitoring lag still requires log correlation.
    """
    if data.get('nextPageToken'):
        raise ValueError('Incomplete metric pages')
    states = {}
    for series in data.get('timeSeries', []):
        labels = series.get('resource', {}).get('labels', {})
        if (series.get('resource', {}).get('type') != 'cloud_run_revision'
                or labels.get('project_id') != PROJECT
                or labels.get('service_name') != MODEL_SERVICE
                or labels.get('revision_name') != revision
                or series.get('metric', {}).get('type') != METRIC):
            raise ValueError('Unexpected metric scope')
        state = series['metric'].get('labels', {}).get('state')
        if state not in ('active', 'idle') or state in states:
            raise ValueError('Unexpected or duplicate state')
        points = sorted(series.get('points', []), key=lambda p: timestamp(p['interval']['endTime']), reverse=True)
        if len(points) < 2:
            raise ValueError('Two explicit samples required')
        samples = []
        for point in points[:2]:
            stamp = timestamp(point['interval']['endTime'])
            value = point.get('value', {}).get('int64Value')
            if value not in ('0', 0) or isinstance(value, bool):
                raise ValueError('Instances are nonzero or unknown')
            age = (now-stamp).total_seconds()
            if not math.isfinite(age) or not 0 <= age <= 240:
                raise ValueError('Metric is stale or future dated')
            samples.append(stamp)
        if not 45 <= (samples[0]-samples[1]).total_seconds() <= 90:
            raise ValueError('Samples are not consecutive minutes')
        states[state] = samples
    if set(states) != {'active', 'idle'} or states['active'] != states['idle']:
        raise ValueError('Both states need matching explicit zero samples')
    return {'revision': revision, 'sample_times': [t.isoformat() for t in states['active']],
            'observed_at': now.isoformat(), 'active': 0, 'idle': 0,
            'startup_log_correlation_required': True}


def run(state, output):
    if state.get('disabled'):
        raise ValueError('Active disposable fixtures required')
    # Refuse an existing output before accessing any provider.
    with output.open('x', encoding='utf-8') as evidence:
        def record(stage, **values):
            row = {'stage': stage, **values}
            evidence.write(json.dumps(row)+'\n'); evidence.flush()
            print(json.dumps(row), flush=True)
        iam = gc('auth', 'print-identity-token')
        member = state['users']['member']['idToken']
        require_token_lifetime(iam, 'Operator', minimum=600)
        require_token_lifetime(member, 'Synthetic member', minimum=600)
        model = json.loads(gc('run', 'services', 'describe', MODEL_SERVICE,
                             '--region=us-central1', '--format=json'))
        revision = model['status']['latestReadyRevisionName']
        traffic = model['status'].get('traffic', [])
        if any(t.get('percent', 0) and t.get('revisionName') != revision for t in traffic):
            raise ValueError('Split revision traffic is not supported by this test')
        app_url = gc('run', 'services', 'describe', SERVICE, '--region=us-central1', '--format=value(status.url)')
        with requests.Session() as client:
            client.trust_env = False
            client.headers['X-Serverless-Authorization'] = 'Bearer '+iam
            config = client.get(app_url+'/api/identities', timeout=30, allow_redirects=False)
            config.raise_for_status()
            header = config.json()['auth_header']
            if header not in ('Authorization', 'X-WZOS-Authorization'):
                raise ValueError('Unexpected auth header')
            client.headers.update({header: 'Bearer '+member,
                                   'X-WZOS-Organization': state['orgs']['main'], 'Origin': ORIGIN})
            # Control-plane monitoring only: never call model readiness to warm it.
            now = datetime.now(timezone.utc)
            metric = requests.get('https://monitoring.googleapis.com/v3/projects/'+PROJECT+'/timeSeries',
                headers={'Authorization': 'Bearer '+gc('auth', 'print-access-token')},
                params={'filter': f'metric.type="{METRIC}" AND resource.labels.service_name="{MODEL_SERVICE}" AND resource.labels.revision_name="{revision}"',
                        'interval.startTime': (now-timedelta(minutes=6)).isoformat(),
                        'interval.endTime': now.isoformat(), 'pageSize': 1000}, timeout=30)
            metric.raise_for_status()
            record('zero_preflight', **zero_observation(metric.json(), revision, datetime.now(timezone.utc)))
            rid = str(uuid4())
            record('request_start', request_id=rid, utc=datetime.now(timezone.utc).isoformat())
            started = time.monotonic()
            try:
                reply = client.post(app_url+'/api/assistant/chat', timeout=310, allow_redirects=False,
                    json={'request_id': rid, 'page': 'work_orders',
                          'question': 'Explain uncertainty in a synthetic job with missing site dimensions. Do not invent facts.'})
                try:
                    body = reply.json()
                except ValueError:
                    body = {}
                if not isinstance(body, dict):
                    body = {}
                passed = (reply.status_code == 200 and body.get('model_called') is True
                          and body.get('actions_performed') == [] and body.get('approved_for_field_use') is False)
                record('request_result', http_status=reply.status_code, seconds=round(time.monotonic()-started,3),
                       utc=datetime.now(timezone.utc).isoformat(), response_validated=passed,
                       cold_start_accepted=False, startup_log_correlation_required=True)
                if not passed:
                    raise RuntimeError('Cold request failed; no automatic retry')
            except requests.RequestException as error:
                record('transport_failure', error_type=type(error).__name__, seconds=round(time.monotonic()-started,3))
                try:
                    cancelled = client.post(app_url+'/api/assistant/requests/'+rid+'/cancel', timeout=10, allow_redirects=False)
                    record('cleanup_cancel', http_status=cancelled.status_code)
                except requests.RequestException:
                    record('cleanup_cancel', confirmed=False)
                raise RuntimeError('Request transport failed; inspect sanitized evidence') from None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(json.loads(args.state.read_text()), args.output)
