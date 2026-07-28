"""Validated, atomic and forward-only control-data contracts."""
from __future__ import annotations
import hashlib,json,os,shutil,tempfile
from datetime import datetime,timezone
from pathlib import Path
SCHEMA=1
ORDER=('phase1processing','phase1completed','automatichandoff','reviewcomparisonpending','reviewrecordcommitted','calibrationindexcommitted','phase2archiving','phase2completed')
class ContractError(ValueError): pass
def utcnow(): return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def sha256_bytes(value): return hashlib.sha256(value).hexdigest()
def canonical_hash(data): return sha256_bytes(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf8'))
def batch_id(source_name,fingerprint): return f'{source_name}-{fingerprint[:8]}'
def _is_utc(value):
 try:return isinstance(value,str) and value.endswith('Z') and datetime.strptime(value,'%Y-%m-%dT%H:%M:%SZ') is not None
 except ValueError:return False
def _required(data, keys, kind):
 if not isinstance(data,dict) or any(k not in data for k in keys):raise ContractError(f'{kind}REQUIREDFIELDS')
def validate_state(data):
 _required(data,('schemaversion','batchid','state','createdat','updatedat','history'),'STATE')
 if data['schemaversion']!=SCHEMA:raise ContractError('STATEVERSION')
 if not isinstance(data['batchid'],str) or not data['batchid'] or data['state'] not in ORDER:raise ContractError('STATEVALUES')
 if not _is_utc(data['createdat']) or not _is_utc(data['updatedat']) or not isinstance(data['history'],list):raise ContractError('STATETIME')
 for step in data['history']:
  _required(step,('state','at'),'STATEHISTORY')
  if step['state'] not in ORDER or not _is_utc(step['at']):raise ContractError('STATEHISTORYVALUES')
 return data
def validate_manifest(data):
 _required(data,('schemaversion','batchid','completedat','configfingerprint','modelversion','images','manifesthash'),'MANIFEST')
 if data['schemaversion']!=SCHEMA or not _is_utc(data['completedat']) or not isinstance(data['images'],list):raise ContractError('MANIFESTVALUES')
 probe={k:v for k,v in data.items() if k!='manifesthash'}
 if data['manifesthash']!=canonical_hash(probe):raise ContractError('MANIFESTHASH')
 return data
def validate_review_record(data):
 _required(data,('schemaversion','recordid','batchid','handoffsource','phase1completedat','reviewedat','configfingerprint','modelversion','images','counts','integrity','recordhash'),'RECORD')
 if data['schemaversion']!=SCHEMA or data['handoffsource'] not in ('manualreview','automatic') or not _is_utc(data['reviewedat']):raise ContractError('RECORDVALUES')
 probe={k:v for k,v in data.items() if k!='recordhash'}
 if data['recordhash']!=canonical_hash(probe):raise ContractError('RECORDHASH')
 return data
def validate_selection(data):
 _required(data,('schemaversion','createdat','updatedat','producerversion','scope','algorithmversion','poolfingerprint','entries'),'SELECTION')
 if data['schemaversion']!=SCHEMA or not _is_utc(data['createdat']) or not _is_utc(data['updatedat']) or not isinstance(data['entries'],list):raise ContractError('SELECTIONVALUES')
 for e in data['entries']:
  _required(e,('relativepath','sha256','size','origin','status','selectionvalue','selectionreason'),'SELECTIONENTRY')
  if e['status'] not in ('active','inactive','pendingreview','superseded','manualprotected','archived') or e['origin'] not in ('manual','generated','managed'):raise ContractError('SELECTIONENTRYVALUES')
 return data
def validate_candidates(data):
 _required(data,('schemaversion','createdat','updatedat','producerversion','scope','candidates'),'CANDIDATES')
 if data['schemaversion']!=SCHEMA or not isinstance(data['candidates'],list):raise ContractError('CANDIDATESVALUES')
 for x in data['candidates']:_required(x,('candidateid','sourcepath','sourcehash','status','quality','novelty','confidence','createdat'),'CANDIDATEENTRY')
 return data
def validate_summary(data):
 _required(data,('schemaversion','runid','createdat','updatedat','producerversion','command','configfingerprint','status','useractionsrequired'),'SUMMARY')
 if data['schemaversion']!=SCHEMA or not _is_utc(data['createdat']) or not _is_utc(data['updatedat']):raise ContractError('SUMMARYVALUES')
 return data

def validate_control(data,kind):
 return {'state':validate_state,'manifest':validate_manifest,'record':validate_review_record,'selection':validate_selection,'candidates':validate_candidates,'summary':validate_summary}[kind](data)
def atomic_json(path,data,validator=None):
 if validator: validator(data)
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name+'.',suffix='.tmp')
 try:
  with os.fdopen(fd,'w',encoding='utf8') as f:json.dump(data,f,indent=2,ensure_ascii=False,sort_keys=True);f.flush();os.fsync(f.fileno())
  loaded=json.loads(Path(tmp).read_text(encoding='utf8'))
  if validator:validator(loaded)
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def quarantine(path,quarantinedir,reason):
 p=Path(path);q=Path(quarantinedir);q.mkdir(parents=True,exist_ok=True);digest=sha256_bytes(p.read_bytes()) if p.exists() else 'missing';target=q/(p.name+'.'+digest[:12]+'.json')
 if p.exists():shutil.copy2(p,target)
 return {'reason':reason,'source':str(p),'copy':str(target),'sha256':digest,'at':utcnow()}
def load_control(path,kind,quarantinedir=None):
 p=Path(path)
 try:return validate_control(json.loads(p.read_text(encoding='utf8')),kind)
 except (OSError,json.JSONDecodeError,ContractError) as exc:
  if quarantinedir:quarantine(p,quarantinedir,type(exc).__name__)
  raise ContractError(f'{kind.upper()}INVALID:{exc}') from exc
def transition(state_path,next_state,**extra):
 if next_state not in ORDER:raise ContractError('STATEUNKNOWN')
 p=Path(state_path);old=load_control(p,'state') if p.exists() else None;now=utcnow()
 if old:
  current=old['state']
  if current==next_state:
   data=dict(old);data.update(extra,updatedat=now);atomic_json(p,data,validate_state);return data
  if current=='phase2completed':raise ContractError('STATECOMPLETED')
  if ORDER.index(next_state)<ORDER.index(current):raise ContractError('STATEBACKWARD')
  history=list(old['history'])
  data=dict(old)
 else:
  if next_state not in ('phase1processing','phase1completed'):raise ContractError('STATEINITIALTRANSITION')
  if not extra.get('batchid'):raise ContractError('STATEBATCHID')
  history=[];data={'schemaversion':SCHEMA,'batchid':extra['batchid'],'createdat':now}
 history.append({'state':next_state,'at':now});data.update(extra,state=next_state,updatedat=now,history=history)
 atomic_json(p,data,validate_state);return data
