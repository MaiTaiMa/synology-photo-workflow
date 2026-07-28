import json,stat
from pathlib import Path
from app.metadatawriter import writecullingmetadata,buildcullingkeywords
from app.photoworkflow import defaults

def fake(tmp_path,mode='ok'):
 p=tmp_path/'fake_exiftool.py';p.write_text("""#!/usr/bin/env python3
import sys,json
args=sys.argv[1:]
open(sys.argv[0]+'.args','a').write(json.dumps(args)+'\\n')
if '-j' in args:
 print(json.dumps([{'Rating':'4','Subject':['workflowaicull','workflowmodelrule-v1','decisionpredictedkeep','decisionfinalkeep','scoreband4']}]))
 sys.exit(0)
if %r=='fail':sys.exit(2)
sys.exit(0)
""" % mode);p.chmod(p.stat().st_mode|stat.S_IXUSR);return p
def row():return {'starrating':4,'scoredecision':'keep','finaldecision':'keep','modelversion':'rule-v1','detectedpeople':[]}
def cfg(exe):
 c=defaults();c['metadataculling'].update(enabled=True,exiftoolpath=str(exe),writerating=True,writekeywords=True);return c
def test_fake_exiftool_uses_argument_argv_and_readback(tmp_path):
 exe=fake(tmp_path);photo=tmp_path/'photo with spaces.jpg';photo.write_bytes(b'x')
 assert writecullingmetadata(photo,row(),cfg(exe))=='written'
 calls=[json.loads(x) for x in Path(str(exe)+'.args').read_text().splitlines()];assert calls[0][-1]==str(photo);assert any(x.startswith('-XMP:Rating=4') for x in calls[0]);assert '-j' in calls[1]
def test_fake_exiftool_write_failure_is_reported(tmp_path):
 exe=fake(tmp_path,'fail');photo=tmp_path/'a.jpg';photo.write_bytes(b'x');assert writecullingmetadata(photo,row(),cfg(exe))=='writefailed'
def test_missing_exiftool_is_optional_status(tmp_path):
 photo=tmp_path/'a.jpg';photo.write_bytes(b'x');c=defaults();c['metadataculling'].update(enabled=True,exiftoolpath=str(tmp_path/'missing'));assert writecullingmetadata(photo,row(),c)=='exiftoolmissing'
