from PIL import Image
from app.samples import ensure_selection
def test_selection_exposes_deterministic_visual_diversity(tmp_path):
 root=tmp_path/'samples';(root/'reference').mkdir(parents=True)
 Image.new('RGB',(20,20),(50,50,50)).save(root/'reference'/'a.jpg');Image.new('RGB',(20,20),(50,50,50)).save(root/'reference'/'b.jpg')
 m=ensure_selection(root);entries=m['entries'];assert all(x['status']=='active' for x in entries);assert any(x['visualduplicate'] for x in entries)
 assert ensure_selection(root)==m
