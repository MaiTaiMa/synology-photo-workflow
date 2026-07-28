import json
import pytest
from app.state import ContractError,transition,load_control,atomic_json,validate_state,canonical_hash

def state_args():return dict(batchid='20250707-deadbeef',sourcefolder='20250707',fingerprint='deadbeef'*8,configfingerprint='a'*64,modelversion='rule-v1')
def test_new_state_is_atomic_and_forward_only(tmp_path):
 p=tmp_path/'state.json';first=transition(p,'phase1completed',**state_args())
 assert first['history'][0]['state']=='phase1completed';assert load_control(p,'state')['batchid']==first['batchid']
 later=transition(p,'reviewcomparisonpending');assert later['state']=='reviewcomparisonpending'
 with pytest.raises(ContractError,match='STATEBACKWARD'):transition(p,'phase1completed')
def test_invalid_state_is_quarantined(tmp_path):
 p=tmp_path/'state.json';p.write_text('{bad json');q=tmp_path/'quarantine'
 with pytest.raises(ContractError,match='STATEINVALID'):load_control(p,'state',q)
 assert list(q.iterdir())
def test_atomic_writer_rejects_invalid_contract(tmp_path):
 with pytest.raises(ContractError):atomic_json(tmp_path/'x.json',{'schemaversion':1},validate_state)


def test_duplicate_image_hashes_block_final_review(tmp_path):
 from app.photoworkflow import final_decisions
 from app.safety import SafetyError
 d=tmp_path; (d/'Review').mkdir(); (d/'a.jpg').write_bytes(b'x'); (d/'Review/b.jpg').write_bytes(b'x')
 m={'images':[{'imageid':'same','relativepath':'a.jpg'},{'imageid':'same','relativepath':'b.jpg'}]}
 with pytest.raises(SafetyError,match='reviewstateinvalid'):final_decisions(d,m)
