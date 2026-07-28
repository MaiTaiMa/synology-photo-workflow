from pathlib import Path
from test_v7 import config,jpg
from app.familyrecognition import detectfamilymembers,rebuildfamilycache
from app.photoworkflow import score_folder

def test_disabled_or_missing_backend_degrades_without_match(tmp_path,monkeypatch):
 c=config(tmp_path);c['familyrecognition']['enabled']=True;c['familyrecognition']['referencedir']=str(tmp_path/'refs');c['familyrecognition']['cachedir']=str(tmp_path/'cache')
 monkeypatch.setattr('app.familyrecognition.face_recognition',None)
 assert rebuildfamilycache(c)['status']=='backendunavailable';assert detectfamilymembers(tmp_path/'x.jpg',{},c)==([],'backendunavailable')
def test_family_match_only_promotes_reject_to_review(tmp_path,monkeypatch):
 c=config(tmp_path);c['familyrecognition'].update({'enabled':True,'referencedir':str(tmp_path/'refs'),'cachedir':str(tmp_path/'cache'),'protectmatches':True})
 p=tmp_path/'x.jpg';jpg(p)
 monkeypatch.setattr('app.photoworkflow.loadfamilymodel',lambda _: {'status':'available','people':{'Ada':[[1]]}})
 monkeypatch.setattr('app.photoworkflow.detectfamilymembers',lambda *a: (['Ada'],'matched'))
 monkeypatch.setattr('app.photoworkflow.extractfeatures',lambda _: {'embedding':[0]*10,'megapixels':1,'aspect':1,'filesize':1,'edgevariance':.01})
 monkeypatch.setattr('app.photoworkflow.basescorecomponents',lambda *_: {'sharpscore':.1,'aesthscore':.1,'exposurescore':.1,'referencescore':None})
 r=score_folder(c,tmp_path)[0];assert r['finaldecision']=='review';assert r['protectedbyfamilyrule'];assert r['detectedpeople']==['Ada']
