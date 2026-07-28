from pathlib import Path
import json
from test_v7 import config
from app.photoworkflow import automatic_phase2_gate,write_automation_approval,configfingerprint

def eligible(c):
 p=Path(c['runtime']['calibrationsummary']);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({'configfingerprint':configfingerprint(c),'modelversion':c['models']['version'],'status':'eligibleconservative','recordshash':'r'*64}))
def test_assisted_review_is_always_manual(tmp_path):
 c=config(tmp_path);assert automatic_phase2_gate(c)==(False,['assistedreview'])
def test_automatic_requires_eligible_summary_and_explicit_bound_approval(tmp_path):
 c=config(tmp_path);c['automation'].update({'mode':'automaticphase2conservative','automaticphase2enabled':True,'approvalfile':str(tmp_path/'approval.json')});c['workflow']['phaseexecution']='phase1thenphase2'
 assert automatic_phase2_gate(c)==(False,['calibrationsummarymissing']);eligible(c);assert automatic_phase2_gate(c)==(False,['approvalmissing']);write_automation_approval(c);assert automatic_phase2_gate(c)==(True,[])
def test_changed_config_invalidates_approval(tmp_path):
 c=config(tmp_path);c['automation'].update({'mode':'automaticphase2conservative','automaticphase2enabled':True,'approvalfile':str(tmp_path/'approval.json')});c['workflow']['phaseexecution']='phase1thenphase2';eligible(c);write_automation_approval(c);c['culling']['keepthreshold']=.7
 assert automatic_phase2_gate(c)==(False,['calibrationcontextmismatch'])
def test_full_automatic_needs_stricter_status(tmp_path):
 c=config(tmp_path);c['automation'].update({'mode':'automaticphase2','automaticphase2enabled':True,'approvalfile':str(tmp_path/'approval.json')});c['workflow']['phaseexecution']='phase1thenphase2';eligible(c);write_automation_approval(c)
 assert automatic_phase2_gate(c)==(False,['calibrationnoteligible:eligibleconservative'])
