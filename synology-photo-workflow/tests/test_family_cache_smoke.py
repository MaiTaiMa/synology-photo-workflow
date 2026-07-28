import json
from types import SimpleNamespace
from PIL import Image
import app.familyrecognition as f
from app.photoworkflow import defaults
class E(list):
 def tolist(self):return list(self)
class Backend:
 def load_image_file(self,p):return p
 def face_encodings(self,p):return [E([.1,.2,.3])]
 def face_distance(self,refs,e):return [0.0 for _ in refs]
def cfg(tmp):
 c=defaults();c['familyrecognition'].update(referencedir=str(tmp/'faces'),cachedir=str(tmp/'cache'),minreferenceimagesperperson=1);c['runtime']['quarantine']=str(tmp/'q');return c
def test_rebuild_smoke_activates_valid_cache(tmp_path,monkeypatch):
 monkeypatch.setattr(f,'face_recognition',Backend());(tmp_path/'faces'/'alice'/'reference').mkdir(parents=True);Image.new('RGB',(10,10)).save(tmp_path/'faces'/'alice'/'reference'/'a.jpg')
 m=f.rebuildfamilycache(cfg(tmp_path));assert m['status']=='available' and 'alice' in m['people'];assert f.loadfamilymodel(cfg(tmp_path))['fingerprint']==m['fingerprint']
def test_failed_rebuild_preserves_previous_active_cache(tmp_path,monkeypatch):
 monkeypatch.setattr(f,'face_recognition',Backend());(tmp_path/'faces'/'alice'/'reference').mkdir(parents=True);Image.new('RGB',(10,10)).save(tmp_path/'faces'/'alice'/'reference'/'a.jpg');c=cfg(tmp_path);good=f.rebuildfamilycache(c)
 class Broken(Backend):
  def face_encodings(self,p):return []
 monkeypatch.setattr(f,'face_recognition',Broken())
 import pytest
 with pytest.raises(ValueError):f.rebuildfamilycache(c)
 assert json.loads((tmp_path/'cache'/'familyindex.json').read_text())['fingerprint']==good['fingerprint']
