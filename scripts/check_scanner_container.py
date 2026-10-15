"""Harmless acceptance inside a disposable scanner container, without IAM tokens."""
import io
import json
import os
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from services.workspace_preview.clamd_scanner import ClamdScanner
from services.workspace_preview.scanner_runtime import SupervisedScanner

roots = list(Path('/tmp').glob('wzos-scanner-runtime-*'))
assert len(roots) == 1
root = roots[0]
os.environ.update(WZOS_CLAMD_SOCKET=str(root/'clamd.sock'), WZOS_CLAMD_CONFIG=str(root/'clamd.conf'))
scanner = ClamdScanner()
clean = scanner.scan(b'%PDF-1.7\nSynthetic acceptance only\n%%EOF\n')
assert clean.status == 'clean'
fixture = b'X5O!P%@AP[4'+b'\\PZX54(P^)7CC)7}'+b'$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
assert scanner.scan(fixture).status == 'infected'
packed=io.BytesIO()
with zipfile.ZipFile(packed,'w',zipfile.ZIP_DEFLATED) as archive:
    archive.writestr('synthetic-limit.txt', b'0'*(11*1024*1024))
assert scanner.scan(packed.getvalue()).status == 'error'
try:
    urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8080/scan',data=b'synthetic'),timeout=3)
    raise AssertionError('Missing service identity accepted')
except urllib.error.HTTPError as error:
    assert error.code == 401
os.environ['WZOS_SCANNER_INSTANCE_DEADLINE']='1'
assert SupervisedScanner().scan(b'synthetic').status == 'error'
print(json.dumps({'clean':'clean','safe_detection_fixture':'infected','expanded_limit':'error',
                  'missing_identity':401,'expired_worker':'error','engine':clean.engine}))
