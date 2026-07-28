import json
from pathlib import Path
import pytest
from app.calibration import build_record,rebuild_index,record_matches
from app.state import canonical_hash

def manifest(batchid='b',pred='keep'):
 m={'schemaversion':1,'batchid':batchid,'completedat':'2026-01-01T00:00:00Z','configfingerprint':'a'*64,'modelversion':'rule-v1','images':[{'imageid':batchid+'i','relativepath':'x.jpg','finaldecision':pred,'finalscore':.8,'basescore':.7,'personalscore':None,'familyscore':None,'seriesrank':1,'finalsource':'mainfolder','finalrelativepath':'x.jpg'}]};m['manifesthash']=canonical_hash(m);return m
def cfg():return {'calibration':{'minimumreviewedbatches':2,'minimumreviewedimages':2,'minterminaldecisionagreement':.9,'maxrejecttokeeprate':0.,'maxrejecttoreviewrate':.01,'evaluationwindow':{'reviewedbatches':10,'reviewedimages':1000}}}
def write(root,r):
 p=root/r['batchid']/'reviewdecisionrecord.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r));return p
def test_record_is_immutable_match_ignores_timestamp_and_detects_decision_change():
 m=manifest();r=build_record('b',m,{'bi':'keep'},'a'*64,'rule-v1','2026-01-02T00:00:00Z')
 assert record_matches(r,m,{'bi':'keep'},'a'*64,'rule-v1');assert not record_matches(r,m,{'bi':'reject'},'a'*64,'rule-v1')
def test_index_uses_nested_records_and_fingerprint_separation(tmp_path):
 rr=tmp_path/'records';write(rr,build_record('b1',manifest('b1'),{'b1i':'keep'},'a'*64,'rule-v1','2026-01-03T00:00:00Z'));write(rr,build_record('b2',manifest('b2'),{'b2i':'keep'},'a'*64,'rule-v1','2026-01-02T00:00:00Z'));write(rr,build_record('other',manifest('other'),{'otheri':'keep'},'b'*64,'rule-v1','2026-01-04T00:00:00Z'))
 out=tmp_path/'index.jsonl';summary=tmp_path/'summary.json';p=rebuild_index(rr,out,summary,'a'*64,'rule-v1',cfg())
 assert p['recordcount']==2;assert p['status']=='eligibleconservative';assert len(out.read_text().splitlines())==2
def test_critical_reject_to_keep_is_not_eligible(tmp_path):
 rr=tmp_path/'records';write(rr,build_record('b1',manifest('b1','reject'),{'b1i':'keep'},'a'*64,'rule-v1','2026-01-03T00:00:00Z'));write(rr,build_record('b2',manifest('b2','keep'),{'b2i':'keep'},'a'*64,'rule-v1','2026-01-02T00:00:00Z'))
 p=rebuild_index(rr,tmp_path/'i',tmp_path/'s','a'*64,'rule-v1',cfg());assert p['status']=='noteligible';assert 'criticalmetric' in p['reasons']
