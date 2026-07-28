"""Immutable manual-review records and deterministic calibration summaries."""
from __future__ import annotations
import json
from pathlib import Path
from app.state import atomic_json,canonical_hash,utcnow,validate_review_record
VALID={'keep','review','reject'}
def correction(pred,final,manual=False):
 if manual:return 'manualkeep'
 if pred==final:return 'confirmed'
 return 'promoted' if final=='keep' else 'demoted'
def build_record(batchid,manifest,decisions,configfingerprint,modelversion,reviewedat=None):
 images=[]
 for x in manifest['images']:
  final=decisions[x['imageid']]
  if final not in VALID:raise ValueError('INVALIDFINALDECISION')
  images.append({'imageid':x['imageid'],'phase1relativepath':x['relativepath'],'predicteddecision':x['finaldecision'],'predictedprobabilities':{'keep':None,'review':None,'reject':None},'finaldecision':final,'correctiontype':correction(x['finaldecision'],final,x.get('manualkeep',False)),'finalscore':x['finalscore'],'modelconfidence':round(abs(float(x['finalscore'])-0.5)*2,6),'features':{'basescore':x['basescore'],'personalscore':x.get('personalscore'),'familyscore':x.get('familyscore'),'seriesrank':x.get('seriesrank',0)},'finaldecisionsource':x['finalsource'],'finalrelativepath':x['finalrelativepath']})
 record={'schemaversion':1,'recordid':batchid+'-review-v1','batchid':batchid,'handoffsource':'manualreview','phase1completedat':manifest['completedat'],'reviewedat':reviewedat or utcnow(),'configfingerprint':configfingerprint,'modelversion':modelversion,'images':images,'counts':{k:sum(i['finaldecision']==k for i in images) for k in sorted(VALID)},'integrity':{'phase1manifesthash':manifest['manifesthash']}}
 record['recordhash']=canonical_hash(record);validate_review_record(record);return record
def record_matches(existing,manifest,decisions,configfp,modelversion):
 try:
  validate_review_record(existing)
  if existing['integrity']['phase1manifesthash']!=manifest['manifesthash'] or existing['configfingerprint']!=configfp or existing['modelversion']!=modelversion:return False
  return {x['imageid']:x['finaldecision'] for x in existing['images']}==decisions
 except (KeyError,ValueError):return False
def load_records(recordsroot,configfp,modelversion):
 records=[];invalid=[]
 for p in sorted(Path(recordsroot).rglob('reviewdecisionrecord.json')):
  try:
   r=json.loads(p.read_text(encoding='utf8'));validate_review_record(r)
   if r['configfingerprint']==configfp and r['modelversion']==modelversion:records.append(r)
  except (OSError,ValueError,json.JSONDecodeError):invalid.append(str(p))
 return sorted(records,key=lambda r:(r['reviewedat'],r['recordid']),reverse=True),invalid
def _window(records,c):
 selected=records[:int(c.get('evaluationwindow',{}).get('reviewedbatches',10))]
 limit=int(c.get('evaluationwindow',{}).get('reviewedimages',1000));rows=[];complete=[]
 for r in selected:
  if len(rows)+len(r['images'])>limit:break
  complete.append(r);rows.extend((r,x) for x in r['images'])
 return complete,rows
def _metrics(rows):
 n=len(rows);xs=[x for _,x in rows];terminal=[x for x in xs if x['predicteddecision'] in ('keep','reject')];den=len(terminal)
 def rate(numerator):return numerator/den if den else None
 same=sum(x['predicteddecision']==x['finaldecision'] for x in xs)
 return {'images':n,'terminalimages':den,'terminalagreement':rate(sum(x['predicteddecision']==x['finaldecision'] for x in terminal)),'rejecttokeeprate':rate(sum(x['predicteddecision']=='reject' and x['finaldecision']=='keep' for x in terminal)),'rejecttoreviewrate':rate(sum(x['predicteddecision']=='reject' and x['finaldecision']=='review' for x in terminal)),'keeptorejectrate':rate(sum(x['predicteddecision']=='keep' and x['finaldecision']=='reject' for x in terminal)),'reviewrate':sum(x['predicteddecision']=='review' for x in xs)/n if n else None,'overallagreement':same/n if n else None}
def _status(records,rows,metrics,c,invalid):
 reasons=[]
 minb=int(c['minimumreviewedbatches']);mini=int(c['minimumreviewedimages'])
 if invalid:reasons.append('invalidrecords')
 if not records or not rows:return 'collecting','continueassistedreview',reasons+['noreviewdata']
 if len(records)<minb or len(rows)<mini:
  return ('learning' if len(records)>1 else 'collecting'),'continueassistedreview',reasons+['insufficientreviewdata']
 critical=(metrics['terminalagreement'] is None or metrics['terminalagreement']<c.get('minterminaldecisionagreement',.9) or metrics['rejecttokeeprate'] is None or metrics['rejecttokeeprate']>c.get('maxrejecttokeeprate',0.0) or metrics['rejecttoreviewrate'] is not None and metrics['rejecttoreviewrate']>c.get('maxrejecttoreviewrate',.01))
 if critical:return 'noteligible','assistedreviewrequired',reasons+['criticalmetric']
 if len(records)>=10:return 'eligibleautomaticphase2','userapprovalrequired',reasons
 if len(records)>=minb:return 'eligibleconservative','userapprovalrequired',reasons
 return 'promising','continueassistedreview',reasons

def _trend(current,previous):
 if not previous:return {'available':False}
 old=previous.get('metrics',{});return {'available':True,**{k:(round(current.get(k)-old[k],12) if current.get(k) is not None and old.get(k) is not None else None) for k in ('terminalagreement','overallagreement','rejecttokeeprate','keeptorejectrate','reviewrate')}}
def rebuild_index(recordsroot,output,summary,configfp,modelversion,cfg):
 records,invalid=load_records(recordsroot,configfp,modelversion);window,rows=_window(records,cfg['calibration']);metrics=_metrics(rows);status,nextaction,reasons=_status(window,rows,metrics,cfg['calibration'],invalid)
 previous=None
 try:previous=json.loads(Path(summary).read_text(encoding='utf8'))
 except (OSError,ValueError,json.JSONDecodeError):pass
 payload={'schemaversion':1,'createdat':utcnow(),'updatedat':utcnow(),'producerversion':'7.1.0','scopeid':'calibration','configfingerprint':configfp,'modelversion':modelversion,'recordcount':len(records),'imagecount':sum(len(r['images']) for r in records),'evaluationwindow':{'records':len(window),'images':len(rows)},'metrics':metrics,'trend':_trend(metrics,previous),'status':status,'recommendation':status,'reasons':reasons,'nextaction':nextaction,'recordids':[r['recordid'] for r in window]};payload['recordshash']=canonical_hash(payload['recordids']);atomic_json(summary,payload)
 Path(output).parent.mkdir(parents=True,exist_ok=True);tmp=Path(output).with_suffix('.tmp')
 with tmp.open('w',encoding='utf8') as f:
  for r,x in rows:f.write(json.dumps({'recordid':r['recordid'],**x},ensure_ascii=False,sort_keys=True)+'\n')
 tmp.replace(output);return payload
