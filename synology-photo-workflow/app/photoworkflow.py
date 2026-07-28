from __future__ import annotations
import argparse,csv,hashlib,json,os,re,shutil,sys,time
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime,timezone
import yaml
from app.aesthetic import extractfeatures,basescorecomponents,weightedbasescore,loadpersonalmodel,personalmodelscore
import numpy as np
from app.seriesculling import applyseriesculling,ratingforscore
from app.metadatawriter import writecullingmetadata
from app.state import atomic_json,canonical_hash,batch_id,transition,utcnow,validate_manifest,validate_review_record,validate_summary,load_control
from app.safety import within,require,sha256,verified_zip,verify_zip,safe_unlink,SafetyError
from app.samples import ensure_selection
from app.calibration import build_record,rebuild_index,record_matches
from app.familyrecognition import loadfamilymodel,detectfamilymembers
from app.runtime import RunBudget,PauseRequested,install_budget,restore_budget,resumable_states,mark_paused,mark_running
VERSION='7.1.0'; IMG={'.jpg','.jpeg'}; RAW={'.arw'}; VALID={'keep','review','reject'}
def defaults():return {'paths':{'basedir':'data/TEMP','tempsd':'data/TEMP/TEMPSD','tempimages':'data/TEMP/TEMPIMAGES','tempdone':'data/TEMP/TEMPDONE','temperror':'data/TEMP/TEMPERROR','manualkeepinbox':'data/TEMP/MANUALKEEP/inbox','manualkeepused':'data/TEMP/MANUALKEEP/used','lockfile':'data/TEMP/.workflow.lock'},'workflow':{'phaseexecution':'phase1only','waittimeseconds':0,'stalelockseconds':43200,'batchlimit':1,'batchsort':'oldestfirst','resumeincompletebatches':True,'stabilityseconds':0,'maxrunhours':10,'batchlocknames':['.workflow.lock','.lock'],'datereconstruction':{'mode':'legacybash','decadeprefix':'202','yeardigitindex':3}},'automation':{'mode':'assistedreview','automaticphase2enabled':False,'approvalfile':'data/TEMP/WORKFLOW_DATA/runtime/automation-approval.json','minimumstatus':'eligibleconservative'},'culling':{'enabled':True,'movefiles':True,'keepthreshold':.65,'rejectthreshold':.35,'autokeepminrating':2,'finalcomponentweights':{'basescore':.55,'eyescore':.1,'personalscore':.2,'familyscore':.15},'baseweights':{'sharpness':.35,'aesthetic':.35,'exposure':.2,'referencescore':.1},'starratingbands':[{'min':0,'max':.19,'rating':0},{'min':.2,'max':.39,'rating':1},{'min':.4,'max':.59,'rating':2},{'min':.6,'max':.74,'rating':3},{'min':.75,'max':.89,'rating':4},{'min':.9,'max':1,'rating':5}]},'seriesdetection':{'enabled':True,'clustereps':.18,'minsamples':2,'reviewmargin':.03,'demotenonbestto':'review'},'personalscoring':{'enabled':False,'modelpath':'data/TEMP/WORKFLOW_DATA/models/taste/active.json'},'familyrecognition':{'enabled':False,'backend':'face_recognition','referencedir':'data/TEMP/WORKFLOW_DATA/samples/family','cachedir':'data/TEMP/WORKFLOW_DATA/runtime/family','maxreferenceimagesperperson':10,'minreferenceimagesperperson':2,'matchtolerance':.45,'protectmatches':True,'candidatecropsenabled':False,'minbestsecondmargin':.08,'minfacesizepx':80,'cropmarginpx':12,'mincropsharpness':.08,'mincropexposure':.35},'metadataculling':{'enabled':False,'exiftoolpath':'exiftool','allowrecoverysidecar':False,'writerating':True,'writekeywords':True,'required':False},'manualkeep':{'enabled':True,'similaritythreshold':.95,'minimummargin':.03},'runtime':{'root':'data/TEMP/WORKFLOW_DATA/runtime','state':'data/TEMP/WORKFLOW_DATA/runtime/state','runsummaries':'data/TEMP/WORKFLOW_DATA/runtime/runsummaries','calibrationbatches':'data/TEMP/WORKFLOW_DATA/runtime/calibration/batches','calibrationindex':'data/TEMP/WORKFLOW_DATA/runtime/calibration/decisionindex.jsonl','calibrationsummary':'data/TEMP/WORKFLOW_DATA/runtime/calibration/calibrationsummary.json','quarantine':'data/TEMP/WORKFLOW_DATA/runtime/quarantine'},'calibration':{'enabled':True,'minimumreviewedbatches':3,'minimumreviewedimages':300,'minterminaldecisionagreement':.9,'maxrejecttokeeprate':0.0},'models':{'version':'rule-v1'},'samples':{'root':'data/TEMP/WORKFLOW_DATA/samples','candidatesenabled':False,'candidatequalitymin':.75,'candidateratingmin':5,'candidatenoveltymin':.15},'training':{'minlabeledimages':4}}
def deep(a,b):
 for k,v in b.items():a[k]=deep(a.get(k,{}) if isinstance(a.get(k),dict) else {},v) if isinstance(v,dict) else v
 return a
