import json
from pathlib import Path
from PIL import Image
import pytest
import app.photoworkflow as w
from app.photoworkflow import defaults,write_phase1,configfingerprint
from app.state import transition,load_control
from app.safety import SafetyError

def setup(tmp_path):
 c=defaults();base=tmp_path/'TEMP';c['paths'].update(basedir=str(base),tempdone=str(base/'TEMPDONE'),tempsd=str(base/'TEMPSD'),tempimages=str(base/'TEMPIMAGES'),temperror=str(base/'TEMPERROR'),manualkeepinbox=str(base/'MK/inbox'),manualkeepused=str(base/'MK/used'),lockfile=str(base/'.lock'))
 c['runtime'].update(state=str(tmp_path/'runtime/state'),calibrationbatches=str(tmp_path/'runtime/cal/batches'),calibrationindex=str(tmp_path/'runtime/cal/index.jsonl'),calibrationsummary=str(tmp_path/'runtime/cal/summary.json'),runsummaries=str(tmp_path/'runtime/runs'),quarantine=str(tmp_path/'runtime/q'));c['calibration']['enabled']=False
 d=base/'TEMPDONE'/'2026-01-01';(d/'ARW').mkdir(parents=True);Image.new('RGB',(20,20)).save(d/'keep.jpg');(d/'ARW'/'discard.ARW').write_bytes(b'raw-discard');(d/'ARW'/'keep.ARW').write_bytes(b'raw-keep')
 row={'imageid':'id1','relativepath':'keep.jpg','basescore':.8,'eyescore':None,'personalscore':None,'familyscore':None,'finalscore':.8,'starrating':4,'scoredecision':'keep','decision':'keep','finaldecision':'keep','decisionreason':'test','embedding':[0]*10,'modelversion':c['models']['version'],'configfingerprint':configfingerprint(c),'manualkeep':False}
 m=write_phase1(c,d,'batch-test', [row]);state=Path(c['runtime']['state'])/'batch-test.json';transition(state,'phase1completed',batchid='batch-test',currentpath=str(d),handoffsource='manualreview');return c,d,state

def test_archive_activated_before_delete_and_resume_reuses_it(tmp_path,monkeypatch):
 c,d,state=setup(tmp_path);real=w.safe_unlink;calls=[]
 def stop(cfg,path):
  calls.append(Path(path).name);raise RuntimeError('simulated power loss')
 monkeypatch.setattr(w,'safe_unlink',stop)
 with pytest.raises(RuntimeError):w.phase2(c)
 st=load_control(state,'state');archive=Path(st['archive']);assert archive.exists() and st['archiveverified'] is True;assert (d/'ARW'/'discard.ARW').exists()
 monkeypatch.setattr(w,'safe_unlink',real);w.phase2(c)
 assert not (d/'ARW'/'discard.ARW').exists() and (d/'ARW'/'keep.ARW').exists();assert archive.exists();assert load_control(state,'state')['state']=='phase2completed'
def test_tampered_planned_raw_blocks_resume(tmp_path):
 c,d,state=setup(tmp_path);w.phase2(c,dry=True)
 # Persist a plan then mutate input: phase2 must refuse destructive continuation.
 planned=[{'relativepath':'ARW/discard.ARW','sha256':'0'*64,'size':1}];transition(state,'phase2archiving',batchid='batch-test',archiveplan=planned,archiveplanhash=w.canonical_hash(planned))
 with pytest.raises(SafetyError,match='ARCHIVEPLANMISMATCH'):w.phase2(c)
def test_existing_archive_collision_gets_extra_name(tmp_path):
 c,d,state=setup(tmp_path);(d/'SAVE').mkdir(exist_ok=True);(d/'SAVE'/'2026-01-01SORTARW.zip').write_bytes(b'foreign')
 out=w.phase2(c);assert 'EXTRA' in Path(out[0]['archive']).name
