"""Operator-only private invocation preflight. No writes, generation, or retries."""
import argparse
import base64
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

PROJECT = 'enterprise-gemma2'
REGION = 'us-central1'
APP = 'wzos-v2-accounts'
MODEL = 'wzos-atlas-inference'
CALLER = f'{APP}@{PROJECT}.iam.gserviceaccount.com'


def gc(*args):
    result = subprocess.run(['gcloud', *args, '--project', PROJECT, '--quiet'],
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        # gcloud stderr can contain identity or token details; never echo it.
        raise RuntimeError('gcloud_failed')
    return result.stdout.strip()


def inspect(app, model, policy):
    errors = []
    for name, service in [('app', app), ('model', model)]:
        status = service.get('status', {})
        if not any(c.get('type') == 'Ready' and c.get('status') == 'True'
                   for c in status.get('conditions', [])):
            errors.append(name + '_not_ready')
        revision = status.get('latestReadyRevisionName')
        traffic = status.get('traffic', [])
        if not revision or not any(t.get('revisionName') == revision and
                                   t.get('percent') == 100 for t in traffic):
            errors.append(name + '_traffic_not_latest_ready')
        if revision != status.get('latestCreatedRevisionName'):
            errors.append(name + '_pending_revision')
    spec = app.get('spec', {}).get('template', {}).get('spec', {})
    if spec.get('serviceAccountName') != CALLER:
        errors.append('unexpected_caller')
    containers = spec.get('containers', [])
    env = {e['name']: e.get('value') for e in containers[0].get('env', [])} if containers else {}
    origin = model.get('status', {}).get('url', '')
    # Reuse the adapter's strict HTTPS Cloud Run origin validation.
    from services.workspace_preview.cloud_intelligence import service_url
    try:
        if service_url(origin) != origin or env.get('WZOS_ATLAS_VLLM_URL') != origin:
            errors.append('audience_target_mismatch')
    except (ValueError, RuntimeError):
        errors.append('invalid_target')
    annotations = model.get('metadata', {}).get('annotations', {})
    if annotations.get('run.googleapis.com/invoker-iam-disabled', 'false') != 'false':
        errors.append('invoker_check_disabled')
    bindings = policy.get('bindings', [])
    if any(set(b.get('members', [])) & {'allUsers', 'allAuthenticatedUsers'} for b in bindings):
        errors.append('public_policy_binding')
    if not any(b.get('role') == 'roles/run.invoker' and not b.get('condition') and
               f'serviceAccount:{CALLER}' in b.get('members', []) for b in bindings):
        errors.append('missing_unconditional_invoker_binding')
    return {'configuration_passed': not errors, 'errors': errors,
            'caller': CALLER, 'audience': origin, 'atlas_enabled': env.get('WZOS_ATLAS_VLLM_ENABLED'),
            'private_invocation_verified': False, 'inference_accepted': False}


def probe(report):
    if not report['configuration_passed']:
        return
    report['probe_identity_method'] = 'operator_impersonation_not_runtime_metadata'
    token = gc('auth', 'print-identity-token', '--impersonate-service-account', CALLER,
               '--audiences', report['audience'], '--include-email')
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError('invalid_token')
    claims = json.loads(base64.urlsafe_b64decode(parts[1] + '=' * (-len(parts[1]) % 4)))
    if claims.get('aud') != report['audience'] or claims.get('email') != CALLER or \
            not isinstance(claims.get('exp'), (int, float)) or claims['exp'] < time.time() + 330:
        raise ValueError('token_claim_mismatch')
    # Cloud Run validates the signature. Local claim checks only catch mistakes.
    started = time.monotonic()
    with httpx.Client(timeout=httpx.Timeout(300, connect=15), follow_redirects=False,
                      trust_env=False) as client:
        with client.stream('GET', report['audience'] + '/health',
                           headers={'Authorization': 'Bearer ' + token}) as response:
            report['probe_http_status'] = response.status_code
            report['private_invocation_verified'] = response.status_code == 200
    report['probe_seconds'] = round(time.monotonic() - started, 3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--probe-with-active-budget-guard', action='store_true',
                        help='One GET /health; may start billable GPU. Requires an independently active cleanup guard.')
    args = parser.parse_args()
    report = {'started_at': datetime.now(timezone.utc).isoformat(),
              'configuration_passed': False, 'private_invocation_verified': False,
              'inference_accepted': False}
    stage = 'configuration'
    try:
        app = json.loads(gc('run', 'services', 'describe', APP, '--region', REGION, '--format=json'))
        model = json.loads(gc('run', 'services', 'describe', MODEL, '--region', REGION, '--format=json'))
        policy = json.loads(gc('run', 'services', 'get-iam-policy', MODEL, '--region', REGION, '--format=json'))
        report.update(inspect(app, model, policy))
        if args.probe_with_active_budget_guard:
            stage = 'identity_or_health_probe'
            probe(report)
    except Exception as exc:
        report['failure_stage'] = stage
        report['failure_type'] = type(exc).__name__
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
    passed = report['configuration_passed'] and 'failure_stage' not in report
    if args.probe_with_active_budget_guard:
        passed = passed and report['private_invocation_verified']
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
