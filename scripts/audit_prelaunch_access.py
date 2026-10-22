"""Read WZOS runtime access metadata, never secret payloads or IAM mutations.

Run in the already authorized enterprise-gemma2 Cloud Shell. Private raw policy
snapshots remain outside Git; stdout contains only a compact summary.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

PROJECT = 'enterprise-gemma2'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    args = parser.parse_args()
    root = args.evidence
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(root, 0o700)
    def capture(name, arguments):
        result = subprocess.run(['gcloud', *arguments, '--quiet', '--format=json'],
                                capture_output=True, text=True, timeout=90)
        (root/(name+'.exit')).write_text(str(result.returncode))
        (root/(name+'.stderr')).write_text(result.stderr)
        if result.returncode:
            return None
        data = json.loads(result.stdout)
        (root/(name+'.json')).write_text(json.dumps(data, indent=2))
        return data
    project = subprocess.check_output(['gcloud', 'config', 'get-value', 'project'], text=True).strip()
    if project != PROJECT:
        raise SystemExit('Wrong active project; nothing inspected.')
    service = capture('app', ['run', 'services', 'describe', 'wzos-v2-accounts',
                            '--project='+PROJECT, '--region=us-central1'])
    if service is None:
        raise SystemExit('Runtime metadata unavailable; inspect app.stderr.')
    spec = service['spec']['template']['spec']
    identity = spec['serviceAccountName']
    member = 'serviceAccount:'+identity
    project_policy = capture('project-policy', ['projects', 'get-iam-policy', PROJECT])
    def roles(policy):
        if policy is None:
            return None
        return [{'role': b['role'], 'conditional': bool(b.get('condition'))}
                for b in policy.get('bindings', []) if member in b.get('members', [])]
    # Names and pinned version identifiers only. No `versions access` command.
    refs = {}
    for container in spec.get('containers', []):
        for env in container.get('env', []):
            ref = env.get('valueFrom', {}).get('secretKeyRef')
            if ref:
                refs.setdefault(ref['name'], set()).add(ref['key'])
    secret_rows = []
    for index, (name, versions) in enumerate(sorted(refs.items())):
        policy = capture('secret-policy-'+str(index), ['secrets', 'get-iam-policy', name,
                                                     '--project='+PROJECT])
        secret_rows.append({'secret': name, 'versions': sorted(versions),
                            'direct_runtime_roles': roles(policy)})
    bucket_name = next((e.get('value') for c in spec['containers'] for e in c.get('env', [])
                        if e['name'] == 'WZOS_FILES_BUCKET'), None)
    bucket_policy = None
    if bucket_name:
        bucket_policy = capture('bucket-policy', ['storage', 'buckets', 'get-iam-policy',
                                                  'gs://'+bucket_name])
    ancestors = capture('ancestors', ['projects', 'get-ancestors', PROJECT])
    inherited = []
    for resource in ancestors or []:
        kind, resource_id = resource.get('type'), resource.get('id')
        if kind in ('organization', 'folder'):
            command = ['organizations', 'get-iam-policy'] if kind == 'organization' else ['resource-manager', 'folders', 'get-iam-policy']
            policy = capture('ancestor-'+kind+'-'+resource_id, [*command, resource_id])
            inherited.append({'type': kind, 'direct_runtime_roles': roles(policy)})
    summary = {'runtime': identity, 'project_roles': roles(project_policy),
               'secret_bindings': secret_rows, 'bucket_direct_roles': roles(bucket_policy),
               'ancestor_direct_roles': inherited,
               'limitations': 'Direct principal bindings only; groups, resource-specific roles, conditions and deny policies need separate interpretation.'}
    (root/'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
