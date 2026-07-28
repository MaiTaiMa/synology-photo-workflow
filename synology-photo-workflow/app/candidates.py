from __future__ import annotations
import shutil
from PIL import Image
from pathlib import Path
from app.state import atomic_json,load_control,validate_candidates,utcnow,canonical_hash,ContractError
from app.safety import sha256
IMAGE={'.jpg','.jpeg','.png'}
def _empty(scope):return {'schemaversion':1,'createdat':utcnow(),'updatedat':utcnow(),'producerversion':'7.1.0','scope':scope,'candidates':[]}
def load_candidates(root,scope,quarantine_dir=None):
 p=Path(root)/'candidates.json'
 if not p.exists():return _empty(scope)
 return load_control(p,'candidates',quarantine_dir)
def _write(root,data):
 data['updatedat']=utcnow();atomic_json(Path(root)/'candidates.json',data,validate_candidates);return data
def visual_hash(path):
 im=Image.open(path).convert('L').resize((9,8));px=list(im.get_flattened_data());diff=''.join('1' if px[y*9+x]>px[y*9+x+1] else '0' for y in range(8) for x in range(8));mean=sum(px)//len(px);return diff+':'+str(mean)
def _distance(a,b):
 if not a or not b:return 65
 try:
  da,ma=a.split(':');db,mb=b.split(':');return 65 if abs(int(ma)-int(mb))>12 else sum(x!=y for x,y in zip(da,db))
 except ValueError:return 65
def propose(root,source,scope,quality,novelty,confidence,limit_per_run=10,max_open=100,quarantine_dir=None,runid=None,visual_distance_max=4,metadata=None):
 root=Path(root);source=Path(source);new=root/'newfaces' if scope.startswith('face:') else root/'newrefs';new.mkdir(parents=True,exist_ok=True)
 if not source.is_file() or source.is_symlink() or source.suffix.lower() not in IMAGE:raise ValueError('CANDIDATEINVALIDSOURCE')
 data=load_candidates(root,scope,quarantine_dir);runid=runid or utcnow();open_=[x for x in data['candidates'] if x['status']=='pendingreview']
 if len(open_)>=max_open:return None,'openlimitreached'
 sourcehash=sha256(source)
 try:vhash=visual_hash(source)
 except Exception:raise ValueError('CANDIDATEIMAGEUNREADABLE')
 # Hash catches byte-identical files; dHash rejects near-identical re-encodes/crops conservatively.
 known=[x.get('visualhash') for x in data['candidates'] if x.get('status') in ('pendingreview','accepted')]
 for folder in (root/'reference',new):
  if folder.exists():
   for p in folder.rglob('*'):
    if p.is_file() and not p.is_symlink() and p.suffix.lower() in IMAGE:
     try:known.append(visual_hash(p))
     except Exception:continue
 if any(_distance(vhash,h)<=int(visual_distance_max) for h in known):return None,'visualduplicate'
 if any(x['sourcehash']==sourcehash and x['status'] in ('pendingreview','accepted') for x in data['candidates']):return None,'duplicate'
 created=sum(1 for x in data['candidates'] if x.get('runid')==runid and x['status']=='pendingreview')
 if created>=limit_per_run:return None,'runlimitreached'
 cid=canonical_hash({'sourcehash':sourcehash,'scope':scope})[:16];target=new/(source.stem+'-'+sourcehash[:8]+source.suffix.lower())
 if target.exists() and sha256(target)!=sourcehash:raise ValueError('CANDIDATECOLLISION')
 if not target.exists():
  tmp=target.with_name('.'+target.name+'.tmp');shutil.copy2(source,tmp)
  if sha256(tmp)!=sourcehash:tmp.unlink(missing_ok=True);raise ValueError('CANDIDATECOPYVERIFYFAILED')
  tmp.replace(target)
 item={'candidateid':cid,'sourcepath':str(source),'sourcehash':sourcehash,'relativepath':str(target.relative_to(root)).replace('\\','/'),'status':'pendingreview','quality':float(quality),'novelty':float(novelty),'confidence':float(confidence),'createdat':utcnow(),'runid':runid,'visualhash':vhash,'origin':'generated'}
 item.update(metadata or {});data['candidates'].append(item);_write(root,data);return item,'created'
def refresh_candidates(root,scope,quarantine_dir=None):
 data=load_candidates(root,scope,quarantine_dir);root=Path(root);changed=False
 for x in data['candidates']:
  p=root/x.get('relativepath','')
  if x['status']=='pendingreview' and not p.exists():x['status']='missing';changed=True
  elif x['status']=='pendingreview' and p.is_file() and sha256(p)!=x['sourcehash']:x['status']='invalid';changed=True
 if changed:_write(root,data)
 return data

def reconcile_candidates(root,scope,quarantine_dir=None):
 """Recognise human acceptance by a matching manual copy into reference; never delete candidates."""
 root=Path(root);data=load_candidates(root,scope,quarantine_dir);reference=root/'reference';hashes={sha256(p) for p in reference.rglob('*') if p.is_file() and not p.is_symlink() and p.suffix.lower() in IMAGE} if reference.exists() else set();changed=False
 for x in data['candidates']:
  if x['status']=='pendingreview' and x['sourcehash'] in hashes:
   x['status']='accepted';x['acceptedat']=utcnow();x['acceptance']='manual-copy-to-reference';changed=True
 if changed:_write(root,data)
 return data
def move_generated_candidate_to_notused(root,candidateid,scope,quarantine_dir=None):
 """Explicit, reversible lifecycle step: copy-verify-delete only generated proposals, never references."""
 root=Path(root);data=load_candidates(root,scope,quarantine_dir);item=next((x for x in data['candidates'] if x['candidateid']==candidateid),None)
 if not item or item['status'] not in ('pendingreview','superseded') or item.get('origin')!='generated':raise ValueError('CANDIDATENOTMOVABLE')
 src=root/item['relativepath'];destdir=root/'notused';destdir.mkdir(exist_ok=True);dest=destdir/src.name
 if not src.exists() or sha256(src)!=item['sourcehash']:raise ValueError('CANDIDATESOURCEINVALID')
 if dest.exists() and sha256(dest)!=item['sourcehash']:raise ValueError('CANDIDATEDESTCOLLISION')
 if not dest.exists():
  tmp=dest.with_name('.'+dest.name+'.tmp');shutil.copy2(src,tmp)
  if sha256(tmp)!=item['sourcehash']:tmp.unlink(missing_ok=True);raise ValueError('CANDIDATECOPYVERIFYFAILED')
  tmp.replace(dest)
 src.unlink();item['status']='inactive';item['movedat']=utcnow();item['relativepath']=str(dest.relative_to(root)).replace('\\','/');item['move']='copy-verify-delete-to-notused';_write(root,data);return item
