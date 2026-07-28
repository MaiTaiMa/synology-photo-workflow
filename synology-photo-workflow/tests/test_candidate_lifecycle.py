from pathlib import Path
from PIL import Image
from app.candidates import propose,reconcile_candidates,move_generated_candidate_to_notused

def image(p,c=(1,2,3)):p.parent.mkdir(parents=True,exist_ok=True);Image.new('RGB',(20,20),c).save(p)
def test_manual_reference_copy_accepts_without_deleting_proposal(tmp_path):
 root=tmp_path/'samples';src=tmp_path/'src.jpg';image(src);item,_=propose(root,src,'samples',.9,.8,.7)
 image(root/'reference'/'accepted.jpg');(root/'reference'/'accepted.jpg').write_bytes((root/item['relativepath']).read_bytes())
 data=reconcile_candidates(root,'samples');assert data['candidates'][0]['status']=='accepted';assert (root/item['relativepath']).exists()
def test_explicit_generated_move_is_verified_and_never_reference(tmp_path):
 root=tmp_path/'samples';src=tmp_path/'src.jpg';image(src);item,_=propose(root,src,'samples',.9,.8,.7)
 moved=move_generated_candidate_to_notused(root,item['candidateid'],'samples');assert moved['status']=='inactive';assert (root/moved['relativepath']).exists();assert not (root/'newrefs'/Path(item['relativepath']).name).exists()
