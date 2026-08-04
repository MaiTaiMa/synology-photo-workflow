"""tests/test_configuration.py

Spezifikation v10.2 - AP5
"""
from pathlib import Path


def test_config_yaml_exists_and_is_versioned():
    root = Path(__file__).parents[1] / 'config' / 'config.yaml'
    content = root.read_text(encoding='utf-8')
    assert 'paths:' in content
    assert 'workflow:' in content
    assert 'basedir:' in content
