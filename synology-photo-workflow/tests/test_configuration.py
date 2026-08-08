"""Projekt: Synology Photo Workflow
Datei: tests/test_configuration.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.9.0
Funktion: Prueft den 01AP-Vertrag fuer Laden, Schema, Fingerprint,
          Secret-Schutz und lokale Modellvalidierung der Konfiguration.
SICHERHEIT: Ungueltige oder secrets-haltige Konfigurationen muessen vor jedem Lauf scheitern.

Aenderungsprotokoll:
  2026-08-08 | 7.9.0 | 01AP-Tests fuer Dataclass-Config, Fingerprint,
                       Secret-Schutz und Modellartefakte ergaenzt.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from app.configuration import Config, get_fingerprint, load_config

from .conftest import write_config


def _read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding='utf-8'))


def test_load_config_returns_dataclass_with_deterministic_fingerprint(tmp_path):
    config_path = write_config(tmp_path)

    config = load_config(config_path)

    assert isinstance(config, Config)
    assert config['paths']['basedir'] == str(tmp_path.resolve())
    assert config['family_recognition']['backend'] == 'opencv_yunet_sface_cpu'
    assert config.fingerprint == load_config(config_path).fingerprint


def test_invalid_config_raises_value_error(tmp_path):
    config_path = write_config(tmp_path, workflow={'batch_limit': 0})

    with pytest.raises(ValueError, match='CONFIGINVALID workflow'):
        load_config(config_path)


def test_unknown_top_level_key_is_rejected_but_extensions_allowed(tmp_path):
    config_path = write_config(tmp_path)
    payload = _read_yaml(config_path)
    payload['extensions']['future_toggle'] = True
    payload['unexpected_section'] = {}
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding='utf-8')

    with pytest.raises(ValueError, match='unknown top-level'):
        load_config(config_path)


def test_fingerprint_is_deterministic_for_equivalent_dicts():
    left = {'workflow': {'batch_limit': 1}, 'paths': {'basedir': '/tmp'}}
    right = {'paths': {'basedir': '/tmp'}, 'workflow': {'batch_limit': 1}}

    assert get_fingerprint(left) == get_fingerprint(right)


def test_enabled_local_taste_model_requires_existing_file_and_matching_hash(tmp_path):
    model_path = tmp_path / 'WORKFLOW_DATA' / 'models' / 'taste' / 'model.safetensors'
    model_path.parent.mkdir(parents=True)
    model_path.write_bytes(b'clip-model')
    config_path = write_config(
        tmp_path,
        culling={
            'taste_model': {
                'enabled': True,
                'model_path': str(model_path),
                'model_sha256': hashlib.sha256(b'clip-model').hexdigest(),
            }
        },
    )

    config = load_config(config_path)

    assert config.culling['taste_model']['enabled'] is True


def test_secret_like_config_entries_are_rejected(tmp_path):
    config_path = write_config(tmp_path)
    payload = _read_yaml(config_path)
    payload['extensions']['session_token'] = 'top-secret'
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding='utf-8')

    with pytest.raises(ValueError, match='secret-like key prohibited'):
        load_config(config_path)


def test_publish_root_and_target_folder_are_validated_when_finalization_enabled(tmp_path):
    publish_root = tmp_path / 'PUBLISH_ROOT'
    publish_root.mkdir(parents=True)
    config_path = write_config(
        tmp_path,
        finalization={
            'enabled': True,
            'publish_to_synology_photos': {
                'enabled': True,
                'target_folder': str(publish_root / 'album'),
            },
        },
    )

    config = load_config(config_path)

    assert config.finalization['publish_to_synology_photos']['target_folder'].endswith('album')
