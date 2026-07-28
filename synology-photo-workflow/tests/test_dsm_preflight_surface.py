from pathlib import Path
import subprocess
def test_dsm_preflight_is_non_destructive_and_syntax_valid():
 root=Path(__file__).parents[1];p=root/'scripts/dsm-acceptance-preflight.sh';text=p.read_text()
 assert 'phase1' not in text.lower() and 'phase2' not in text.lower() and 'docker compose config -q' in text
 assert subprocess.run(['sh','-n',str(p)],capture_output=True).returncode==0
