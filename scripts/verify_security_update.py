"""Read-only comparison of staged revision metadata; never prints private env."""
import copy
import json
import sys
from pathlib import Path


def main():
    p=Path(sys.argv[1]); image=sys.argv[2]
    before=json.loads((p/'before-service.json').read_text())
    after=json.loads((p/'candidate-service.json').read_text())
    allowed={'WZOS_SCANNER_URL':'https://wzos-v2-scanner-udtvm4rgca-uc.a.run.app', 'WZOS_FILE_SCAN_REQUIRED':'1'}
    expected={'security-fallback-1016':'us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:ef31216bc772a0233b7c59a9e219dcd9b17f6c6f2c8ed058270a9a009676ab9d',
              'security-update-1016':image}
    old=copy.deepcopy(before['spec']['template']['spec'])
    for suffix, wanted in expected.items():
        name='wzos-v2-accounts-'+suffix
        revision=json.loads((p/(name+'.json')).read_text())
        assert revision['metadata']['name']==name
        assert revision['status']['imageDigest']==wanted
        assert any(c['type']=='Ready' and c['status']=='True' for c in revision['status']['conditions'])
        spec=copy.deepcopy(revision['spec']); new=spec['containers'][0]; prior=old['containers'][0]
        assert new['image']==wanted
        new['image']=prior['image']
        env={v['name']:v for v in new.get('env',[])}
        prior_env={v['name']:v for v in prior.get('env',[])}
        for key,value in allowed.items():
            assert env[key]=={'name':key,'value':value}
            env.pop(key)
            prior_env.pop(key,None)
        assert env==prior_env,'Unapproved environment/secret binding change'
        new['env']=prior.get('env',[])
        # Revision API may include service-level defaults in metadata, not spec.
        assert spec==old,'Unapproved runtime resources/identity/SQL configuration'
    for key in ('run.googleapis.com/ingress','run.googleapis.com/invoker-iam-disabled'):
        assert before['metadata'].get('annotations',{}).get(key)==after['metadata'].get('annotations',{}).get(key)
    ignored={'run.googleapis.com/client-name','run.googleapis.com/client-version','run.googleapis.com/operation-id'}
    def annotations(x):
        return {k:v for k,v in x['spec']['template']['metadata'].get('annotations',{}).items() if k not in ignored}
    assert annotations(before)==annotations(after),'Unexpected autoscaling/SQL annotation change'
    assert [(t.get('revisionName'),t.get('percent')) for t in after['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-hub-5a3ac86',100)]
    print('SECURITY_UPDATE_STAGED_PASS_CONFIGURATION_PRESERVED_NO_TRAFFIC')


if __name__=='__main__':
    main()