def configfingerprint(c):
 x={k:v for k,v in c.items() if k not in ('paths','runtime')};return canonical_hash(x)
def loadconfig(path):
 c=deep(defaults(),yaml.safe_load(Path(path).read_text()) or {})
 old=c['culling'].get('decisionmode'); mode=c['automation']['mode']
 if old:
  alias={'manual':'assistedreview','assistedreview':'assistedreview','automatic':'automaticphase2','automaticphase2':'automaticphase2'}.get(old)
  if alias is None or (mode!='assistedreview' and mode!=alias):raise ValueError('CONFIGINVALID culling.decisionmode conflicts with automation.mode')
  c['automation']['mode']=alias
 if c['workflow']['phaseexecution'] not in ('phase1thenphase2','phase1only','phase2only'):raise ValueError('CONFIGINVALID workflow.phaseexecution')
 if c['automation']['mode'] not in ('assistedreview','automaticphase2','automaticphase2conservative'):raise ValueError('CONFIGINVALID automation.mode')
 if not 0<=c['culling']['rejectthreshold']<c['culling']['keepthreshold']<=1:raise ValueError('CONFIGINVALID thresholds')
 finalweights=c['culling']['finalcomponentweights']; expected={'basescore','eyescore','personalscore','familyscore'}
 if set(finalweights)!=expected or any(not isinstance(v,(int,float)) or v<0 for v in finalweights.values()) or sum(finalweights.values())<=0:raise ValueError('CONFIGINVALID finalcomponentweights')
 baseweights=c['culling']['baseweights']; baseexpected={'sharpness','aesthetic','exposure','referencescore'}
 if set(baseweights)!=baseexpected or any(not isinstance(v,(int,float)) or v<0 for v in baseweights.values()) or sum(baseweights.values())<=0:raise ValueError('CONFIGINVALID baseweights')
 for band in c['culling']['starratingbands']:
  if not isinstance(band.get('rating'),int) or not 0<=band.get('min',-1)<=band.get('max',2)<=1:raise ValueError('CONFIGINVALID starratingbands')
 for k,v in c['paths'].items():
  if k not in ('basedir',) and not within(c['paths']['basedir'],v):raise ValueError('CONFIGINVALID path outside basedir:'+k)
 return c
def automatic_phase2_gate(c):
 a=c['automation'];mode=a['mode']
 if mode=='assistedreview':return False,['assistedreview']
 if not a.get('automaticphase2enabled',False):return False,['automaticphase2disabled']
 if c['workflow']['phaseexecution']!='phase1thenphase2':return False,['phaseexecutionnotcombined']
 try:summary=json.loads(Path(c['runtime']['calibrationsummary']).read_text(encoding='utf8'))
 except (OSError,ValueError):return False,['calibrationsummarymissing']
 if summary.get('configfingerprint')!=configfingerprint(c) or summary.get('modelversion')!=c['models']['version']:return False,['calibrationcontextmismatch']
 allowed=('eligibleautomaticphase2',) if mode=='automaticphase2' else ('eligibleconservative','eligibleautomaticphase2')
 if summary.get('status') not in allowed:return False,['calibrationnoteligible:'+str(summary.get('status'))]
 try:approval=json.loads(Path(a['approvalfile']).read_text(encoding='utf8'))
 except (OSError,ValueError):return False,['approvalmissing']
 if approval.get('approved') is not True or approval.get('configfingerprint')!=configfingerprint(c) or approval.get('modelversion')!=c['models']['version'] or approval.get('calibrationrecordshash')!=summary.get('recordshash') or approval.get('status')!=summary.get('status'):return False,['approvalinvalid']
 return True,[]
