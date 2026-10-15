"""Operator preflight must accept auth-check's plain response without leaking tokens."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.error

spec=importlib.util.spec_from_file_location('hf_check',Path(__file__).resolve().parents[1]/'scripts/check_huggingface_access.py')
check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)
TOKEN='hf_syntheticPlaceholder12345'

class Reply:
    status=200
    def __init__(self,body):self.body=body
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,*args):return self.body

class AccessChecks(unittest.TestCase):
    def run_check(self,model):
        identity=Reply(b'{"auth":{"accessToken":{"role":"fineGrained"}}}')
        client=SimpleNamespace(open=None)
        from unittest.mock import Mock
        client.open=Mock(side_effect=[identity,model])
        out=io.StringIO()
        with patch.object(check.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=TOKEN.encode())) as proc,patch.object(check.urllib.request,'build_opener',return_value=client),patch('sys.argv',['check','--secret','HF_TOKEN']),contextlib.redirect_stdout(out):
            code=check.main()
        self.assertNotIn(TOKEN,out.getvalue())
        self.assertNotIn(TOKEN,str(proc.call_args))
        self.assertEqual(client.open.call_args_list[1].args[0].full_url,'https://huggingface.co/api/models/google/gemma-4-31B-it/auth-check')
        return code,json.loads(out.getvalue())
    def test_plain_auth_success(self):
        code,data=self.run_check(Reply(b'Access is authorized'))
        self.assertEqual(code,0);self.assertTrue(data['token_valid']);self.assertEqual(data['model_access_http_status'],200)
    def test_denied_model_is_not_credential_success(self):
        code,data=self.run_check(urllib.error.HTTPError('https://huggingface.co',403,'Forbidden',{},None))
        self.assertEqual(code,1);self.assertTrue(data['token_valid']);self.assertEqual(data['model_access_http_status'],403)

if __name__=='__main__':unittest.main()
