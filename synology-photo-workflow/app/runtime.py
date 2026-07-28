from __future__ import annotations
import signal,time
from dataclasses import dataclass,field
from app.state import utcnow,transition
class PauseRequested(RuntimeError): pass
@dataclass
class RunBudget:
 maxhours:float
 started:float=field(default_factory=time.monotonic)
 stoprequested:bool=False
 reason:str|None=None
 def __post_init__(self):self.deadline=self.started+max(0.,self.maxhours)*3600
 def request_stop(self,signum=None,frame=None):self.stoprequested=True;self.reason='sigterm' if signum else 'stoprequested'
 def checkpoint(self,step=''):
  if self.stoprequested or time.monotonic()>=self.deadline:
   self.reason=self.reason or 'timebudgetexceeded';raise PauseRequested(self.reason+(':'+step if step else ''))
def install_budget(cfg):
 b=RunBudget(float(cfg['workflow'].get('maxrunhours',10)))
 old=signal.getsignal(signal.SIGTERM);signal.signal(signal.SIGTERM,b.request_stop)
 return b,old
def restore_budget(old):signal.signal(signal.SIGTERM,old)
def mark_paused(statepath,batchid,reason,currentstep,**extra):
 from app.state import load_control
 old=load_control(statepath,'state');return transition(statepath,old['state'],batchid=batchid,runstatus='paused',pausedreason=reason,currentstep=currentstep,pausedat=utcnow(),**extra)
def mark_running(statepath,batchid,currentstep,**extra):
 from app.state import load_control
 old=load_control(statepath,'state');return transition(statepath,old['state'],batchid=batchid,runstatus='running',currentstep=currentstep,pausedreason=None,**extra)
def resumable_states(state_root):
 from pathlib import Path
 from app.state import load_control
 rows=[]
 for p in Path(state_root).glob('*.json'):
  try:
   x=load_control(p,'state')
   if x.get('runstatus')=='paused':rows.append((x.get('updatedat',''),p,x))
  except Exception:continue
 return sorted(rows,key=lambda x:x[0])
