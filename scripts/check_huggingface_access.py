"""Operator-only HF access check. No token output/cache, model download or inference."""
import argparse
import json
import re
import subprocess
import urllib.error
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--secret', required=True)
    parser.add_argument('--version', default='latest')
    parser.add_argument('--repo', default='google/gemma-4-31B-it')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,255}', args.secret):
        raise SystemExit('Invalid secret name')
    if not re.fullmatch(r'latest|[1-9][0-9]*', args.version):
        raise SystemExit('Invalid secret version')
    if not re.fullmatch(r'google/[A-Za-z0-9_.-]+', args.repo):
        raise SystemExit('Only an explicit Google model repository is allowed')
    try:
        result = subprocess.run(['gcloud', 'secrets', 'versions', 'access', args.version,
            '--secret='+args.secret, '--project=enterprise-gemma2', '--quiet'],
            capture_output=True, timeout=30, check=False)
        if result.returncode:
            raise SystemExit('HF_CHECK: Secret access unavailable; no permission changed')
        token = result.stdout.decode('ascii').strip()
        if not re.fullmatch(r'hf_[A-Za-z0-9]{10,200}', token):
            raise SystemExit('HF_CHECK: Secret is not in the expected Hugging Face token format')
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        def get(path):
            request = urllib.request.Request('https://huggingface.co'+path,
                headers={'Authorization':'Bearer '+token, 'Accept':'application/json'})
            try:
                with opener.open(request, timeout=15) as response:
                    payload = response.read(65537)
                    if len(payload)>65536:
                        return response.status, {}
                    return response.status, json.loads(payload or '{}')
            except urllib.error.HTTPError as error:
                return error.code, {}
        status, identity = get('/api/whoami-v2')
        output = {'token_valid':status==200, 'identity_http_status':status}
        if status==200:
            role=identity.get('auth',{}).get('accessToken',{}).get('role')
            output['token_role']=role if role in ('read','write','fineGrained') else 'not_reported'
            output['model_repo']=args.repo
            output['model_access_http_status']=get('/api/models/'+args.repo+'/auth-check')[0]
        print(json.dumps(output,sort_keys=True))
        return 0 if output.get('model_access_http_status')==200 else 1
    except (OSError, ValueError, subprocess.TimeoutExpired):
        raise SystemExit('HF_CHECK: Verification unavailable; no token or provider response disclosed')


if __name__=='__main__':
    raise SystemExit(main())
