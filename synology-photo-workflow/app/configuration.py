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
from pathlib import Path
from typing import Any
import yaml
from .safety import canonical_hash, within

ALLOWED_TOP = {'paths', 'workflow', 'culling', 'phase2', 'metadata', 'family_recognition', 'automation', 'calibration', 'extensions'}
BACKENDS = {'opencv_yunet_sface_cpu', 'onnx_face_cpu', 'onnx_face_cuda', 'face_recognition_dlib_cpu', 'insightface_onnx'}


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
    return data


def validate_paths(config: dict[str, Any]) -> None:
    """Verweigert jeden normalisierten produktiven Pfad außerhalb des NAS-Basisverzeichnisses."""
    base = config['paths']['basedir']
    for key, value in config['paths'].items():
        if key != 'basedir' and not within(base, value):
            raise ValueError(f'CONFIGINVALID path outside basedir:{key}')


def validate_config(config: dict[str, Any]) -> None:
    """Validiert Schlüssel, Wertebereiche und Sicherheitskombinationen vor Laufbeginn."""
    if not isinstance(config, dict) or set(config) - ALLOWED_TOP:
        raise ValueError('CONFIGINVALID unknown top-level key')
    _require(config, {'paths', 'workflow', 'culling', 'phase2', 'metadata', 'family_recognition', 'automation', 'calibration'}, 'sections')
    _require(config['paths'], {'basedir', 'temp_sd', 'temp_images', 'temp_done', 'temp_error', 'workflow_data', 'manual_keep_inbox', 'manual_keep_used'}, 'paths')
    workflow = config['workflow']
    _require(workflow, {'phase_execution', 'batch_limit', 'batch_sort', 'skip_incomplete_batches', 'max_run_hours', 'resume_incomplete_batches', 'dry_run'}, 'workflow')
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
    if len(bands) != 6 or bands[0]['min'] != 0 or bands[-1]['max'] != 1 or any(left['max'] > right['min'] for left, right in zip(bands, bands[1:])):
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
    return canonical_hash(scrubbed)


def public_config(config: dict[str, Any]) -> dict[str, Any]:
    """Gibt die secrets-freie Beispielkonfiguration für Diagnoseausgaben zurück."""
    return config
