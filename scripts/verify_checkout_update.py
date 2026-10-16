"""Compare staged checkout revisions without printing secrets or changing traffic."""
import copy
import json
import sys
from pathlib import Path


def main():
    p=Path(sys.argv[1]);load=lambda n:json.loads((p/n).read_text())
    before=load('before-service.json');after=load('checkout-staged-service.json')
    image='us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:53f9348a618430d823067748ce0958ef084b6d73565780ffcb4a1195dda76a22'
    additions={'WZOS_SCANNER_URL':'https://wzos-v2-scanner-udtvm4rgca-uc.a.run.app',
        'WZOS_FILE_SCAN_REQUIRED':'1','WZOS_COMMERCE_ENABLED':'1',
        'WZOS_STRIPE_MODE':'live','WZOS_STRIPE_TAX_VERIFIED':'1'}
    bindings={'WZOS_STRIPE_API_KEY':('wzos-v2-stripe-api-keY','3'),
        'WZOS_STRIPE_WEBHOOK_SECRET':('wzos-v2-stripe-webhook-secret','1'),
        'WZOS_PURCHASE_ENCRYPTION_KEY':('wzos-v2-purchase-encryption-key','1')}
    original=before['spec']['template']['spec']
    for mode,pause in [('hold','1'),('live','0')]:
        revision=load('checkout-'+mode+'-revision.json')
        assert revision['metadata']['name']=='wzos-v2-accounts-checkout-'+mode+'-1016'
        assert revision['status']['imageDigest']==image
        assert any(c['type']=='Ready' and c['status']=='True' for c in revision['status']['conditions'])
        spec=copy.deepcopy(revision['spec']);container=spec['containers'][0];prior=original['containers'][0]
        assert container['image']==image
        container['image']=prior['image']
        env={e['name']:e for e in container.get('env',[])}
        expected={e['name']:e for e in prior.get('env',[])}
        for name,value in {**additions,'WZOS_COMMERCE_CHECKOUT_PAUSED':pause}.items():
            assert env.pop(name)=={'name':name,'value':value}
            expected.pop(name,None)
        for name,(secret,version) in bindings.items():
            assert env.pop(name)=={'name':name,'valueFrom':{'secretKeyRef':{'name':secret,'key':version}}}
            expected.pop(name,None)
        assert env==expected,'Unapproved environment or secret change'
        container['env']=prior.get('env',[])
        assert spec==original,'Unapproved identity/resources/runtime configuration'
    for key in ('run.googleapis.com/ingress','run.googleapis.com/invoker-iam-disabled'):
        assert before['metadata'].get('annotations',{}).get(key)==after['metadata'].get('annotations',{}).get(key)
    ignored={'run.googleapis.com/client-name','run.googleapis.com/client-version','run.googleapis.com/operation-id'}
    annotations=lambda x:{k:v for k,v in x['spec']['template']['metadata'].get('annotations',{}).items() if k not in ignored}
    assert annotations(before)==annotations(after),'Unexpected autoscaling/SQL change'
    assert [(t.get('revisionName'),t.get('percent')) for t in after['status']['traffic'] if t.get('percent')]==[('wzos-v2-accounts-hub-5a3ac86',100)]
    print('CHECKOUT_STAGED_PASS_CONFIG_PRESERVED_NO_TRAFFIC')


if __name__=='__main__':
    main()
