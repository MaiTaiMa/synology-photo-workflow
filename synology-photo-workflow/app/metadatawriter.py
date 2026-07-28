from pathlib import Path
import json, shutil, subprocess
MANAGED_PREFIXES=('workflowaicull','workflowmodel','decisionpredicted','decisionfinal','seriesid','seriesrole','familymatch','person','scoreband','whatsappmanualkeep')
def buildcullingkeywords(row):
 out=['workflowaicull','workflowmodel'+str(row.get('modelversion','rule-v1')),'decisionpredicted'+row.get('scoredecision','review'),'decisionfinal'+row.get('finaldecision',row.get('decision','review')),'scoreband'+str(row['starrating'])]
 if row.get('seriesid'):out+=['seriesid'+row['seriesid'],'seriesrole'+('best' if row.get('seriesbest') else 'member')]
 if row.get('protectedbyfamilyrule'):out+=['familymatchtrue']
 out += ['person'+p for p in row.get('detectedpeople',[])]
 if row.get('manualkeep'):out+=['whatsappmanualkeep']
 return sorted(set(out))
def _run(args,timeout=30):
 try:return subprocess.run(args,capture_output=True,text=True,timeout=timeout,check=False)
 except (OSError,subprocess.TimeoutExpired):return None
def _read(exe,path):
 r=_run([exe,'-j','-XMP:Rating','-XMP-dc:Subject',str(path)])
 if not r or r.returncode:return None
 try:return json.loads(r.stdout)[0]
 except (ValueError,IndexError):return None
def writecullingmetadata(path,row,cfg):
 c=cfg['metadataculling']
 if not c.get('enabled',True):return 'disabled'
 exe=c.get('exiftoolpath','exiftool')
 if not shutil.which(exe):return 'exiftoolmissing'
 expected=buildcullingkeywords(row);args=[exe]
 if not c.get('keepbackup',False):args.append('-overwrite_original')
 if c.get('writerating',True):args.append(f'-XMP:Rating={row["starrating"]}')
 if c.get('writekeywords',True):args.extend(f'-XMP-dc:Subject+={k}' for k in expected)
 args.append(str(path));result=_run(args)
 if not result or result.returncode:return 'writefailed'
 observed=_read(exe,path)
 if observed is None:return 'readbackfailed'
 subjects=observed.get('Subject',[]);subjects=[subjects] if isinstance(subjects,str) else subjects
 if c.get('writerating',True) and str(observed.get('Rating'))!=str(row['starrating']):return 'readbackfailed'
 if c.get('writekeywords',True) and not set(expected).issubset(set(subjects)):return 'readbackfailed'
 return 'written'
