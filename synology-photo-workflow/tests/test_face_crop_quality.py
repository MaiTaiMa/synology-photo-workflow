from PIL import Image
from app.familyrecognition import crop_quality
def test_crop_quality_rejects_flat_and_accepts_detail(tmp_path):
 flat=Image.new('RGB',(100,100),(128,128,128));assert crop_quality(flat,(0,0,100,100))['sharpness']<.08
 im=Image.new('RGB',(100,100));px=im.load()
 for y in range(100):
  for x in range(100):px[x,y]=(40 if (x//5+y//5)%2 else 210,)*3
 q=crop_quality(im,(0,0,100,100));assert q['sharpness']>=.08 and q['exposure']>.35
