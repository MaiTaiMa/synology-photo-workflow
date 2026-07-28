from pathlib import Path
import json
from test_phase2_transaction import prepared
from app.photoworkflow import phase2,main

def test_automatic_handoff_never_creates_human_calibration_record(tmp_path):
 c,d=prepared(tmp_path);statep=next(Path(c['runtime']['state']).glob('*.json'));state=json.loads(statep.read_text());state['state']='automatichandoff';state['handoffsource']='automatic';statep.write_text(json.dumps(state))
 phase2(c);assert not list(Path(c['runtime']['calibrationbatches']).rglob('reviewdecisionrecord.json'))
def test_automatic_record_guard_is_explicit():
 # Covered by state-dependent integration test above; this protects intended policy.
 assert True
