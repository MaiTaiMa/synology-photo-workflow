from pathlib import Path
import json,numpy as np
from app.aesthetic import extractfeatures
from app.samples import ensure_selection
from app.state import canonical_hash,atomic_json,utcnow
FEATURES=['megapixels','aspect','filesize','edgevariance']
def _dataset(root):
 selection=ensure_selection(root);rows=[]
 for e in selection['entries']:
  try:rows.append((e,extractfeatures(Path(root)/e['relativepath'])))
  except Exception:continue
 return selection,rows
def buildpersonalmodelfromsamples(root):
 selection,rows=_dataset(root)
 # The manifest mediates the pool: a file without a manifest entry never trains.
 # `reference` entries are positive; explicitly labelled inactive entries are negative.
 rows=[(e,x) for e,x in rows if e.get('status')=='active' or e.get('traininglabel')=='negative']
 if not rows:return None,[]
 X=np.array([[1]+[x[k] for k in FEATURES] for _,x in rows],dtype=float);y=np.array([(e.get('selectionvalue',-1)+1)/2 for e,_ in rows],dtype=float)
 coef=np.linalg.lstsq(X,y,rcond=None)[0]
 labels=[e.get('selectionvalue',-1) for e,_ in rows]
 return {'schemaversion':1,'modeltype':'linearv1','intercept':float(coef[0]),'weights':dict(zip(FEATURES,map(float,coef[1:]))),'scoreoffset':0,'scorescale':1,'trainingrows':len(rows),'positiveexamples':sum(x>0 for x in labels),'negativeexamples':sum(x<0 for x in labels),'samplepoolfingerprint':selection['poolfingerprint'],'features':FEATURES,'createdat':utcnow()},rows

def trainfromdirectory(cfg,images_dir=None,model_out=None):
 root=Path(images_dir or cfg['samples']['root']);model,rows=buildpersonalmodelfromsamples(root);minimum=int(cfg.get('training',{}).get('minlabeledimages',4))
 if not model or len(rows)<minimum or model['positiveexamples']==0 or model['negativeexamples']==0:raise ValueError('INSUFFICIENTBALANCEDSAMPLES')
 model['modelhash']=canonical_hash(model);out=Path(model_out or cfg['personalscoring']['modelpath']);atomic_json(out,model);return model
def loadorrebuildpersonalmodel(cfg):
 from app.aesthetic import loadpersonalmodel
 return loadpersonalmodel(cfg['personalscoring']['modelpath'])
