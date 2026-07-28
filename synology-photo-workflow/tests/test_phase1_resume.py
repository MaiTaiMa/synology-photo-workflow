from pathlib import Path
from PIL import Image
from app.photoworkflow import score_folder,_save_phase1_work,_phase1_work,defaults

def test_phase1_work_roundtrip_and_score_reuse(tmp_path,monkeypatch):
 d=tmp_path/'20260101';d.mkdir();Image.new('RGB',(20,20)).save(d/'a.jpg')
 row={'imageid':'x','relativepath':'a.jpg','embedding':[0]*10,'finalscore':.5,'decision':'review','finaldecision':'review'}
 _save_phase1_work(d/'work.json',{'x':row});assert _phase1_work(d/'work.json')['x']==row
