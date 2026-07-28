from __future__ import annotations
from pathlib import Path
import hashlib, os, shutil, zipfile
class SafetyError(RuntimeError): pass
def within(root, path):
    try:return Path(path).resolve().is_relative_to(Path(root).resolve()) and not Path(path).is_symlink()
    except (OSError,ValueError):return False
def require(root,path):
    if not within(root,path):raise SafetyError(f'PATHESCAPE:{path}')
def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def collision_free(path):
    p=Path(path); n=1
    while p.exists():p=path.with_name(f'{path.stem}EXTRA{n}{path.suffix}');n+=1
    return p
def verified_zip(files, target, root):
    target=collision_free(Path(target)); tmp=target.with_name('.'+target.name+'.tmp')
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
        for f in files:
            require(root,f); z.write(f,Path(f).relative_to(root))
    expected={str(Path(f).relative_to(root)) for f in files}
    with zipfile.ZipFile(tmp) as z:
        if z.testzip() is not None or set(z.namelist())!=expected: raise SafetyError('ZIPVERIFYFAILED')
    os.replace(tmp,target); return target,sha256(target)
def safe_unlink(cfg,path):
    p=Path(path);require(cfg['paths']['basedir'],p)
    if 'ARW' not in p.parts or p.is_symlink() or not p.is_file():raise SafetyError(f'ARWDELETEREFUSED:{p}')
    p.unlink()

def verify_zip(path, expected, root):
    path=Path(path);require(root,path)
    if not path.is_file() or path.is_symlink():raise SafetyError('ZIPMISSING')
    expected=set(expected)
    try:
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None or set(z.namelist())!=expected:raise SafetyError('ZIPVERIFYFAILED')
    except (OSError,zipfile.BadZipFile) as exc:raise SafetyError('ZIPVERIFYFAILED') from exc
    return sha256(path)
