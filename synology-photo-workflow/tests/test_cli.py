"""tests/test_cli.py

Spezifikation v10.2 - AP6
"""
import subprocess, sys
from .conftest import write_config


def test_canonical_spec_entrypoint_validates_config(tmp_path):
    config = write_config(tmp_path)
    r = subprocess.run(
        [sys.executable, '-m', 'app.photoworkflow', '--config', str(config), 'validate_config'],
        capture_output=True, text=True
    )
    assert r.returncode == 0, r.stderr
    assert '"valid": true' in r.stdout