def write_automation_approval(c):
 try:summary=json.loads(Path(c['runtime']['calibrationsummary']).read_text(encoding='utf8'))
 except (OSError,ValueError):raise ValueError('CALIBRATIONSUMMARYMISSING')
 approved={'schemaversion':1,'approved':True,'approvedat':utcnow(),'configfingerprint':configfingerprint(c),'modelversion':c['models']['version'],'calibrationrecordshash':summary.get('recordshash'),'status':summary.get('status')}
 atomic_json(c['automation']['approvalfile'],approved);return approved
@contextmanager
def lock(c):
 p=Path(c['paths']['lockfile']);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and time.time()-p.stat().st_mtime<c['workflow']['stalelockseconds']:raise RuntimeError('LOCKACTIVE')
 if p.exists():p.unlink()
 p.write_text(json.dumps({'pid':os.getpid(),'startedat':utcnow()}))
 try:yield
 finally:
  if p.exists():p.unlink()
def files(d, ext):return [p for p in Path(d).iterdir() if p.is_file() and not p.is_symlink() and p.suffix.lower() in ext]
def makedatename(n,c):
 return date_name(n,c)
def date_name(n,c):
 d=c['workflow']['datereconstruction']; m=re.fullmatch(r'(\d{8})',n)
 if not m:raise ValueError('FOLDERNAMEUNSUPPORTED')
 if d['mode']=='fullyear':year=n[:4]
 elif d['mode']=='legacybash' and str(d['decadeprefix']).isdigit() and len(str(d['decadeprefix']))==3:year=str(d['decadeprefix'])+n[int(d['yeardigitindex'])]
 else:raise ValueError('CONFIGINVALID date')
 from datetime import date
 date(int(year),int(n[4:6]),int(n[6:]));return f'{year}-{n[4:6]}-{n[6:]}'
def folder_fp(d):
 h=hashlib.sha256()
 for p in sorted(x for x in Path(d).rglob('*') if x.is_file() and not x.is_symlink()):h.update(f'{p.relative_to(d)}:{p.stat().st_size}:{p.stat().st_mtime_ns}\n'.encode())
 return h.hexdigest()
def score_folder(c,d,budget=None,resume_rows=None,on_row=None):
 familymodel=loadfamilymodel(c) if c['familyrecognition'].get('enabled',False) else None
 model=loadpersonalmodel(c['personalscoring']['modelpath']) if c['personalscoring']['enabled'] else None; rows=[];resume_rows=resume_rows or {}
 for p in files(d,IMG):
  imageid=sha256(p)
  if imageid in resume_rows:rows.append(resume_rows[imageid]);continue
  if on_row:on_row(None,p.name)
  if budget:budget.checkpoint('score-image')
  try:
   f=extractfeatures(p); comp=basescorecomponents(f,None); base=weightedbasescore(comp,{'sharpscore':c['culling']['baseweights']['sharpness'],'aesthscore':c['culling']['baseweights']['aesthetic'],'exposurescore':c['culling']['baseweights']['exposure'],'referencescore':c['culling']['baseweights']['referencescore']}); personal=personalmodelscore(f,model)
   vals={'basescore':base,'eyescore':None,'personalscore':personal,'familyscore':None}; weights=c['culling']['finalcomponentweights']; active=[k for k in vals if vals[k] is not None and weights[k]>0]
   if not active: raise ValueError('NOSCORECOMPONENT')
   final=sum(float(vals[k])*weights[k] for k in active)/sum(weights[k] for k in active)
   if not 0<=final<=1: raise ValueError('SCOREOUTOFRANGE')
   dec='keep' if final>=c['culling']['keepthreshold'] else 'reject' if final<c['culling']['rejectthreshold'] else 'review'
   people,familystatus=detectfamilymembers(p,familymodel,c) if familymodel else ([], 'disabled')
   protected=bool(people) and c['familyrecognition'].get('protectmatches',True) and dec=='reject'
   if protected:dec='review'
   row={'imageid':imageid,'relativepath':p.name,'basescore':base,'eyescore':None,'personalscore':personal,'familyscore':None,'finalscore':final,'scoredecision':dec,'decision':dec,'finaldecision':dec,'decisionreason':'score','embedding':f['embedding'],'modelversion':c['models']['version'],'configfingerprint':configfingerprint(c),'manualkeep':False,'detectedpeople':people,'familystatus':familystatus,'protectedbyfamilyrule':protected}
  except Exception as e:row={'imageid':imageid,'relativepath':p.name,'basescore':None,'eyescore':None,'personalscore':None,'familyscore':None,'finalscore':0.,'scoredecision':'review','decision':'review','finaldecision':'review','decisionreason':'imagereadfailed','embedding':[0]*10,'modelversion':c['models']['version'],'configfingerprint':configfingerprint(c),'manualkeep':False,'error':str(e)}
  rows.append(row)
  if on_row:on_row(row,p.name)
 rows=applyseriesculling(rows,c); bands={x['rating']:x['min'] for x in c['culling']['starratingbands']}
 for r in rows:r['finaldecision']=r['decision'];r['starrating']=ratingforscore(r['finalscore'],bands)
 return rows
