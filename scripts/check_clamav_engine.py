#!/usr/bin/env python3
"""Explicit Linux-only real-engine acceptance. No customer files or public service.

Requires operator-installed clamd and current official databases. Starts only an
owned foreground daemon; stops it even if any assertion fails. EICAR is the
standard harmless antivirus test fixture, assembled in memory, never executed.
"""
import argparse
import io
import json
import os
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from services.workspace_preview.clamd_scanner import ClamdScanner, daemon_config


def main():
    def interrupted(_signal, _frame):
        raise SystemExit('ENGINE_GATE_BLOCKED: interrupted; stopping owned daemon')
    signal.signal(signal.SIGTERM, interrupted)
    parser=argparse.ArgumentParser()
    parser.add_argument('--database-dir',required=True)
    parser.add_argument('--evidence-dir',required=True)
    parser.add_argument('--certs-dir')
    args=parser.parse_args()
    binary=shutil.which('clamd')
    if os.name!='posix' or not binary:
        raise SystemExit('ENGINE_GATE_BLOCKED: Linux clamd installation required')
    database=Path(args.database_dir).resolve()
    if not any(database.glob('*.c?d')):
        raise SystemExit('ENGINE_GATE_BLOCKED: official signature database missing')
    evidence=Path(args.evidence_dir).resolve(); evidence.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='wzos-clamd-',dir='/tmp') as work:
        root=Path(work); endpoint=root/'clamd.sock'; config=root/'clamd.conf'
        certs=Path(args.certs_dir).resolve() if args.certs_dir else None
        config.write_text(daemon_config(endpoint,database,certs),encoding='utf-8'); config.chmod(0o600)
        env={**os.environ,'TZ':'UTC','WZOS_CLAMD_SOCKET':str(endpoint),'WZOS_CLAMD_CONFIG':str(config)}
        os.environ.update({key:env[key] for key in ['TZ','WZOS_CLAMD_SOCKET','WZOS_CLAMD_CONFIG']})
        time.tzset()
        results={}
        with (evidence/'clamd.log').open('wb') as log:
            process=subprocess.Popen([binary,'--config-file='+str(config)],stdout=log,stderr=subprocess.STDOUT,env=env)
            try:
                deadline=time.monotonic()+120
                while not endpoint.exists():
                    if process.poll() is not None or time.monotonic()>deadline:
                        raise RuntimeError('Daemon did not become ready; inspect clamd.log')
                    time.sleep(.25)
                scanner=ClamdScanner()
                benign=b'%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n'
                clean=scanner.scan(benign)
                results['benign']=clean.status; results['engine']=clean.engine
                assert clean.status=='clean', 'Fresh-signature benign scan failed'
                fixture=(b'X5O!P%@AP[4'+b'\\PZX54(P^)7CC)7}'+b'$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*')
                results['standard_safe_detection_fixture']=scanner.scan(fixture).status
                assert results['standard_safe_detection_fixture']=='infected', 'Safe detection fixture not detected'
                # Compare the workflow's nonstandard PDF-looking wrapper with
                # an intact standard fixture inside a supported OOXML container.
                # A wrapper verdict is diagnostic, never an expected infection.
                assert len(fixture) == 68
                results['pdf_wrapped_fixture']=scanner.scan(b'%PDF-1.7\n'+fixture+b'\n%%EOF\n').status
                document=io.BytesIO()
                with zipfile.ZipFile(document,'w',zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr('[Content_Types].xml',
                        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
                    archive.writestr('word/document.xml',
                        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')
                    archive.writestr('synthetic-antivirus-test.txt',fixture)
                results['ooxml_contained_standard_fixture']=scanner.scan(document.getvalue()).status
                assert results['ooxml_contained_standard_fixture']=='infected', 'Contained standard fixture not detected'
                packed=io.BytesIO()
                with zipfile.ZipFile(packed,'w',zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr('synthetic-limit.txt',b'0'*(11*1024*1024))
                results['expanded_file_limit']=scanner.scan(packed.getvalue()).status
                assert results['expanded_file_limit']=='error','Expanded scan limit did not hold for review'
                # Malformed/inactive endpoint must never fall back to another scanner.
                saved=scanner.path; scanner.path=str(root/'absent.sock')
                results['missing_engine']=scanner.scan(benign).status
                scanner.path=saved
                assert results['missing_engine']=='error'
            finally:
                if process.poll() is None:
                    process.terminate()
                    try: process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.wait(timeout=5)
                results['daemon_stopped']=process.poll() is not None
                results['child_peak_rss_kib']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
                (evidence/'engine-results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results,sort_keys=True))
    print('CLAMAV_ENGINE_GATE_PASS')


if __name__=='__main__': main()
