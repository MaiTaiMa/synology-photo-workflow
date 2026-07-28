from pathlib import Path
from PIL import Image
from app.candidates import propose,load_candidates

def image(p,c=(1,2,3)):p.parent.mkdir(parents=True,exist_ok=True);Image.new('RGB',(20,20),c).save(p)
def test_proposal_is_verified_and_recorded(tmp_path):
 src=tmp_path/'source.jpg';image(src);item,status=propose(tmp_path/'samples',src,'samples',.9,.8,.7)
 assert status=='created';copy=tmp_path/'samples'/item['relativepath'];assert copy.exists()
 assert load_candidates(tmp_path/'samples','samples')['candidates'][0]['status']=='pendingreview'
def test_proposals_respect_duplicate_and_open_limit(tmp_path):
 src=tmp_path/'a.jpg';image(src);root=tmp_path/'samples';assert propose(root,src,'samples',1,1,1,max_open=1)[1]=='created'
 assert propose(root,src,'samples',1,1,1,max_open=1)[1]=='openlimitreached'
 src2=tmp_path/'b.jpg';image(src2,(2,3,4));assert propose(root,src2,'samples',1,1,1,max_open=1)[1]=='openlimitreached'
