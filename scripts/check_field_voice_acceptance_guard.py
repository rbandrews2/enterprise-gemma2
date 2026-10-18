"""Prove sequence gating with inert shell stubs; no cloud/provider commands."""
from pathlib import Path
import subprocess
import tempfile

helper=Path(__file__).with_name('run_field_voice_acceptance.sh')
with tempfile.TemporaryDirectory(prefix='wzos-sequence-guard-') as directory:
    base=Path(directory)
    for fail in (True,False):
        root=base/str(fail);root.mkdir()
        for marker in ('combined-pilot-approved','speech-pilot-approved','model-approved','job-approved'):
            (root/marker).touch()
        (root/'speech-model.txt').write_text('long\n')
        (root/'run_speech.sh').write_text('exit 1\n' if fail else 'echo 0 > "$2/speech-pilot.exit"\necho 0 > "$2/speech-cleanup.verified"\n')
        (root/'run_pilot.sh').write_text('echo called >> "$2/gpu-stub.calls"\necho 0 > "$2/pilot.exit"\necho 0 > "$2/cleanup.verified"\n')
        result=subprocess.run(['bash',str(helper),str(root)],capture_output=True)
        assert (result.returncode!=0)==fail
        assert (root/'gpu-stub.calls').exists()!=fail, 'GPU stage must not run after Speech failure'
        repeated=subprocess.run(['bash',str(helper),str(root)],capture_output=True)
        assert repeated.returncode!=0, 'Started sequence must not repeat paid stages'
        if not fail: assert (root/'gpu-stub.calls').read_text().splitlines()==['called']
print('FIELD_VOICE_SEQUENCE_GUARD_PASS cases=4 provider_calls=0')
