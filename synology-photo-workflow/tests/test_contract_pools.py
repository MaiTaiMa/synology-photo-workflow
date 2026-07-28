from pathlib import Path
from PIL import Image
import pytest
from app.samples import ensure_selection
from app.state import ContractError

def img(p):p.parent.mkdir(parents=True,exist_ok=True);Image.new('RGB',(10,10)).save(p)
def test_selection_preserves_explicit_status_and_quarantines_invalid(tmp_path):
 root=tmp_path/'samples';img(root/'reference'/'a.jpg');m=ensure_selection(root);m['entries'][0]['status']='manualprotected';from app.state import atomic_json,validate_selection;atomic_json(root/'selection.json',m,validate_selection)
 assert ensure_selection(root)['entries'][0]['status']=='manualprotected'
 (root/'selection.json').write_text('{broken')
 with pytest.raises(ContractError):ensure_selection(root,quarantine_dir=tmp_path/'q')
 assert list((tmp_path/'q').glob('*'))
def test_newrefs_never_enter_active_pool(tmp_path):
 root=tmp_path/'samples';img(root/'reference'/'a.jpg');img(root/'newrefs'/'proposal.jpg');m=ensure_selection(root)
 assert all('newrefs/' not in x['relativepath'] for x in m['entries'])
