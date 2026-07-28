from pathlib import Path
import hashlib,subprocess
def test_legacy_script_is_present_unchanged_and_syntax_valid():
 root=Path(__file__).parents[1]; script=root/'legacy/nas_photosort.sh'; recorded=(root/'legacy/SHA256SUMS').read_text().split()[0]
 assert script.exists() and hashlib.sha256(script.read_bytes()).hexdigest()==recorded
 assert subprocess.run(['bash','-n',str(script)],capture_output=True).returncode==0
