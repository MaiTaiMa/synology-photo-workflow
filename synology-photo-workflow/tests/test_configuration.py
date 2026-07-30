"""Projekt: Synology Photo Workflow
Datei: app/archives.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Automatisierte Prüfung der Projektlogik, Skripte und Verträge.
"""

from pathlib import Path


def test_config_yaml_exists_and_is_versioned():
    root = Path(__file__).parents[1] / 'config' / 'config.yaml'
    content = root.read_text(encoding='utf-8')
    assert 'paths:' in content
    assert 'workflow:' in content
    assert 'basedir:' in content