def _cosine(a,b):
 a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float);return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-12))
def _move_no_overwrite(src,dstfolder):
 dstfolder.mkdir(parents=True,exist_ok=True);dst=dstfolder/src.name;n=1
 while dst.exists():dst=dstfolder/(src.stem+f'-extra{n}'+src.suffix);n+=1
 shutil.move(str(src),str(dst));return dst
def apply_manual_keep(c,d,rows):
 mc=c.get('manualkeep',{})
 if not mc.get('enabled',True):return []
 inbox=Path(c['paths']['manualkeepinbox']);used=Path(c['paths']['manualkeepused']);events=[]
 if not inbox.exists():return events
 for candidate in files(inbox,IMG):
  try:vector=extractfeatures(candidate)['embedding']
  except Exception:events.append({'file':candidate.name,'status':'unreadable'});continue
  ranked=sorted(((_cosine(vector,r['embedding']),r) for r in rows),key=lambda x:x[0],reverse=True)
  if not ranked:events.append({'file':candidate.name,'status':'unmatched'});continue
  bestscore,best=ranked[0];second=ranked[1][0] if len(ranked)>1 else -1
  if bestscore>=float(mc.get('similaritythreshold',.95)) and bestscore-second>=float(mc.get('minimummargin',.03)):
   best.update(manualkeep=True,decision='keep',finaldecision='keep',decisionreason='manualkeepmatch');_move_no_overwrite(candidate,used);events.append({'file':candidate.name,'status':'matched','imageid':best['imageid'],'similarity':bestscore})
  else:events.append({'file':candidate.name,'status':'unmatched','similarity':bestscore})
 return events
def write_phase1(c,d,bid,rows):
 save=d/'SAVE';save.mkdir(exist_ok=True); cols=['imageid','relativepath','basescore','eyescore','personalscore','familyscore','finalscore','starrating','scoredecision','finaldecision','decisionreason','seriesid','seriessize','seriesrank','seriesbest','seriesmargintobest','modelversion','configfingerprint']
 with (save/'culling_scores.csv').open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,cols);w.writeheader();w.writerows([{k:r.get(k) for k in cols} for r in rows])
 manifest={'schemaversion':1,'batchid':bid,'completedat':utcnow(),'configfingerprint':configfingerprint(c),'modelversion':c['models']['version'],'images':rows};manifest['manifesthash']=canonical_hash(manifest);atomic_json(save/'phase1_manifest.json',manifest,validate_manifest);return manifest
def move(src,dst):
 if dst.exists():raise SafetyError('MOVEDESTEXISTS')
 shutil.move(str(src),str(dst));return dst
runphase1=phase1 if 'phase1' in globals() else None
def _batch_paths(c, source):
 root=Path(c['paths']['tempsd']); require(root,source)
 if source.is_symlink() or not source.is_dir():raise SafetyError('BATCHINVALIDTYPE')
 for p in source.rglob('*'):
  if p.is_symlink():raise SafetyError('BATCHSYMLINK:'+str(p.relative_to(source)))
