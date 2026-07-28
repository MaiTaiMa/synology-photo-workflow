from __future__ import annotations
import json
from pathlib import Path
from app.state import atomic_json,canonical_hash,utcnow,validate_selection,load_control,ContractError
from app.safety import sha256
from app.candidates import visual_hash,_distance
IMAGE={'.jpg','.jpeg','.png'}
def _entry(root,p,status,value,origin='manual'):
 return {'relativepath':str(p.relative_to(root)).replace('\\','/'),'sha256':sha256(p),'size':p.stat().st_size,'origin':origin,'status':status,'selectionvalue':value,'selectionreason':'reference-folder' if status=='active' else 'notused-folder','traininglabel':'positive' if status=='active' else 'negative' if origin!='manual' or status=='inactive' else None}
def _annotate_diversity(root,entries):
 # Deterministic greedy profile: informative for pool review, never silently changes user-selected status.
 hashes={};selected=[]
 for e in sorted(entries,key=lambda x:(-float(x.get('selectionvalue',0)),x['relativepath'],x['sha256'])):
  try:hashes[e['relativepath']]=visual_hash(Path(root)/e['relativepath'])
  except Exception:hashes[e['relativepath']]=None
 for e in sorted(entries,key=lambda x:(x['relativepath'],x['sha256'])):
  h=hashes[e['relativepath']]; distances=[_distance(h,hashes[x['relativepath']]) for x in selected if hashes[x['relativepath']]]
  nearest=min(distances) if distances else None
  e['visualhash']=h;e['nearestvisualdistance']=nearest;e['visualduplicate']=bool(nearest is not None and nearest<=4)
  # Rank is stable and exposes diversity to reviewers; selection remains explicitly human-authoritative.
  e['diversityvalue']=round((nearest or 64)/64,6);selected.append(e)
 return entries
def ensure_selection(root,scope='samples',displayname='personal taste',quarantine_dir=None):
 root=Path(root);
 try:
  from app.candidates import reconcile_candidates
  reconcile_candidates(root,scope,quarantine_dir)
 except ContractError: raise
 manifest=root/'selection.json';folders=((root/'reference','active',1),(root/'notused','inactive',-1));inventory=[]
 for folder,status,value in folders:
  folder.mkdir(parents=True,exist_ok=True)
  for p in sorted(folder.rglob('*')):
   if p.is_file() and not p.is_symlink() and p.suffix.lower() in IMAGE:inventory.append(_entry(root,p,status,value))
 (root/'newrefs').mkdir(exist_ok=True);inventory.sort(key=lambda x:(x['relativepath'],x['sha256']));fingerprint=canonical_hash(inventory);previous=None
 if manifest.exists():
  try:previous=load_control(manifest,'selection',quarantine_dir)
  except ContractError:raise
 # Preserve explicit manifest labels where the exact managed file still exists; filesystem only inventories additions.
 prior={(e['relativepath'],e['sha256']):e for e in previous.get('entries',[]) } if previous else {}
 entries=[]
 for e in inventory:
  old=prior.get((e['relativepath'],e['sha256']))
  entries.append(old if old else e)
 if previous and previous.get('poolfingerprint')==fingerprint:return previous
 entries=_annotate_diversity(root,entries)
 data={'schemaversion':1,'createdat':previous['createdat'] if previous else utcnow(),'updatedat':utcnow(),'producerversion':'7.1.0','scope':scope,'displayname':displayname,'algorithmversion':'authoritative-selection-v1','poolfingerprint':fingerprint,'entries':entries,'rebuildrequired':bool(previous)}
 atomic_json(manifest,data,validate_selection);return data

def propose_sample(root,source,quality,novelty,confidence,quarantine_dir=None,runid=None):
 from app.candidates import propose
 return propose(root,source,'samples',quality,novelty,confidence,10,100,quarantine_dir,runid=runid)
