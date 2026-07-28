from pathlib import Path
import json,pytest
from app.photoworkflow import phase1,phase2
from app.safety import SafetyError
from test_v7 import config,jpg

def prepared(tmp_path):
 c=config(tmp_path);src=Path(c['paths']['tempsd'])/'20250707';src.mkdir(parents=True);jpg(src/'a.jpg');jpg(src/'b.jpg');(src/'a.ARW').write_bytes(b'a');(src/'b.ARW').write_bytes(b'b');phase1(c)
 d=Path(c['paths']['tempimages'])/'2025-07-07';(d/'Review/a.jpg').rename(d/'a.jpg');done=Path(c['paths']['tempdone'])/d.name;done.parent.mkdir(parents=True);d.rename(done);return c,done
def test_archive_plan_is_committed_before_delete_and_resume_reuses_archive(tmp_path,monkeypatch):
 c,d=prepared(tmp_path);import app.photoworkflow as w;original=w.safe_unlink;calls=[]
 def interrupted(cfg,p):
  calls.append(Path(p).name);raise RuntimeError('interrupt-after-archive')
 monkeypatch.setattr(w,'safe_unlink',interrupted)
 with pytest.raises(RuntimeError):phase2(c)
 state=json.loads(next(Path(c['runtime']['state']).glob('*.json')).read_text());archive=Path(state['archive']);assert archive.exists();assert (d/'ARW/b.ARW').exists();assert state['archiveverified']
 monkeypatch.setattr(w,'safe_unlink',original);phase2(c);assert not (d/'ARW/b.ARW').exists();assert list((d/'SAVE').glob('*SORTARW.zip'))==[archive]
def test_changed_raw_after_plan_blocks_deletion(tmp_path,monkeypatch):
 c,d=prepared(tmp_path);import app.photoworkflow as w
 def interrupt(cfg,p):raise RuntimeError('interrupt')
 monkeypatch.setattr(w,'safe_unlink',interrupt)
 with pytest.raises(RuntimeError):phase2(c)
 (d/'ARW/b.ARW').write_bytes(b'changed')
 with pytest.raises(SafetyError,match='ARCHIVEPLANMISMATCH'):phase2(c)
 assert (d/'ARW/b.ARW').exists()
def test_zip_collision_uses_extra_name(tmp_path):
 c,d=prepared(tmp_path);(d/'SAVE'/(d.name+'SORTARW.zip')).write_bytes(b'foreign');phase2(c)
 assert list((d/'SAVE').glob(d.name+'SORTARWEXTRA1.zip'))