def _stable_batch(c,d):
 age=time.time()-d.stat().st_mtime
 if age<float(c['workflow'].get('stabilityseconds',0)):raise SafetyError('BATCHUNSTABLE')
 locks=set(c['workflow'].get('batchlocknames',['.workflow.lock','.lock']))
 active=[p.name for p in d.iterdir() if p.name in locks]
 if active:raise SafetyError('BATCHLOCKACTIVE:'+','.join(sorted(active)))
def _quarantine_batch(c,d,reason):
 src=Path(d); root=Path(c['paths']['tempsd']); require(root,src)
 targetroot=Path(c['paths']['temperror']);targetroot.mkdir(parents=True,exist_ok=True)
 target=targetroot/(src.name+'-'+reason.lower().replace(':','-'))
 n=1;base=target
 while target.exists():target=base.with_name(base.name+f'-extra{n}');n+=1
 shutil.move(str(src),str(target));atomic_json(target/'quarantine.json',{'schemaversion':1,'createdat':utcnow(),'sourcefolder':src.name,'reason':reason})
 return target
def _admit_phase1(c,d):
 _batch_paths(c,d);_stable_batch(c,d);date_name(d.name,c)
 return True
def _phase1_work(path):
 p=Path(path)
 try:
  x=json.loads(p.read_text(encoding='utf8'))
  if x.get('schemaversion')!=1 or not isinstance(x.get('rows'),list):raise ValueError('invalid')
  return {r['imageid']:r for r in x['rows'] if isinstance(r,dict) and r.get('imageid')}
 except FileNotFoundError:return {}
 except (OSError,ValueError,json.JSONDecodeError) as exc:raise SafetyError('PHASE1WORKINVALID') from exc
def _save_phase1_work(path,rows):
 atomic_json(path,{'schemaversion':1,'createdat':utcnow(),'updatedat':utcnow(),'rows':list(rows.values())})
