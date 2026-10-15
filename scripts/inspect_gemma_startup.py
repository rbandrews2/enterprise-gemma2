"""Read-only diagnostics. Never emit env values, secret payloads or unredacted tokens."""
import json
import re
import subprocess


def run(args):
    r=subprocess.run(['gcloud',*args,'--project=enterprise-gemma2','--format=json'],capture_output=True,timeout=60)
    if r.returncode:
        raise SystemExit('DIAGNOSTIC_READ_FAILED: '+args[0])
    return json.loads(r.stdout)


def redact(value):
    text=str(value)
    text=re.sub(r'hf_[A-Za-z0-9]{8,}|AIza[A-Za-z0-9_-]{20,}', '[REDACTED]', text)
    text=re.sub(r'(?i)(bearer\s+)[^\s\"\']+', r'\1[REDACTED]', text)
    text=re.sub(r'(?i)((?:api[_-]?key|password|(?:hf_)?token|secret)\s*[=:]\s*)[^\s,}]+',r'\1[REDACTED]',text)
    return text


def main():
    revision=run(['run','revisions','describe','gemma-inference-00007-njh','--region=us-central1'])
    spec=revision.get('spec',{})
    selected={'revision':revision.get('metadata',{}).get('name'),
        'service_account':spec.get('serviceAccountName'),
        'conditions':revision.get('status',{}).get('conditions'),
        'annotations':{k:v for k,v in revision.get('metadata',{}).get('annotations',{}).items() if any(x in k for x in ('accelerator','minScale','maxScale','cpu-throttling'))},
        'containers':[]}
    for c in spec.get('containers',[]):
        selected['containers'].append({'image':c.get('image'),'command':redact(c.get('command',[])),
            'args':redact(c.get('args',[])), 'ports':c.get('ports'), 'resources':c.get('resources'),
            'startupProbe':c.get('startupProbe'),
            'env_names':[e['name'] for e in c.get('env',[])],
            'secret_bindings':{e['name']:e['valueFrom'] for e in c.get('env',[]) if e.get('valueFrom')}})
    print(json.dumps(selected,indent=2))
    rows=run(['logging','read','resource.type="cloud_run_revision" AND resource.labels.service_name="gemma-inference" AND resource.labels.revision_name="gemma-inference-00007-njh"', '--limit=60','--order=asc','--freshness=30d'])
    for row in rows:
        message=row.get('textPayload') or row.get('jsonPayload',{}).get('message') or row.get('jsonPayload',{}).get('msg')
        if message:
            print(redact(message)[:3000])


if __name__=='__main__':
    main()
