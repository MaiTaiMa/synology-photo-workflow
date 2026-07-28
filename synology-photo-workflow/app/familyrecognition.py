from pathlib import Path
import json,importlib
import numpy as np
from PIL import Image,ImageFilter
from app.state import atomic_json,canonical_hash,utcnow
from app.samples import ensure_selection
from app.candidates import propose
try: face_recognition=importlib.import_module('face_recognition')
except ImportError: face_recognition=None
def _validated_embedding(value):
 if not isinstance(value,(list,tuple)) or not value or not all(isinstance(x,(int,float)) for x in value):raise ValueError('FACEEMBEDDINGINVALID')
 return [float(x) for x in value]
def _smoke_match(people,tolerance):
 for person,refs in people.items():
  for embedding in refs:
   distances=face_recognition.face_distance(refs,embedding)
   if not len(distances) or float(min(distances))>float(tolerance):raise ValueError('FACECACHESMOKEMATCHFAILED:'+person)
def _validate_cache(model):
 if not isinstance(model,dict) or model.get('schemaversion')!=1 or model.get('status')!='available' or not isinstance(model.get('people'),dict) or not isinstance(model.get('fingerprint'),str):raise ValueError('FACECACHEINVALID')
 return model
def rebuildfamilycache(cfg):
 c=cfg['familyrecognition'];root=Path(c['referencedir']);out=Path(c['cachedir']);out.mkdir(parents=True,exist_ok=True);people={};skipped=[]
 if not face_recognition:return {'schemaversion':1,'status':'backendunavailable','people':{},'createdat':utcnow(),'updatedat':utcnow()}
 # Build entirely in memory; the old active cache remains untouched on any source or smoke-test error.
 for persondir in sorted(root.iterdir()) if root.exists() else []:
  if not persondir.is_dir() or persondir.is_symlink():continue
  selection=ensure_selection(persondir,scope='face:'+persondir.name,displayname=persondir.name,quarantine_dir=cfg['runtime'].get('quarantine'))
  enc=[]
  for e in selection['entries']:
   if e['status']!='active':continue
   p=persondir/e['relativepath']
   if not p.is_file() or p.is_symlink():raise ValueError('FACEREFERENCEMISSING:'+str(p))
   x=face_recognition.face_encodings(face_recognition.load_image_file(str(p)))
   if len(x)!=1:raise ValueError('FACEREFERENCEAMBIGUOUS:'+str(p))
   enc.append(_validated_embedding(x[0].tolist()))
  if len(enc)>=int(c['minreferenceimagesperperson']):people[persondir.name]=enc
  elif enc:skipped.append({'person':persondir.name,'reason':'minimumreferences','count':len(enc)})
 _smoke_match(people,c['matchtolerance'])
 model={'schemaversion':1,'status':'available','createdat':utcnow(),'updatedat':utcnow(),'producerversion':'7.1.0','people':people,'skipped':skipped,'metric':{'name':'face_distance','direction':'lower','tolerance':float(c['matchtolerance'])}}
 model['fingerprint']=canonical_hash({'people':people,'metric':model['metric']});_validate_cache(model);atomic_json(out/'familyindex.json',model);return model
def loadfamilymodel(cfg):
 p=Path(cfg['familyrecognition']['cachedir'])/'familyindex.json'
 try:
  x=json.loads(p.read_text());return _validate_cache(x)
 except (OSError,ValueError):return rebuildfamilycache(cfg)
def crop_quality(image,box):
 crop=image.crop(box).convert('L');a=np.asarray(crop,dtype=np.float32)/255.;gradient=np.diff(a,axis=0).var()+np.diff(a,axis=1).var()
 brightness=float(a.mean());clipped=float(((a<.03)|(a>.97)).mean());sharp=float(min(1.,gradient*20));exposure=float(max(0.,1-abs(brightness-.5)*2-clipped))
 return {'sharpness':sharp,'brightness':brightness,'clipped':clipped,'exposure':exposure,'quality':round(.6*sharp+.4*exposure,6)}
def propose_known_face_crops(path,model,cfg,decision='review'):
 if decision!='keep' or not cfg['familyrecognition'].get('candidatecropsenabled',False) or not face_recognition:return []
 try:
  image=face_recognition.load_image_file(str(path));locations=face_recognition.face_locations(image);encodings=face_recognition.face_encodings(image,locations)
 except Exception:return []
 c=cfg['familyrecognition'];out=[]
 for idx,(loc,enc) in enumerate(zip(locations,encodings),1):
  ranked=[]
  for person,refs in model.get('people',{}).items():
   dist=min(face_recognition.face_distance(refs,enc),default=99);ranked.append((float(dist),person))
  ranked.sort();
  if not ranked:continue
  best,person=ranked[0];second=ranked[1][0] if len(ranked)>1 else 99
  # Lower distance is better: tolerance plus required separation makes ambiguous identities ineligible.
  if best>float(c.get('matchtolerance',.45)) or second-best<float(c.get('minbestsecondmargin',.08)):continue
  top,right,bottom,left=loc
  if min(bottom-top,right-left)<int(c.get('minfacesizepx',80)):continue
  try:
   im=Image.open(path);margin=int(c.get('cropmarginpx',12));box=(max(0,left-margin),max(0,top-margin),min(im.width,right+margin),min(im.height,bottom+margin));metrics=crop_quality(im,box)
   if metrics['sharpness']<float(c.get('mincropsharpness',.08)) or metrics['exposure']<float(c.get('mincropexposure',.35)):continue
   crop=im.crop(box);tmp=Path(c['referencedir'])/person/'.candidate-tmp.jpg';tmp.parent.mkdir(parents=True,exist_ok=True);crop.save(tmp,'JPEG',quality=95)
   sizequality=min(1.,min(bottom-top,right-left)/300);quality=round(.7*metrics['quality']+.3*sizequality,6);novelty=min(1.,second-best);confidence=max(0.,1-best/float(c.get('matchtolerance',.45)))
   item,status=propose(tmp.parent,tmp,'face:'+person,quality,novelty,confidence,10,100,cfg['runtime'].get('quarantine'),runid=cfg.get('_runid'),metadata={'facecrop':{'sourcepath':str(path),'boundingbox':[top,right,bottom,left],'cropbox':[box[1],box[2],box[3],box[0]],'marginpx':margin,'bestdistance':best,'seconddistance':second,**metrics}}) ;tmp.unlink(missing_ok=True)
   if item:
    out.append({'person':person,'candidateid':item['candidateid'],'status':status,'bestdistance':best,'seconddistance':second,'quality':quality})
  except Exception:continue
 return out
def detectfamilymembers(path,model,cfg):
 if not cfg['familyrecognition'].get('enabled',False):return [],'disabled'
 if not face_recognition:return [],'backendunavailable'
 if model.get('status')!='available':return [],'cacheunavailable'
 try:found=face_recognition.face_encodings(face_recognition.load_image_file(str(path)))
 except Exception:return [],'imagereadfailed'
 best=[]
 for e in found:
  for name,refs in model.get('people',{}).items():
   if min(face_recognition.face_distance(refs,e),default=99)<=float(cfg['familyrecognition']['matchtolerance']):best.append(name)
 return sorted(set(best)),'matched' if best else 'nomatch'
def writenativetags(*args,**kwargs):return 'notimplemented'
