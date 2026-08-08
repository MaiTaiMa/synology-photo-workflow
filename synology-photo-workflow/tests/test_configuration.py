"""Projekt: Synology Photo Workflow
Datei: tests/test_configuration.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Prüft Ladeverhalten, Aliasmigrationen und Pfadvalidierung der Konfiguration.
"""

import hashlib
from pathlib import Path

import pytest
import yaml

from app.configuration import get_fingerprint, load_config, validate_schema

from .conftest import write_config


def test_config_yaml_exists_and_is_versioned():
    root = Path(__file__).parents[1] / 'config' / 'config.yaml'
    content = root.read_text(encoding='utf-8')
    assert 'paths:' in content
    assert 'workflow:' in content
    assert 'basedir:' in content


def test_load_config_accepts_valid_config(tmp_path):
    config_path = write_config(tmp_path)
    config = load_config(config_path)
    assert config['workflow']['phase_execution'] == 'phase1_then_phase2'
    assert Path(config['paths']['basedir']).is_absolute()


def test_load_config_rejects_invalid_thresholds(tmp_path):
    config_path = write_config(tmp_path, culling={'keep_threshold': 0.1, 'reject_threshold': 0.9})
    with pytest.raises(ValueError, match='score thresholds'):
        load_config(config_path)


def test_validate_schema_rejects_unknown_keys_except_extensions(tmp_path):
    cfg_path = write_config(tmp_path)
    config = yaml.safe_load(Path(cfg_path).read_text(encoding='utf-8'))
    config['unexpected'] = {}
    with pytest.raises(ValueError, match='unknown top-level'):
        validate_schema(config)
    del config['unexpected']
    config['extensions'] = {'my_plugin': {'custom_flag': True}}
    validate_schema(config)


def test_get_fingerprint_is_deterministic_for_same_content():
    left = {'b': [2, 1], 'a': {'x': 1}}
    right = {'a': {'x': 1}, 'b': [2, 1]}
    assert get_fingerprint(left) == get_fingerprint(right)


def test_model_path_and_hash_validation(tmp_path):
    models_dir = tmp_path / 'WORKFLOW_DATA' / 'models' / 'taste'
    models_dir.mkdir(parents=True)
    model_path = models_dir / 'model.safetensors'
    model_path.write_bytes(b'model-bytes')
    sha = hashlib.sha256(b'model-bytes').hexdigest()
    config_path = write_config(
        tmp_path,
        culling={
            'taste_model': {
                'enabled': True,
                'backend': 'clip_aesthetic',
                'model_path': str(model_path),
                'model_sha256': sha,
                'positive_prompts': ['good'],
                'negative_prompts': ['bad'],
            }
        },
    )
    config = load_config(config_path)
    assert config['culling']['taste_model']['model_sha256'] == sha


def test_config_rejects_secrets(tmp_path):
    cfg_path = write_config(tmp_path)
    config = yaml.safe_load(Path(cfg_path).read_text(encoding='utf-8'))
    config['extensions'] = {'plugin': {'api_token': 'secret-value'}}
    Path(cfg_path).write_text(yaml.safe_dump(config), encoding='utf-8')
    with pytest.raises(ValueError, match='secrets_not_allowed'):
        load_config(cfg_path)
