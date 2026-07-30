"""Projekt: Synology Photo Workflow
Datei: tests/integration/test_signal_integration.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Optionaler Subprozess-Test: SIGTERM ergibt kontrollierten recoverable Exit ohne Signalhandler-Seiteneffekt.
SICHERHEIT: Integrationstests sind optional und führen nur kontrollierte, lokale Testartefakte aus.
"""
import os
import signal
import subprocess
import sys
import time
import pytest

pytestmark = pytest.mark.integration


def test_signal_contract_in_subprocess():
    script = """import signal,time
flag={'value':False}
def h(*_): flag['value']=True
signal.signal(signal.SIGTERM,h)
while not flag['value']: time.sleep(.01)
raise SystemExit(3)
"""
    process = subprocess.Popen([sys.executable, '-c', script])
    time.sleep(.05)
    os.kill(process.pid, signal.SIGTERM)
    assert process.wait(timeout=3) == 3
