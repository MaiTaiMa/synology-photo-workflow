from __future__ import annotations
from pathlib import Path
import json, math
import numpy as np
from PIL import Image, ImageFilter, ImageStat

def _clamp(x): return float(max(0., min(1., x)))
def extractfeatures(path, previewsize=32):
    with Image.open(path) as im:
        im=im.convert("RGB"); width,height=im.size; a=np.asarray(im.resize((previewsize,previewsize)),dtype=np.float32)/255
        gray=np.mean(a,axis=2); edge=np.asarray(im.resize((previewsize,previewsize)).convert("L").filter(ImageFilter.FIND_EDGES),dtype=np.float32)/255
    return {"megapixels":width*height/1e6,"aspect":width/max(height,1),"filesize":Path(path).stat().st_size,"brightness":float(gray.mean()),"contrast":float(gray.std()),"saturation":float((a.max(2)-a.min(2)).mean()),"edgevariance":float(edge.var()),"embedding":np.r_[a.mean((0,1)),a.std((0,1)),gray.mean(),gray.std(),edge.mean(),edge.std()].tolist()}
def genericaestheticscore(f):
    resolution=_clamp(math.log1p(f['megapixels'])/math.log(25)); aspect=_clamp(1-abs(math.log(max(f['aspect'],.01)/(3/2)))/1.2)
    sharp=_clamp(math.log1p(f['edgevariance']*100)/math.log(4)); brightness=_clamp(1-abs(f['brightness']-.5)*2); contrast=_clamp(f['contrast']/.25); saturation=_clamp(f['saturation']/.45)
    return _clamp(.25*resolution+.15*aspect+.25*sharp+.2*brightness+.1*contrast+.05*saturation)
def basescorecomponents(f, reference_score=None):
    sharp=_clamp(math.log1p(f['edgevariance']*100)/math.log(4)); aesth=genericaestheticscore(f); exposure=_clamp(.65*(1-abs(f['brightness']-.5)*2)+.35*_clamp(f['contrast']/.2))
    return {'sharpscore':sharp,'aesthscore':aesth,'exposurescore':exposure,'referencescore':reference_score}
def _weighted(values, weights):
    active=[(values[k],weights.get(k,0)) for k in values if values[k] is not None and weights.get(k,0)>0]
    return None if not active else sum(v*w for v,w in active)/sum(w for _,w in active)
def weightedbasescore(c, weights): return _weighted({'sharpscore':c['sharpscore'],'aesthscore':c['aesthscore'],'exposurescore':c['exposurescore'],'referencescore':c.get('referencescore')},weights)
def ensurereferenceprofile(cfg):
    folder=Path(cfg.get('referencescoring',{}).get('folder','')); cache=Path(cfg.get('referencescoring',{}).get('cachedir',''))/'profile.json'
    if not folder.exists(): return None
    files=[p for p in folder.rglob('*') if p.suffix.lower() in {'.jpg','.jpeg','.png'} and not p.is_symlink()]
    if not files:return None
    vectors=[]
    for p in files:
        try:vectors.append(extractfeatures(p,cfg.get('referencescoring',{}).get('previewsize',32))['embedding'])
        except Exception:pass
    if not vectors:return None
    profile=np.mean(vectors,axis=0);cache.parent.mkdir(parents=True,exist_ok=True);cache.write_text(json.dumps(profile.tolist()));return profile.tolist()
def reference_score(features, profile):
    if profile is None:return None
    a=np.asarray(features['embedding']);b=np.asarray(profile);return _clamp((float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-12))+1)/2)
def loadpersonalmodel(path):
    try:return json.loads(Path(path).read_text())
    except (OSError,json.JSONDecodeError):return None
def personalmodelscore(features, model):
    if not model:return None
    if model.get('modeltype')=='prototypev1':
        vals=[]
        for k,m in model.get('mean',{}).items():
            if k in features and model.get('std',{}).get(k,0)>0: vals.append(abs(features[k]-m)/model['std'][k])
        return _clamp(1-min(1,np.mean(vals)/2.5)) if vals else None
    score=model.get('intercept',0)+sum(model.get('weights',{}).get(k,0)*features.get(k,0) for k in model.get('weights',{}))
    return _clamp((score-model.get('scoreoffset',0))/max(model.get('scorescale',1),1e-9))
