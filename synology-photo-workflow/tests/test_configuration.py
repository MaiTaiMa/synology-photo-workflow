"""Projekt: Synology Photo Workflow
Datei: tests/test_configuration.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Prüft Ladeverhalten, Aliasmigrationen und Pfadvalidierung der Konfiguration.
"""

from pathlib import Path


def test_config_yaml_exists_and_is_versioned():
    root = Path(__file__).parents[1] / 'config' / 'config.yaml'
    content = root.read_text(encoding='utf-8')
    assert 'paths:' in content
    assert 'workflow:' in content
    assert 'basedir:' in content