def phase1(c,one=None,budget=None):
 source=Path(one) if one else Path(c['paths']['tempsd']); ds=[source] if one else sorted([p for p in source.iterdir() if p.is_dir() and not p.is_symlink()],key=lambda p:p.stat().st_mtime)
 out=[]
 for d in ds[:c['workflow']['batchlimit'] or None]:
  if budget:budget.checkpoint('phase1-batch')
  try:
   _admit_phase1(c,d)
   if c['familyrecognition'].get('enabled'):
    fm=loadfamilymodel(c)
    if fm.get('status') != 'available': raise SafetyError('FACEMODELREBUILDFAILED:'+str(fm.get('status')))
  except (SafetyError,ValueError) as exc:
   _quarantine_batch(c,d,str(exc));out.append({'sourcefolder':d.name,'status':'quarantined','reason':str(exc)});continue
  name=date_name(d.name,c); fp=folder_fp(d);bid=batch_id(d.name,fp);state=Path(c['runtime']['state'])/(bid+'.json');arw=d/'ARW';arw.mkdir(exist_ok=True)
  if not state.exists():transition(state,'phase1processing',batchid=bid,sourcefolder=d.name,currentpath=str(d),fingerprint=fp,configfingerprint=configfingerprint(c),modelversion=c['models']['version'],runstatus='running',currentstep='phase1-prepare')
  else:mark_running(state,bid,'phase1-resume',currentpath=str(d))
  for p in files(d,RAW):shutil.move(str(p),arw/p.name)
  save=d/'SAVE';save.mkdir(exist_ok=True);verified_zip(files(d,IMG),save/(name+'ALLJPG.zip'),d)
  workpath=save/'phase1_work.json';completed=_phase1_work(workpath)
  def checkpoint_row(row,relativepath):
   if row:completed[row['imageid']]=row;_save_phase1_work(workpath,completed)
   transition(state,'phase1processing',batchid=bid,runstatus='running',currentstep='phase1-scoring',progresscursor=relativepath,completedimages=len(completed))
  try:rows=score_folder(c,d,budget,resume_rows=completed,on_row=checkpoint_row)
  except PauseRequested as exc:
   mark_paused(state,bid,str(exc),'phase1-scoring',progresscursor=load_control(state,'state').get('progresscursor'),completedimages=len(completed));raise
  manualevents=apply_manual_keep(c,d,rows)
  # Suggestions are opt-in and derived only from already-safe keep decisions; they never alter culling.
  facecandidateevents=[]
  if c['familyrecognition'].get('enabled') and c['familyrecognition'].get('candidatecropsenabled'):
   from app.familyrecognition import propose_known_face_crops
   fm=loadfamilymodel(c)
   for r in rows:
    if budget:budget.checkpoint('face-candidate')
    facecandidateevents.extend(propose_known_face_crops(d/r['relativepath'],fm,c,r.get('finaldecision')))
  sampleevents=[]
  sc=c.get('samples',{})
  if sc.get('candidatesenabled',False):
   from app.samples import propose_sample
   existing={x.get('imageid') for x in rows if x.get('finaldecision')=='keep'}
   for r in rows:
    if budget:budget.checkpoint('sample-candidate')
    if r.get('finaldecision')!='keep' or r.get('rating',0)<int(sc.get('candidateratingmin',5)) or r.get('finalscore',0)<float(sc.get('candidatequalitymin',.75)):continue
    # Existing candidates are content-hash deduplicated by the candidate service; novelty is conservative score distance.
    novelty=min(1.,abs(float(r['finalscore'])-.5)*2)
    if novelty<float(sc.get('candidatenoveltymin',.15)):continue
    item,status=propose_sample(sc['root'],d/r['relativepath'],r['finalscore'],novelty,r['finalscore'],c['runtime'].get('quarantine'),runid=bid)
    sampleevents.append({'imageid':r['imageid'],'status':status,'candidateid':item.get('candidateid') if item else None})
  for r in rows:
   try:
    if budget:budget.checkpoint('phase1-metadata')
   except PauseRequested as exc:
    mark_paused(state,bid,str(exc),'phase1-metadata',progresscursor=r['relativepath']);raise
   metadatastatus=writecullingmetadata(d/r['relativepath'],r,c)
   if c['metadataculling'].get('enabled') and c['metadataculling'].get('required',False) and metadatastatus!='written':raise SafetyError('METADATAFAILED:'+r['relativepath']+':'+metadatastatus)
   r['metadatastatus']=metadatastatus
  manifest=write_phase1(c,d,bid,rows);manifest['manualkeepevents']=manualevents;manifest['samplecandidateevents']=sampleevents;manifest['facecandidateevents']=facecandidateevents
  for r in rows:
   p=d/r['relativepath']
   if r['finaldecision']!='keep' and p.exists():
    q=d/('Review' if r['finaldecision']=='review' else 'Rejected');q.mkdir(exist_ok=True);shutil.move(str(p),q/p.name)
  automatic,gate_reasons=automatic_phase2_gate(c)
  target=Path(c['paths']['tempdone'] if automatic else c['paths']['tempimages'])/name
  move(d,target);transition(state,'automatichandoff' if automatic else 'phase1completed',batchid=bid,sourcefolder=name,currentpath=str(target),fingerprint=fp,manifesthash=manifest['manifesthash'],configfingerprint=configfingerprint(c),modelversion=c['models']['version'],handoffsource='automatic' if automatic else 'manualreview');out.append({'batchid':bid,'path':str(target),'handoff':'automatic' if automatic else 'manualreview','automationgates':gate_reasons})
 return out
def final_decisions(d,manifest):
 result={};seen=set()
 for x in manifest['images']:
  name=x['relativepath']; hits=[]
  for folder,decision in (('', 'keep'),('Review','review'),('Rejected','reject')):
   p=d/folder/name
   if p.exists():hits.append((decision,p))
  if len(hits)!=1 or x['imageid'] in seen:raise SafetyError('reviewstateinvalid:'+name)
  seen.add(x['imageid']); decision,p=hits[0];x['finalsource']={'keep':'mainfolder','review':'reviewfolder','reject':'rejectedfolder'}[decision];x['finalrelativepath']=str(p.relative_to(d));result[x['imageid']]=decision
 return result
