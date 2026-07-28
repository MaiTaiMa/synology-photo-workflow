from pathlib import Path
from PIL import Image
from app.photoworkflow import loadconfig,phase1,phase2,makedatename
import yaml
def jpg(p):
 p.parent.mkdir(parents=True,exist_ok=True); seed=sum(p.name.encode())%120;Image.new('RGB',(64,48),(seed+40,100,50)).save(p)
def config(tmp):
 b=tmp/'data/TEMP'; data={'paths':{'basedir':str(b),'tempsd':str(b/'TEMPSD'),'tempimages':str(b/'TEMPIMAGES'),'tempdone':str(b/'TEMPDONE'),'temperror':str(b/'TEMPERROR'),'manualkeepinbox':str(b/'MANUALKEEP/inbox'),'manualkeepused':str(b/'MANUALKEEP/used'),'lockfile':str(b/'.lock')},'runtime':{'root':str(tmp/'data/TEMP/WORKFLOW_DATA/runtime'),'state':str(tmp/'data/TEMP/WORKFLOW_DATA/runtime/state'),'runsummaries':str(tmp/'data/TEMP/WORKFLOW_DATA/runtime/runsummaries'),'calibrationbatches':str(tmp/'data/TEMP/WORKFLOW_DATA/runtime/calibration/batches'),'calibrationindex':str(tmp/'data/TEMP/WORKFLOW_DATA/runtime/calibration/index.jsonl'),'calibrationsummary':str(tmp/'data/TEMP/WORKFLOW_DATA/runtime/calibration/summary.json')},'samples':{'root':str(tmp/'data/TEMP/WORKFLOW_DATA/samples')},'metadataculling':{'enabled':False},'workflow':{'phaseexecution':'phase1only','batchlimit':1},'calibration':{'enabled':True,'minimumreviewedbatches':1,'minimumreviewedimages':1,'minterminaldecisionagreement':.9,'maxrejecttokeeprate':0.0}}
 q=tmp/'c.yaml';q.write_text(yaml.safe_dump(data));return loadconfig(q)
def test_manual_flow(tmp_path):
 c=config(tmp_path);src=Path(c['paths']['tempsd'])/'20250707';src.mkdir(parents=True)
 jpg(src/'a.jpg');jpg(src/'b.jpg');(src/'a.ARW').write_bytes(b'raw-a');(src/'b.ARW').write_bytes(b'raw-b')
 phase1(c);reviewed=Path(c['paths']['tempimages'])/'2025-07-07';assert (reviewed/'SAVE/culling_scores.csv').exists()
 # Simulate an explicit human review: a becomes active, b remains visible in Review.
 (reviewed/'Review/a.jpg').rename(reviewed/'a.jpg')
 done=Path(c['paths']['tempdone'])/reviewed.name;done.parent.mkdir(parents=True);reviewed.rename(done)
 assert phase2(c,dry=True)[0]['dryrun'];assert (done/'ARW/a.ARW').exists();assert (done/'ARW/b.ARW').exists()
 phase2(c);assert (done/'ARW/a.ARW').exists();assert not (done/'ARW/b.ARW').exists();assert list(Path(c['runtime']['calibrationbatches']).rglob('reviewdecisionrecord.json'))

def test_date(tmp_path):assert makedatename('20250707',config(tmp_path))=='2025-07-07'
