"""Read model object metadata only; never download weights or start inference."""
import json
import subprocess
import urllib.parse
import urllib.request


LOCATIONS = (
    ('vertex-model-garden-public-us', 'gemma4/gemma-4-31B-it/'),
    ('enterprise-gemma2-atlas-models-us-central1', 'gemma-4-31B-it/'),
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def inventory(opener, token, bucket, prefix):
    query = urllib.parse.urlencode({'prefix': prefix, 'maxResults': 100,
                                  'fields': 'items(name,size,crc32c,generation),nextPageToken'})
    url = f'https://storage.googleapis.com/storage/v1/b/{bucket}/o?{query}'
    request = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token})
    with opener.open(request, timeout=30) as response:
        payload = response.read(65537)
    if len(payload) > 65536:
        raise ValueError('Metadata too large')
    data = json.loads(payload)
    if data.get('nextPageToken'):
        raise ValueError('Unexpected inventory size')
    result = {}
    for item in data.get('items', []):
        name = item['name'][len(prefix):]
        if not name:  # Ignore a zero-byte directory marker, never model objects.
            continue
        if not item['name'].startswith(prefix) or name in result:
            raise ValueError('Unexpected object name')
        result[name] = {k: item[k] for k in ('size', 'crc32c', 'generation')}
    return result


def main():
    token = subprocess.run(['gcloud', 'auth', 'print-access-token',
                            '--project=enterprise-gemma2'], capture_output=True,
                           check=True, timeout=30).stdout.decode().strip()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    source, copied = [inventory(opener, token, *location) for location in LOCATIONS]
    matches = (len(source) == 10 and source.keys() == copied.keys() and
               all((v['size'], v['crc32c']) == (copied[k]['size'], copied[k]['crc32c'])
                   for k, v in source.items()))
    print(json.dumps({'checksums_match': matches, 'objects': len(copied),
                      'bytes': sum(int(v['size']) for v in copied.values()),
                      'source': source, 'copied': copied}, sort_keys=True))
    return 0 if matches else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        # Never emit subprocess/HTTP exceptions that might include credentials.
        print(json.dumps({'checksums_match': False, 'error_type': type(error).__name__}))
        raise SystemExit(2)