def _raw_plan(d, arw, active):
 fileset=[p for p in arw.rglob('*') if p.is_file() and not p.is_symlink() and p.suffix.lower() in RAW] if arw.exists() else []
 selected=[p for p in fileset if p.stem.lower() not in active]
 entries=[{'relativepath':str(p.relative_to(d)).replace('\\','/'),'sha256':sha256(p),'size':p.stat().st_size} for p in sorted(selected)]
 return entries,canonical_hash(entries)
def _validate_plan(d,entries):
 for item in entries:
  p=d/item['relativepath'];require(d,p)
  if not p.exists():continue # already safely deleted after archive activation
  if p.is_symlink() or not p.is_file() or sha256(p)!=item['sha256'] or p.stat().st_size!=item['size']:raise SafetyError('ARCHIVEPLANMISMATCH:'+item['relativepath'])
def phase2(c,one=None,dry=False,budget=None):
 root=Path(c['paths']['tempdone'])
 if one:ds=[Path(one)]
 else:
  available={str(p.resolve()):p for p in root.iterdir() if p.is_dir() and not p.is_symlink()}
  paused=[]
  if c['workflow'].get('resumeincompletebatches',True):
   for _,_,st in resumable_states(c['runtime']['state']):
    candidate=st.get('currentpath')
    if candidate and str(Path(candidate).resolve()) in available:paused.append(available[str(Path(candidate).resolve())])
  rest=[p for p in sorted(available.values(),key=lambda x:x.stat().st_mtime) if p not in paused];ds=paused+rest
 out=[]
 for d in ds[:c['workflow']['batchlimit'] or None]:
  if budget:budget.checkpoint('phase2-batch')
  require(root,d);manifest=validate_manifest(json.loads((d/'SAVE/phase1_manifest.json').read_text()));bid=manifest['batchid'];statepath=Path(c['runtime']['state'])/(bid+'.json');state=load_control(statepath,'state')
  if state.get('runstatus')=='paused':mark_running(statepath,bid,'phase2-resume')
  if state['state']=='phase2completed':out.append({'batchid':bid,'status':'alreadycompleted'});continue
  decisions=final_decisions(d,manifest);arw=d/'ARW';active={p.stem.lower() for p in files(d,IMG)};planned,planhash=_raw_plan(d,arw,active)
  oldplan=state.get('archiveplan')
  if oldplan and state.get('archiveplanhash')!=canonical_hash(oldplan):raise SafetyError('ARCHIVEPLANHASHINVALID')
  if oldplan:
   _validate_plan(d,oldplan);planned=oldplan;planhash=state['archiveplanhash']
  if dry:out.append({'batchid':bid,'dryrun':True,'wouldarchive':[x['relativepath'] for x in planned],'archiveplanhash':planhash});continue
  manual_handoff=state.get('state') != 'automatichandoff' and state.get('handoffsource','manualreview') != 'automatic'
  if manual_handoff and state['state']=='phase1completed':transition(statepath,'reviewcomparisonpending',batchid=bid)
  if manual_handoff and c['calibration']['enabled'] and state['state'] in ('phase1completed','reviewcomparisonpending'):
   recpath=Path(c['runtime']['calibrationbatches'])/bid/'reviewdecisionrecord.json'
   if recpath.exists():
    rec=json.loads(recpath.read_text())
    if not record_matches(rec,manifest,decisions,configfingerprint(c),c['models']['version']):raise SafetyError('reviewrecordconflict')
   else:
    rec=build_record(bid,manifest,decisions,configfingerprint(c),c['models']['version']);atomic_json(recpath,rec,validate_review_record)
   transition(statepath,'reviewrecordcommitted',batchid=bid);rebuild_index(Path(c['runtime']['calibrationbatches']),c['runtime']['calibrationindex'],c['runtime']['calibrationsummary'],configfingerprint(c),c['models']['version'],c);transition(statepath,'calibrationindexcommitted',batchid=bid)
  state=load_control(statepath,'state');
  if state['state'] in ('calibrationindexcommitted','automatichandoff'):transition(statepath,'phase2archiving',batchid=bid,archiveplan=planned,archiveplanhash=planhash)
  state=load_control(statepath,'state');expected=[x['relativepath'] for x in planned];save=d/'SAVE';save.mkdir(exist_ok=True)
  archive=Path(state['archive']) if state.get('archive') else None
  if archive:
   archivehash=verify_zip(archive,expected,d)
   if archivehash!=state.get('archivehash'):raise SafetyError('ARCHIVEHASHMISMATCH')
  elif planned:
   archive,archivehash=verified_zip([d/x['relativepath'] for x in planned],save/(d.name+'SORTARW.zip'),d)
   transition(statepath,'phase2archiving',batchid=bid,archive=str(archive),archivehash=archivehash,archiveverified=True)
  else: archive=None;archivehash=None;transition(statepath,'phase2archiving',batchid=bid,archive=None,archivehash=None,archiveverified=True)
  # Verification/activation has been committed. Delete only still-present planned files, never a new discovery.
  for item in planned:
   raw=d/item['relativepath']
   if raw.exists():safe_unlink(c,raw)
  if arw.exists() and not any(arw.iterdir()):arw.rmdir()
  (d/'.PROCESSED').write_text(manifest['manifesthash']);transition(statepath,'phase2completed',batchid=bid,archive=str(archive) if archive else None,archivehash=archivehash);out.append({'batchid':bid,'archive':str(archive) if archive else None,'archiveplanhash':planhash})
 return out

