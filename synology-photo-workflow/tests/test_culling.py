from pathlib import Path
from PIL import Image
import pytest
from app.photoworkflow import loadconfig,score_folder,phase1
from app.seriesculling import applyseriesculling
from test_v7 import config,jpg

def test_final_score_renormalizes_available_components(tmp_path,monkeypatch):
 c=config(tmp_path);c['personalscoring']['enabled']=True;c['personalscoring']['modelpath']=str(tmp_path/'model.json');Path(c['personalscoring']['modelpath']).write_text('{"modeltype":"linearv1","intercept":0.8,"weights":{}}')
 p=tmp_path/'x.jpg';jpg(p)
 monkeypatch.setattr('app.photoworkflow.extractfeatures',lambda _: {'embedding':[1]*10,'megapixels':1,'aspect':1,'filesize':1,'edgevariance':.1})
 monkeypatch.setattr('app.photoworkflow.basescorecomponents',lambda *_: {'sharpscore':.2,'aesthscore':.2,'exposurescore':.2,'referencescore':None})
 rows=score_folder(c,tmp_path);r=rows[0]
 # base .2 with weight .55 and personal .8 with .2: unavailable eye/family weights are excluded.
 assert r['finalscore']==pytest.approx((.2*.55+.8*.2)/.75);assert r['scoredecision']=='review';assert r['finaldecision']=='review'
def test_series_best_is_only_promoted_one_class():
 rows=[{'embedding':[1.,0.],'finalscore':.1,'decision':'reject','decisionreason':'score','protectedbyfamilyrule':False},{'embedding':[.99,.01],'finalscore':.05,'decision':'reject','decisionreason':'score','protectedbyfamilyrule':False}]
 cfg={'seriesdetection':{'enabled':True,'clustereps':.18,'minsamples':2,'reviewmargin':.03,'demotenonbestto':'reject'}}
 result=applyseriesculling(rows,cfg)
 assert result[0]['decision']=='review';assert result[0]['seriesbest'];assert result[1]['decision']=='reject';assert result[1]['seriesrank']==2
def test_phase1_places_nonkeep_only_in_review_or_rejected(tmp_path):
 c=config(tmp_path);src=Path(c['paths']['tempsd'])/'20250707';src.mkdir(parents=True);jpg(src/'x.jpg')
 phase1(c);d=Path(c['paths']['tempimages'])/'2025-07-07'
 places=[p for p in (d/'x.jpg',d/'Review/x.jpg',d/'Rejected/x.jpg') if p.exists()]
 assert len(places)==1
