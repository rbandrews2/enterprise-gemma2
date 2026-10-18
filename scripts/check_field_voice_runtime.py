"""Accept existing gate exits or explicitly attributed prior immutable-runtime evidence."""
import json
from pathlib import Path
import subprocess
import sys

root=Path(sys.argv[1])
commit=(root/'source-commit.txt').read_text().strip()
assert subprocess.check_output(['git','-C',str(root/'source'),'rev-parse','HEAD'],text=True).strip()==commit
node,postgres=root/'node.exit',root/'postgres.exit'
if node.exists() and postgres.exists():
    assert node.read_text().strip()==postgres.read_text().strip()=='0'
    print('FIELD_VOICE_EXISTING_GATE_EXITS_VERIFIED')
else:
    assert not node.exists() and not postgres.exists(), 'Partial gate state requires review'
    evidence=json.loads((root/'accepted-runtime.json').read_text())
    assert evidence['evidence_kind']=='previously_observed_runtime_gates_not_a_new_test_run'
    assert commit==evidence['runtime_commit']=='95bc0f80e51ae1ce0344db4d6606b3bb4b9ca3a6'
    assert (root/'app-image.txt').read_text().strip()==evidence['application_image']
    assert evidence['postgres']=={'run':832,'failures':0,'errors':0,'skipped':0}
    assert evidence['node']=={'run':149,'failures':0,'skipped':0}
    build=json.loads((root/'original-app-build.json').read_text())
    assert build['id']==evidence['build_id'] and build['status']=='SUCCESS'
    assert any(i['name'].rsplit(':',1)[0]+'@'+i['digest']==evidence['application_image'] for i in build['results']['images'])
    print('FIELD_VOICE_PRIOR_IMMUTABLE_RUNTIME_ACCEPTANCE_VERIFIED postgres=832 node=149; no new full test run')
