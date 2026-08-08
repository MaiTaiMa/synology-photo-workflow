"""Projekt: Synology Photo Workflow
Datei: app/configuration.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.8.0
Funktion: Lädt, migriert und validiert die vollständige Konfiguration einschließlich sicherer Automatikgates.
SICHERHEIT: Konfigurations- und Lockfehler stoppen vor jeder produktiven Mutation.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from itertools import pairwise
from pathlib import Path
from typing import Any

import yaml

from .safety import block_traversal, within

ALLOWED_TOP = {'paths', 'workflow', 'culling', 'phase2', 'metadata', 'family_recognition', 'automation', 'calibration', 'extensions', 'finalization'}
BACKENDS = {'opencv_yunet_sface_cpu', 'onnx_face_cpu', 'onnx_face_cuda', 'face_recognition_dlib_cpu', 'insightface_onnx'}
HEX64 = 64


def _require(mapping: dict[str, Any], keys: set[str], scope: str) -> None:
    missing = keys - set(mapping)
    if missing:
        raise ValueError(f'CONFIGINVALID missing {scope} keys:{sorted(missing)}')


def _migrate_aliases(data: dict[str, Any]) -> None:
    """Akzeptiert ausschließlich lesend die zwei dokumentierten Alt-Aliase und verweigert Konflikte."""
    culling, automation, family = data.get('culling', {}), data.get('automation', {}), data.get('family_recognition', {})
    legacy_mode = culling.pop('decision_mode', None)
    if legacy_mode is not None:
        mapped = {'assistedreview': 'assisted_review', 'automaticphase2': 'automatic_phase2', 'automaticcandidates': 'automatic_candidates'}.get(legacy_mode, legacy_mode)
        if automation.get('mode') not in (None, mapped):
            raise ValueError('CONFIGINVALID decision_mode conflicts with automation.mode')
        automation['mode'] = mapped
    legacy_metric = family.pop('similarity_metric', None)
    if legacy_metric is not None:
        if family.get('metric') not in (None, legacy_metric):
            raise ValueError('CONFIGINVALID similarity_metric conflicts with metric')
        family['metric'] = legacy_metric


def _reject_unknown(mapping: dict[str, Any], allowed: set[str], scope: str) -> None:
    unknown = set(mapping) - allowed
    if unknown:
        raise ValueError(f'CONFIGINVALID unknown {scope} keys: {sorted(unknown)}')


def _is_hex_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == HEX64 and all(ch in '0123456789abcdefABCDEF' for ch in value)


def _assert_no_secrets(mapping: Any, trail: str = '') -> None:
    if isinstance(mapping, dict):
        for key, value in mapping.items():
            key_l = str(key).lower()
            full = f'{trail}.{key}' if trail else str(key)
            parts = tuple(part for part in re.split(r'[_\-.]+', key_l) if part)
            is_sensitive = (
                key_l in {'api_key', 'apikey', 'client_secret', 'access_key', 'session_token'}
                or any(token in {'password', 'passwd', 'secret', 'token'} for token in parts)
            )
            if is_sensitive and value not in (None, '', False):
                raise ValueError(f'CONFIGINVALID secrets_not_allowed:{full}')
            _assert_no_secrets(value, full)
    elif isinstance(mapping, list):
        for idx, value in enumerate(mapping):
            _assert_no_secrets(value, f'{trail}[{idx}]')


def _resolve_path(raw: str, base_dir: Path) -> Path:
    candidate = Path(raw).expanduser()
    return candidate.resolve() if candidate.is_absolute() else (base_dir / candidate).resolve()


def _validate_model_reference(model_path: str, model_sha256: Any, basedir: Path, models_root: Path, field: str) -> None:
    if not _is_hex_sha256(model_sha256):
        raise ValueError(f'CONFIGINVALID invalid_model_hash:{field}')
    path = _resolve_path(model_path, basedir)
    if not within(models_root, path):
        raise ValueError(f'CONFIGINVALID model_path_outside_models_root:{field}')
    if not path.is_file():
        raise ValueError(f'CONFIGINVALID model_missing:{field}')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest.lower() != str(model_sha256).lower():
        raise ValueError(f'CONFIGINVALID model_hash_mismatch:{field}')


def validate_schema(config_dict: dict[str, Any]) -> None:
    """Strikte Schema-Validierung; unbekannte Schlüssel sind Fehler (außer `extensions`)."""
    if not isinstance(config_dict, dict):
        raise TypeError('CONFIGINVALID root_not_mapping')
    _reject_unknown(config_dict, ALLOWED_TOP, 'top-level')
    _require(config_dict, {'paths', 'workflow', 'culling', 'phase2', 'metadata', 'family_recognition', 'automation', 'calibration'}, 'sections')
    _reject_unknown(config_dict['paths'], {'basedir', 'temp_sd', 'temp_images', 'temp_done', 'temp_error', 'workflow_data', 'manual_keep_inbox', 'manual_keep_used', 'publish_root'}, 'paths')
    _reject_unknown(config_dict['workflow'], {'phase_execution', 'batch_limit', 'batch_sort', 'skip_incomplete_batches', 'max_run_hours', 'resume_incomplete_batches', 'dry_run'}, 'workflow')
    _reject_unknown(config_dict['culling'], {'enabled', 'keep_threshold', 'reject_threshold', 'auto_keep_min_rating', 'final_component_weights', 'base_weights', 'star_rating_bands', 'taste_model', 'decision_mode'}, 'culling')
    _reject_unknown(config_dict['phase2'], {'delete_unneeded_arws_after_verified_archive', 'allow_automatic_handoff'}, 'phase2')
    _reject_unknown(config_dict['metadata'], {'write_mode', 'verify_after_write', 'create_exiftool_backups', 'sidecar_recovery_enabled'}, 'metadata')
    _reject_unknown(config_dict['family_recognition'], {'enabled', 'backend', 'execution_profile', 'metric', 'match_threshold', 'min_best_second_margin', 'backends', 'similarity_metric'}, 'family_recognition')
    _reject_unknown(config_dict['automation'], {'mode', 'automatic_phase2_enabled', 'automatic_candidates_enabled', 'automatic_reference_activation', 'automatic_sample_activation', 'rollback_on_error'}, 'automation')
    _reject_unknown(config_dict['calibration'], {'enabled', 'reviewed_batches_minimum', 'reviewed_images_minimum', 'terminal_agreement_minimum', 'reject_to_keep_rate_maximum', 'shadow_model_enabled'}, 'calibration')
    if 'taste_model' in config_dict['culling']:
        _reject_unknown(config_dict['culling']['taste_model'], {'enabled', 'backend', 'model_path', 'model_sha256', 'positive_prompts', 'negative_prompts'}, 'culling.taste_model')
    if 'finalization' in config_dict and isinstance(config_dict['finalization'], dict):
        _reject_unknown(config_dict['finalization'], {'enabled', 'target_folder'}, 'finalization')


def get_fingerprint(config_dict: dict[str, Any]) -> str:
    """SHA256-Fingerprint der effektiven Konfiguration."""
    payload = json.dumps(config_dict, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def load_config(path: str | Path) -> dict[str, Any]:
    """Lädt YAML, migriert erlaubte Lese-Aliase und löst ausschließlich Pfade unter basedir auf."""
    data = yaml.safe_load(Path(path).read_text(encoding='utf-8')) or {}
    _migrate_aliases(data)
    validate_config(data)
    base = Path(data['paths']['basedir']).expanduser().resolve()
    for key, value in list(data['paths'].items()):
        if key != 'basedir':
            candidate = Path(value)
            data['paths'][key] = str((base / candidate).resolve()) if not candidate.is_absolute() else str(candidate.resolve())
    data['paths']['basedir'] = str(base)
    validate_paths(data)
    _assert_no_secrets(data)
    models_root = Path(data['paths']['workflow_data']) / 'models'
    taste_model = data.get('culling', {}).get('taste_model', {})
    if taste_model.get('enabled'):
        _validate_model_reference(taste_model['model_path'], taste_model.get('model_sha256'), base, models_root, 'culling.taste_model.model_path')
    family = data.get('family_recognition', {})
    if family.get('enabled'):
        backend_name = family.get('backend')
        backend_cfg = family.get('backends', {}).get(backend_name, {})
        for model_key, model_path in backend_cfg.items():
            if model_key.endswith('_model'):
                hash_key = f'{model_key}_sha256'
                _validate_model_reference(model_path, backend_cfg.get(hash_key), base, models_root, f'family_recognition.backends.{backend_name}.{model_key}')
    finalization = data.get('finalization', {})
    if finalization.get('enabled'):
        publish_root = data['paths'].get('publish_root')
        target_folder = finalization.get('target_folder')
        if not publish_root:
            raise ValueError('CONFIGINVALID missing paths.publish_root for finalization')
        if not target_folder:
            raise ValueError('CONFIGINVALID missing finalization.target_folder')
        traversal = block_traversal(str(target_folder))
        if not traversal.allowed:
            raise ValueError(f'CONFIGINVALID invalid finalization.target_folder:{traversal.reason}')
        if not within(publish_root, Path(publish_root) / target_folder):
            raise ValueError('CONFIGINVALID finalization.target_folder outside publish_root')
    return data


def validate_paths(config: dict[str, Any]) -> None:
    """Verweigert jeden normalisierten produktiven Pfad außerhalb des NAS-Basisverzeichnisses."""
    base = config['paths']['basedir']
    for key, value in config['paths'].items():
        if key != 'basedir' and not within(base, value):
            raise ValueError(f'CONFIGINVALID path outside basedir:{key}')


def validate_config(config: dict[str, Any]) -> None:
    """Validiert Schlüssel, Wertebereiche und Sicherheitskombinationen vor Laufbeginn."""
    validate_schema(config)
    workflow = config['workflow']
    if workflow['phase_execution'] not in {'phase1_then_phase2', 'phase1_only', 'phase2_only'} or workflow['batch_sort'] != 'oldest_first' or not isinstance(workflow['batch_limit'], int) or workflow['batch_limit'] < 1:
        raise ValueError('CONFIGINVALID workflow')
    automation = config['automation']
    _require(automation, {'mode', 'automatic_phase2_enabled', 'automatic_candidates_enabled', 'automatic_reference_activation', 'automatic_sample_activation', 'rollback_on_error'}, 'automation')
    if automation['mode'] not in {'assisted_review', 'automatic_phase2', 'automatic_candidates', 'reference_activation'}:
        raise ValueError('CONFIGINVALID automation.mode')
    if automation['mode'] == 'reference_activation' or automation['automatic_reference_activation'] or automation['automatic_sample_activation']:
        raise ValueError('CONFIGINVALID automatic reference/sample activation prohibited')
    if automation['mode'] == 'automatic_phase2' and not (automation['automatic_phase2_enabled'] and workflow['phase_execution'] == 'phase1_then_phase2' and config['phase2']['allow_automatic_handoff']):
        raise ValueError('CONFIGINVALID automatic_phase2 gates')
    if automation['mode'] == 'automatic_candidates' and not automation['automatic_candidates_enabled']:
        raise ValueError('CONFIGINVALID automatic_candidates gate')
    culling = config['culling']
    if not 0 <= culling['reject_threshold'] < culling['keep_threshold'] <= 1:
        raise ValueError('CONFIGINVALID score thresholds')
    weights = culling['final_component_weights']
    if set(weights) != {'base_score', 'eye_score', 'personal_score', 'family_score'} or any(value < 0 for value in weights.values()) or abs(sum(weights.values()) - 1) > 1e-9:
        raise ValueError('CONFIGINVALID final_component_weights')
    bands = culling['star_rating_bands']
    if len(bands) != 6 or bands[0]['min'] != 0 or bands[-1]['max'] != 1 or any(left['max'] > right['min'] for left, right in pairwise(bands)):
        raise ValueError('CONFIGINVALID star_rating_bands')
    face = config['family_recognition']
    if face['backend'] not in BACKENDS or face['execution_profile'] not in {'cpu', 'cuda'}:
        raise ValueError('CONFIGINVALID face backend/profile')
    if face['execution_profile'] == 'cuda' and face['backend'] != 'onnx_face_cuda':
        raise ValueError('CONFIGINVALID cuda profile/backend')
    if face['match_threshold'] is None and face['enabled']:
        pass


def fingerprint(config: dict[str, Any]) -> str:
    """Erzeugt einen stabilen Fingerprint der wirksamen Logik ohne installationsspezifische Pfade."""
    scrubbed = copy.deepcopy(config)
    scrubbed.pop('paths', None)
    return get_fingerprint(scrubbed)


def public_config(config: dict[str, Any]) -> dict[str, Any]:
    """Gibt die secrets-freie Beispielkonfiguration für Diagnoseausgaben zurück."""
    return config
