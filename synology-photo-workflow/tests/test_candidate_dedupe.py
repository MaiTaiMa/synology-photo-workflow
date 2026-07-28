from PIL import Image
from app.candidates import propose
def image(p,c):p.parent.mkdir(parents=True,exist_ok=True);Image.new('RGB',(32,32),c).save(p)
def test_visual_duplicate_and_actual_runid(tmp_path):
 root=tmp_path/'samples';a=tmp_path/'a.jpg';b=tmp_path/'b.jpg';c=tmp_path/'c.jpg';image(a,(10,10,10));image(b,(10,10,10));image(c,(20,30,40))
 assert propose(root,a,'samples',1,1,1,runid='run-a')[1]=='created'
 assert propose(root,b,'samples',1,1,1,runid='run-b')[1]=='visualduplicate'
 assert propose(root,c,'samples',1,1,1,limit_per_run=1,runid='run-a')[1]=='runlimitreached'
 assert propose(root,c,'samples',1,1,1,limit_per_run=1,runid='run-b')[1]=='created'
