from pathlib import Path
import time
from app.photoworkflow import phase1
from test_v7 import config,jpg

def test_invalid_input_is_quarantined_before_original_operations(tmp_path):
 c=config(tmp_path);src=Path(c['paths']['tempsd'])/'badname';src.mkdir(parents=True);jpg(src/'x.jpg');(src/'x.ARW').write_bytes(b'r')
 result=phase1(c)
 assert result[0]['status']=='quarantined';q=Path(c['paths']['temperror'])
 assert (q/'badname-foldernameunsupported'/'x.ARW').exists();assert not list(Path(c['paths']['tempimages']).glob('*'))
def test_active_batch_lock_blocks_and_quarantines(tmp_path):
 c=config(tmp_path);src=Path(c['paths']['tempsd'])/'20250707';src.mkdir(parents=True);jpg(src/'x.jpg');(src/'.lock').write_text('active')
 result=phase1(c);assert result[0]['reason'].startswith('BATCHLOCKACTIVE');assert (Path(c['paths']['temperror'])/'20250707-batchlockactive-.lock'/'x.jpg').exists()
def test_unstable_batch_is_quarantined_without_creating_arw(tmp_path):
 c=config(tmp_path);c['workflow']['stabilityseconds']=3600;src=Path(c['paths']['tempsd'])/'20250707';src.mkdir(parents=True);jpg(src/'x.jpg')
 result=phase1(c);q=Path(c['paths']['temperror']);assert result[0]['reason']=='BATCHUNSTABLE';assert not list(q.rglob('ARW'))