def _write_run_summary(c, command, status, result=None, error=None, actions=None):
 runid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:8]
 payload={'schemaversion':1,'runid':runid,'createdat':utcnow(),'updatedat':utcnow(),'producerversion':VERSION,'command':command,'configfingerprint':configfingerprint(c),'requestedautomationmode':c['automation']['mode'],'effectiveautomationmode':c['automation']['mode'],'status':status,'result':result or {},'error':error,'useractionsrequired':actions or []}
 atomic_json(Path(c['runtime']['runsummaries'])/(runid+'.json'),payload,validate_summary);return payload
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);sub=p.add_subparsers(dest='cmd',required=True)
 for x in ('run','phase1','phase2'):
  q=sub.add_parser(x);q.add_argument('--folder');q.add_argument('--dry-run',action='store_true')
 sub.add_parser('rebuild-personal-model');sub.add_parser('rebuild-family-cache');sub.add_parser('automation-status');sub.add_parser('approve-automatic-phase2');a=p.parse_args(argv);c=loadconfig(a.config)
 for x in list(c['paths'].values())+list(c['runtime'].values()):Path(x).parent.mkdir(parents=True,exist_ok=True)
 budget,oldsignal=install_budget(c)
 try:
  with lock(c):
   ensure_selection(c['samples']['root'],quarantine_dir=c['runtime'].get('quarantine'))
   if a.cmd=='phase1':r=phase1(c,a.folder,budget)
   elif a.cmd=='phase2':r=phase2(c,a.folder,a.dry_run,budget)
   elif a.cmd=='run':
    m=c['workflow']['phaseexecution'];r={'phase1':phase1(c,budget=budget) if m in ('phase1only','phase1thenphase2') else [],'phase2':phase2(c,dry=a.dry_run,budget=budget) if m in ('phase2only','phase1thenphase2') else []}
   elif a.cmd=='rebuild-personal-model':from app.training import trainfromdirectory;r=trainfromdirectory(c)
   elif a.cmd=='rebuild-family-cache':from app.familyrecognition import rebuildfamilycache;r=rebuildfamilycache(c)
   elif a.cmd=='automation-status':
    enabled,reasons=automatic_phase2_gate(c);r={'automaticphase2permitted':enabled,'reasons':reasons}
   else:r=write_automation_approval(c)
  summary=_write_run_summary(c,a.cmd,'success',r);print(json.dumps(summary,ensure_ascii=False));return 0
 except PauseRequested as exc:
  summary=_write_run_summary(c,a.cmd,'paused',error=str(exc),actions=[{'priority':'high','code':'resume_required','message':str(exc)}]);print(json.dumps(summary,ensure_ascii=False),file=sys.stderr);return 75
 except Exception as exc:
  summary=_write_run_summary(c,a.cmd,'failed',error=str(exc),actions=[{'priority':'high','code':'runfailed','message':str(exc)}]);print(json.dumps(summary,ensure_ascii=False),file=sys.stderr);return 1
 finally:restore_budget(oldsignal)

if __name__=='__main__': raise SystemExit(main())

# Backward-compatible public aliases
runphase1 = phase1
runphase2 = phase2
