from pathlib import Path
import json
from app.photoworkflow import apply_manual_keep
from app.metadatawriter import writecullingmetadata,buildcullingkeywords
from test_v7 import config,jpg

def test_manual_keep_requires_threshold_and_margin(tmp_path,monkeypatch):
 c=config(tmp_path);inbox=Path(c['paths']['manualkeepinbox']);jpg(inbox/'m.jpg')
 rows=[{'imageid':'a','embedding':[1,0],'decision':'review','finaldecision':'review','decisionreason':'score'},{'imageid':'b','embedding':[0,1],'decision':'review','finaldecision':'review','decisionreason':'score'}]
 monkeypatch.setattr('app.photoworkflow.extractfeatures',lambda _: {'embedding':[1,0]})
 events=apply_manual_keep(c,tmp_path,rows);assert events[0]['status']=='matched';assert rows[0]['finaldecision']=='keep';assert rows[0]['manualkeep'];assert (Path(c['paths']['manualkeepused'])/'m.jpg').exists()
def test_manual_keep_ambiguous_stays_in_inbox(tmp_path,monkeypatch):
 c=config(tmp_path);inbox=Path(c['paths']['manualkeepinbox']);jpg(inbox/'m.jpg');rows=[{'imageid':'a','embedding':[1,0]},{'imageid':'b','embedding':[.999,0]}]
 monkeypatch.setattr('app.photoworkflow.extractfeatures',lambda _: {'embedding':[1,0]})
 assert apply_manual_keep(c,tmp_path,rows)[0]['status']=='unmatched';assert (inbox/'m.jpg').exists()
def test_metadata_roundtrip_is_verified(tmp_path,monkeypatch):
 image=tmp_path/'x.jpg';jpg(image);row={'starrating':4,'scoredecision':'review','finaldecision':'keep','modelversion':'rule-v1','seriesid':'S001','seriesbest':True,'manualkeep':True}
 expected=buildcullingkeywords(row);cfg={'metadataculling':{'enabled':True,'exiftoolpath':'exiftool','writerating':True,'writekeywords':True}}
 monkeypatch.setattr('app.metadatawriter.shutil.which',lambda _: '/x/exiftool')
 class R:
  returncode=0;stdout=json.dumps([{'Rating':4,'Subject':expected}])
 monkeypatch.setattr('app.metadatawriter.subprocess.run',lambda *a,**k:R())
 assert writecullingmetadata(image,row,cfg)=='written'
