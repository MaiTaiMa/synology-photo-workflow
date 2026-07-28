from pathlib import Path
import re
PATTERNS=[re.compile(r'(?:xmp:)?Rating[^0-9]{0,20}([0-5])',re.I)]
def readrating(imagepath):
 p=Path(imagepath)
 for q in (p.with_suffix('.xmp'),p.with_suffix(p.suffix+'.xmp'),p):
  try:
   t=q.read_bytes().decode('utf-8','ignore')
   for x in PATTERNS:
    m=x.search(t)
    if m:return float(m.group(1))
  except OSError:pass
 return None
