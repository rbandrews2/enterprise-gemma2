"""Build Core/Enterprise sample journeys through local APIs in a NEW directory.

Requires development dependencies. Never imports legacy users or calls providers.
Existing destinations and cloud/account runtime configuration are refused.
"""
import argparse
import json
import os
from pathlib import Path
import sys
from uuid import NAMESPACE_URL, uuid5

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def build(destination):
    if any(os.getenv(k) for k in ('K_SERVICE', 'GAE_ENV', 'NETLIFY', 'WZOS_ACCOUNT_WORKSPACE', 'WZOS_ATLAS_LOCAL_MODEL')):
        raise RuntimeError('Use a separate local synthetic environment')
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    from services.workspace_preview.app import create_app, CHECKLIST_ITEMS
    from services.v2.knowledge.store import Store

    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    manifest = {'synthetic': True, 'status': 'building', 'scenarios': [],
                'limitations': ['No live AI, agency ingestion, Maps, external delivery or field approval.',
                                'Synthetic identities are not production authentication.']}
    def uid(label):
        return str(uuid5(NAMESPACE_URL, 'wzos-demo-v1/' + label))
    with patch.dict(os.environ, {'WZOS_WORKSPACE_PREVIEW': '1'}):
        app = create_app(destination/'orders.sqlite', Store(destination/'sources', {}))
        with TestClient(app) as client:
            def call(method, path, actor, data=None):
                response = client.request(method, path, headers={'X-Preview-Actor': actor}, json=data)
                if response.status_code not in (200, 201):
                    raise RuntimeError(f'{method} {path}: {response.status_code}: {response.text}')
                return response.json()
            for edition, city, work in [('core', 'Richmond', 'road_maintenance'), ('enterprise', 'Norfolk', 'line_striping')]:
                member, admin = edition+'-general', edition+'-admin'
                job = call('POST', '/api/orders', member, {
                    'request_id': uid(edition+'/order'), 'title': city+' demonstration work zone',
                    'work_type': work, 'address': 'Synthetic example site, '+city+', VA', 'locality': city,
                    'work_date': '2026-09-30', 'notes': 'Artificial acceptance scenario. Not a field plan.',
                    'site': {'speed_limit_mph': 35.0, 'lane_count': 2, 'work_period': 'day'}})
                order = job['id']
                form = uid(edition+'/form')
                call('PUT', '/api/modules/forms/'+form, member, {
                    'request_id': uid(edition+'/form-save'), 'title': 'Demo pre-task planning',
                    'form_type': 'jsa', 'order_id': order,
                    'safety': {'tasks': 'Review the sample site', 'hazards': 'Unverified traffic and site conditions',
                               'controls': 'Obtain qualified review before field use'}})
                call('PUT', '/api/modules/schedule/'+uid(edition+'/schedule'), admin, {
                    'request_id': uid(edition+'/schedule-save'), 'title': 'Demo crew briefing',
                    'order_id': order, 'assignees': [member],
                    'start': '2026-09-30T12:00:00Z', 'end': '2026-09-30T13:00:00Z'})
                call('POST', '/api/messages', admin, {'request_id': uid(edition+'/message'),
                    'recipient_id': member, 'text': 'Demo only: review the saved job and planning worksheet.'})
                courses = call('GET', '/api/training', member)['items']
                call('PUT', '/api/training/'+courses[0]['id'], member, {'status': 'studying'})
                # Fixed synthetic timestamps make attendance evidence reproducible.
                with patch('services.workspace_preview.timeclock.utc_now', return_value='2026-09-30T12:00:00+00:00'):
                    shift = call('POST', '/api/time/commands', member, {'request_id': uid(edition+'/clock-in'),
                        'action': 'clock_in', 'task': 'setup', 'order_id': order})['entry']
                with patch('services.workspace_preview.timeclock.utc_now', return_value='2026-09-30T13:00:00+00:00'):
                    call('POST', '/api/time/commands', member, {'request_id': uid(edition+'/clock-out'),
                        'action': 'clock_out', 'shift_id': shift['id'], 'expected_version': shift['version']})
                scenario = {'edition': edition, 'member': member, 'admin': admin, 'order_id': order, 'form_id': form}
                if edition == 'enterprise':
                    call('PUT', '/api/orders/'+order+'/checklist', member, {
                        'expected_version': 0, 'expected_order_version': 1,
                        'items': {k: {'status': 'needs_attention', 'notes': 'Demonstration: verification pending.'} for k in CHECKLIST_ITEMS}})
                    scenario['report_id'] = call('POST', '/api/orders/'+order+'/reports', member,
                        {'request_id': uid('enterprise/report'), 'expected_order_version': 1})['id']
                manifest['scenarios'].append(scenario)
    manifest['status'] = 'complete'
    (destination/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print(f"Built {len(result['scenarios'])} synthetic journeys in {args.output}")
