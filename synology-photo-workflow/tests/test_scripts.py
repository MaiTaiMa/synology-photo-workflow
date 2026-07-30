"""Projekt: Synology Photo Workflow
Datei: tests/test_scripts.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Automatisierte Prüfung der Projektlogik, Skripte und Verträge.
"""

from pathlib import Path


def test_scripts_exist():
    root = Path(__file__).parents[1] / 'scripts'
    expected = ['preflight.sh', 'dsm-acceptance-preflight.sh', 'run-phase1.sh', 'run-phase2.sh', 'run-workflow.sh']
    assert all((root / name).is_file() for name in expected)


def test_no_numeric_suffix_scripts_remain():
    root = Path(__file__).parents[1] / 'scripts'
    assert not any(p.name.endswith(('-2.sh', '-3.sh', '-4.sh', '-5.sh')) for p in root.glob('*.sh'))
