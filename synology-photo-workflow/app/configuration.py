"""Projekt: Synology Photo Workflow
Datei: app/configuration.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.9.0
Funktion: Laedt und validiert die zentrale Konfiguration inklusive
          deterministischem Fingerprint, Secret-Pruefung und Modellpfad-Safety.
SICHERHEIT: Ungueltige Konfigurationen stoppen vor jeder produktiven Mutation.

Aenderungsprotokoll:
  2026-08-08 | 7.9.0 | 01AP: Dataclass-Config, striktes Schema, Fingerprint,
                       Secret- und Modellpfadvalidierung ergaenzt.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .safety import SafetyResult, is_within_base, sha256, validate_path

_ALLOWED_TOP_LEVEL = {
    'paths',
    'workflow',
    'culling',
    'face',
    'finalization',
    'reference_pools',
    'phase2',
    'metadata',
    'family_recognition',
    'automation',
    'calibration',
    'extensions',
}
_REQUIRED_TOP_LEVEL = {
    'paths',
    'workflow',
    'culling',
    'finalization',
    'reference_pools',
}
_REQUIRED_PATH_KEYS = {
    'basedir',
    'temp_sd',
    'temp_images',
    'temp_done',
    'temp_error',
    'workflow_data',
    'manual_keep_inbox',
    'manual_keep_used',
}
_ALLOWED_WORKFLOW_PHASES = {'phase1_then_phase2', 'phase1_only', 'phase2_only'}
_ALLOWED_AUTOMATION_MODES = {
    'assisted_review',
    'automatic_phase2',
    'automatic_candidates',
    'reference_activation',
}
_ALLOWED_FACE_BACKENDS = {
    'opencv_yunet_sface_cpu',
    'onnx_face_cpu',
    'onnx_face_cuda',
    'face_recognition_dlib_cpu',
    'insightface_onnx',
}
_SECRET_TOKENS = ('password', 'secret', 'token', 'api_key', 'apikey', 'session')


@dataclass(frozen=True)
class _SectionConfig(Mapping[str, Any]):
    """Read-only Mapping-Wrapper fuer Konfigurationssektionen.

    Bestehender Code kann weiterhin per ['key'] zugreifen, waehrend 01AP
    zugleich explizite Dataclass-Typen fuer die Top-Level-Sektionen erhaelt.
    """

    _data: dict[str, Any]

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return copy.deepcopy(self._data)


@dataclass(frozen=True)
class PathsConfig(_SectionConfig):
    """Read-only Pfadsektion der zentralen Konfiguration."""


@dataclass(frozen=True)
class WorkflowConfig(_SectionConfig):
    """Read-only Workflowsektion der zentralen Konfiguration."""


@dataclass(frozen=True)
class CullingConfig(_SectionConfig):
    """Read-only Cullingsektion der zentralen Konfiguration."""


@dataclass(frozen=True)
class FaceConfig(_SectionConfig):
    """Read-only Facesektion der zentralen Konfiguration."""


@dataclass(frozen=True)
class FinalizationConfig(_SectionConfig):
    """Read-only PHASE3-/Finalisierungssektion der Konfiguration."""


@dataclass(frozen=True)
class ReferencePoolsConfig(_SectionConfig):
    """Read-only Referenzpoolsektion der zentralen Konfiguration."""


@dataclass(frozen=True)
class Config(Mapping[str, Any]):
    """Normierte 01AP-Konfiguration mit kompatiblem Mapping-Zugriff.

    Die benannten Felder bilden den neuen Vertrag aus 00AP/01AP ab. Fuer den
    bestehenden Code koennen zusaetzlich Legacy-Sektionen per ['key'] gelesen
    werden, ohne die 01AP-Schnittstelle zu verbreitern.
    """

    paths: PathsConfig
    workflow: WorkflowConfig
    culling: CullingConfig
    face: FaceConfig
    finalization: FinalizationConfig
    reference_pools: ReferencePoolsConfig
    fingerprint: str
    _legacy_sections: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def _mapping(self) -> dict[str, Any]:
        mapping = {
            'paths': self.paths,
            'workflow': self.workflow,
            'culling': self.culling,
            'face': self.face,
            'finalization': self.finalization,
            'reference_pools': self.reference_pools,
            'fingerprint': self.fingerprint,
        }
        mapping.update(self._legacy_sections)
        if 'family_recognition' not in mapping:
            mapping['family_recognition'] = self.face
        return mapping

    def __getitem__(self, key: str) -> Any:
        return self._mapping()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._mapping())

    def __len__(self) -> int:
        return len(self._mapping())

    def get(self, key: str, default: Any = None) -> Any:
        return self._mapping().get(key, default)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            'paths': self.paths.to_dict(),
            'workflow': self.workflow.to_dict(),
            'culling': self.culling.to_dict(),
            'face': self.face.to_dict(),
            'finalization': self.finalization.to_dict(),
            'reference_pools': self.reference_pools.to_dict(),
            'fingerprint': self.fingerprint,
        }
        for key, value in self._legacy_sections.items():
            if isinstance(value, _SectionConfig):
                result[key] = value.to_dict()
            else:
                result[key] = copy.deepcopy(value)
        result.setdefault('family_recognition', self.face.to_dict())
        return result


def _require(mapping: Mapping[str, Any], keys: set[str], scope: str) -> None:
    """Prueft das Vorhandensein verpflichtender Schluessel je Konfigurationsblock."""

    missing = sorted(keys - set(mapping))
    if missing:
        raise ValueError(f'CONFIGINVALID missing {scope} keys:{missing}')


def _reject_unknown(mapping: Mapping[str, Any], allowed: set[str], scope: str) -> None:
    """Blockiert unbekannte Schluessel, weil 01AP strikte YAML-Schemata fordert."""

    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise ValueError(f'CONFIGINVALID unknown {scope} keys:{unknown}')


def _migrate_aliases(data: dict[str, Any]) -> None:
    """Akzeptiert die dokumentierten Alt-Aliase nur lesend und konfliktfrei."""

    culling = data.get('culling', {})
    automation = data.get('automation', {})
    family = data.get('family_recognition', data.get('face', {}))
    legacy_mode = culling.pop('decision_mode', None)
    if legacy_mode is not None:
        mapped = {
            'assistedreview': 'assisted_review',
            'automaticphase2': 'automatic_phase2',
            'automaticcandidates': 'automatic_candidates',
        }.get(legacy_mode, legacy_mode)
        if automation.get('mode') not in (None, mapped):
            raise ValueError('CONFIGINVALID decision_mode conflicts with automation.mode')
        automation['mode'] = mapped
    legacy_metric = family.pop('similarity_metric', None)
    if legacy_metric is not None:
        if family.get('metric') not in (None, legacy_metric):
            raise ValueError('CONFIGINVALID similarity_metric conflicts with metric')
        family['metric'] = legacy_metric
    if 'face' not in data and data.get('family_recognition') is not None:
        data['face'] = copy.deepcopy(data['family_recognition'])


def _resolve_local_path(value: str, base_dir: Path) -> Path:
    """Loest relative lokale Pfade deterministisch gegen das Basisverzeichnis auf."""

    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate.resolve(strict=False)


def _normalize_paths(config_dict: dict[str, Any]) -> None:
    """Normalisiert alle konfigurierten Pfade kanonisch vor der Validierung."""

    paths = config_dict.get('paths', {})
    basedir = Path(paths['basedir']).expanduser().resolve(strict=False)
    normalized: dict[str, str] = {'basedir': str(basedir)}
    for key, value in paths.items():
        if key == 'basedir':
            continue
        normalized[key] = str(_resolve_local_path(str(value), basedir))
    paths.clear()
    paths.update(normalized)


def _ensure_secret_free(node: Any, trail: tuple[str, ...] = ()) -> None:
    """Blockiert Secrets in config.yaml anhand der Schluesselnamen und Werte."""

    if isinstance(node, Mapping):
        for key, value in node.items():
            lowered = key.lower()
            if any(token in lowered for token in _SECRET_TOKENS) and value not in (
                None,
                '',
                False,
            ):
                joined = '.'.join(trail + (key,))
                raise ValueError(f'CONFIGINVALID secret-like key prohibited:{joined}')
            _ensure_secret_free(value, trail + (key,))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _ensure_secret_free(item, trail + (str(index),))


def _validate_paths(config_dict: dict[str, Any]) -> None:
    """Validiert produktive Pfade strikt innerhalb von basedir bzw. publish_root."""

    paths = config_dict['paths']
    basedir = Path(paths['basedir'])
    for key, value in paths.items():
        if key in {'basedir', 'publish_root'}:
            continue
        result = validate_path(str(value), str(basedir))
        if not result.allowed:
            raise ValueError(f'CONFIGINVALID path outside basedir:{key}:{result.reason}')


def _validate_culling(culling: Mapping[str, Any]) -> None:
    """Prueft 01AP-relevante Culling-Schwellen, Gewichte und Sternbaender."""

    if not 0 <= culling['reject_threshold'] < culling['keep_threshold'] <= 1:
        raise ValueError('CONFIGINVALID score thresholds')
    weights = culling['final_component_weights']
    _reject_unknown(weights, {'base_score', 'eye_score', 'personal_score', 'family_score'}, 'final_component_weights')
    if any(value < 0 for value in weights.values()) or abs(sum(weights.values()) - 1) > 1e-9:
        raise ValueError('CONFIGINVALID final_component_weights')
    bands = culling['star_rating_bands']
    if len(bands) != 6:
        raise ValueError('CONFIGINVALID star_rating_bands')
    previous_max = -1.0
    for band in bands:
        _require(band, {'min', 'max', 'rating'}, 'star_rating_band')
        if band['min'] > band['max'] or band['min'] < 0 or band['max'] > 1:
            raise ValueError('CONFIGINVALID star_rating_bands')
        if band['min'] < previous_max:
            raise ValueError('CONFIGINVALID star_rating_bands')
        previous_max = band['max']


def _validate_automation(config_dict: dict[str, Any]) -> None:
    """Erhaelt die bisherigen expliziten Automatikgates fuer Bestandskompatibilitaet."""

    if 'automation' not in config_dict or 'phase2' not in config_dict:
        return
    automation = config_dict['automation']
    phase2 = config_dict['phase2']
    workflow = config_dict['workflow']
    _require(
        automation,
        {
            'mode',
            'automatic_phase2_enabled',
            'automatic_candidates_enabled',
            'automatic_reference_activation',
            'automatic_sample_activation',
            'rollback_on_error',
        },
        'automation',
    )
    if automation['mode'] not in _ALLOWED_AUTOMATION_MODES:
        raise ValueError('CONFIGINVALID automation.mode')
    if automation['mode'] == 'reference_activation' or automation['automatic_reference_activation'] or automation['automatic_sample_activation']:
        raise ValueError('CONFIGINVALID automatic reference/sample activation prohibited')
    if automation['mode'] == 'automatic_phase2' and not (
        automation['automatic_phase2_enabled']
        and workflow['phase_execution'] == 'phase1_then_phase2'
        and phase2['allow_automatic_handoff']
    ):
        raise ValueError('CONFIGINVALID automatic_phase2 gates')
    if automation['mode'] == 'automatic_candidates' and not automation['automatic_candidates_enabled']:
        raise ValueError('CONFIGINVALID automatic_candidates gate')


def _validate_face(face: Mapping[str, Any]) -> None:
    """Prueft Backend- und Profilkombinationen fuer die lokale Face-Konfiguration."""

    if not face:
        raise ValueError('CONFIGINVALID face')
    if face['backend'] not in _ALLOWED_FACE_BACKENDS:
        raise ValueError('CONFIGINVALID face backend/profile')
    if face['execution_profile'] not in {'cpu', 'cuda'}:
        raise ValueError('CONFIGINVALID face backend/profile')
    if face['execution_profile'] == 'cuda' and face['backend'] != 'onnx_face_cuda':
        raise ValueError('CONFIGINVALID cuda profile/backend')


def _find_hash(mapping: Mapping[str, Any], *candidates: str) -> str | None:
    """Liest einen der erlaubten Hash-Schluessel, ohne Feldnamen zu erraten."""

    for key in candidates:
        value = mapping.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _validate_model_file(label: str, path_value: str, expected_hash: str | None, models_root: Path, base_dir: Path) -> None:
    """Prueft lokalen Modellpfad unter WORKFLOW_DATA/models und optionalen SHA256."""

    resolved = _resolve_local_path(path_value, base_dir)
    result: SafetyResult = validate_path(str(resolved), str(models_root))
    if not result.allowed:
        raise ValueError(f'CONFIGINVALID model path outside models root:{label}')
    if not resolved.is_file():
        raise ValueError(f'CONFIGINVALID model file missing:{label}')
    if expected_hash is None:
        raise ValueError(f'CONFIGINVALID model hash missing:{label}')
    if sha256(resolved) != expected_hash:
        raise ValueError(f'CONFIGINVALID model hash mismatch:{label}')


def _validate_models(config_dict: dict[str, Any]) -> None:
    """Prueft aktivierte lokale Modellartefakte fuer CLIP und Face-Inferenz."""

    paths = config_dict['paths']
    base_dir = Path(paths['basedir'])
    models_root = Path(paths['workflow_data']) / 'models'
    if not is_within_base(models_root, Path(paths['workflow_data'])):
        raise ValueError('CONFIGINVALID workflow_data models root invalid')

    taste = config_dict['culling'].get('taste_model', {})
    if taste.get('enabled'):
        _validate_model_file(
            'culling.taste_model.model_path',
            taste['model_path'],
            _find_hash(taste, 'model_sha256', 'sha256'),
            models_root,
            base_dir,
        )

    face = config_dict['face']
    if face.get('enabled'):
        backend_options = face.get('backends', {}).get(face['backend'], {})
        for key, hash_keys in {
            'detector_model': ('detector_model_sha256', 'detector_sha256', 'sha256_detector'),
            'recognizer_model': ('recognizer_model_sha256', 'recognizer_sha256', 'sha256_recognizer'),
        }.items():
            if key not in backend_options:
                raise ValueError(f'CONFIGINVALID face backend model missing:{key}')
            _validate_model_file(
                f'face.backends.{face["backend"]}.{key}',
                backend_options[key],
                _find_hash(backend_options, *hash_keys),
                models_root,
                base_dir,
            )


def _validate_finalization(config_dict: dict[str, Any]) -> None:
    """Validiert publish_root und target_folder nur bei aktivierter PHASE3 separat."""

    finalization = config_dict['finalization']
    publish = finalization.get('publish_to_synology_photos', {})
    if not finalization.get('enabled') and not publish.get('enabled'):
        return
    paths = config_dict['paths']
    publish_root = paths.get('publish_root')
    if not publish_root:
        raise ValueError('CONFIGINVALID publish_root missing')
    publish_root_path = Path(publish_root)
    root_check = validate_path(str(publish_root_path), str(publish_root_path))
    if not root_check.allowed:
        raise ValueError(f'CONFIGINVALID publish_root invalid:{root_check.reason}')
    target_folder = publish.get('target_folder')
    if not target_folder:
        raise ValueError('CONFIGINVALID finalization target_folder missing')
    target_path = _resolve_local_path(str(target_folder), publish_root_path)
    target_check = validate_path(str(target_path), str(publish_root_path))
    if not target_check.allowed:
        raise ValueError(f'CONFIGINVALID target_folder invalid:{target_check.reason}')
    publish['target_folder'] = str(target_path)


def validate_schema(config_dict: dict[str, Any]) -> None:
    """Validiert config.yaml strikt gemaess 01AP und bestehenden Sicherheitsgates."""

    if not isinstance(config_dict, dict):
        raise ValueError('CONFIGINVALID config must be a mapping')  # noqa: TRY004
    _reject_unknown(config_dict, _ALLOWED_TOP_LEVEL, 'top-level')
    _require(config_dict, _REQUIRED_TOP_LEVEL, 'sections')
    if 'face' not in config_dict and 'family_recognition' not in config_dict:
        raise ValueError('CONFIGINVALID missing sections:["face"]')
    if (
        'face' in config_dict
        and 'family_recognition' in config_dict
        and config_dict['face'] != config_dict['family_recognition']
    ):
        raise ValueError('CONFIGINVALID face and family_recognition conflict')

    _require(config_dict['paths'], _REQUIRED_PATH_KEYS, 'paths')
    _require(
        config_dict['workflow'],
        {
            'phase_execution',
            'batch_limit',
            'batch_sort',
            'skip_incomplete_batches',
            'max_run_hours',
            'resume_incomplete_batches',
            'dry_run',
        },
        'workflow',
    )
    workflow = config_dict['workflow']
    if workflow['phase_execution'] not in _ALLOWED_WORKFLOW_PHASES:
        raise ValueError('CONFIGINVALID workflow')
    if workflow['batch_sort'] != 'oldest_first':
        raise ValueError('CONFIGINVALID workflow')
    if not isinstance(workflow['batch_limit'], int) or workflow['batch_limit'] < 1:
        raise ValueError('CONFIGINVALID workflow')

    _ensure_secret_free(config_dict)
    _validate_paths(config_dict)
    _validate_culling(config_dict['culling'])
    _validate_automation(config_dict)
    _validate_face(config_dict['face'])
    _validate_models(config_dict)
    _validate_finalization(config_dict)


def get_fingerprint(config_dict: dict[str, Any]) -> str:
    """Erzeugt den deterministischen SHA256-Fingerprint der effektiven Konfiguration."""

    payload = json.dumps(config_dict, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _build_config(config_dict: dict[str, Any], fingerprint: str) -> Config:
    """Materialisiert den 01AP-Dataclass-Vertrag mit Legacy-Kompatibilitaet."""

    legacy = {}
    for key in ('phase2', 'metadata', 'family_recognition', 'automation', 'calibration', 'extensions'):
        if key in config_dict:
            legacy[key] = _SectionConfig(copy.deepcopy(config_dict[key])) if isinstance(config_dict[key], dict) else copy.deepcopy(config_dict[key])
    return Config(
        paths=PathsConfig(copy.deepcopy(config_dict['paths'])),
        workflow=WorkflowConfig(copy.deepcopy(config_dict['workflow'])),
        culling=CullingConfig(copy.deepcopy(config_dict['culling'])),
        face=FaceConfig(copy.deepcopy(config_dict['face'])),
        finalization=FinalizationConfig(copy.deepcopy(config_dict['finalization'])),
        reference_pools=ReferencePoolsConfig(copy.deepcopy(config_dict['reference_pools'])),
        fingerprint=fingerprint,
        _legacy_sections=legacy,
    )


def load_config(path: str | Path) -> Config:
    """Laedt und validiert die zentrale config.yaml mit 01AP-Dataclass-Ausgabe."""

    raw = yaml.safe_load(Path(path).read_text(encoding='utf-8')) or {}
    if not isinstance(raw, dict):
        raise ValueError('CONFIGINVALID config must be a mapping')  # noqa: TRY004
    config_dict = copy.deepcopy(raw)
    _migrate_aliases(config_dict)
    _normalize_paths(config_dict)
    validate_schema(config_dict)
    fingerprint = get_fingerprint(config_dict)
    return _build_config(config_dict, fingerprint)


def validate_config(config: dict[str, Any]) -> None:
    """Kompatibilitaetsalias fuer bestehenden Code und Tests."""

    validate_schema(config)


def validate_paths(config: dict[str, Any]) -> None:
    """Kompatibilitaetsalias fuer bestehende Pfadvalidierungsaufrufe."""

    _validate_paths(config)


def fingerprint(config: Config | dict[str, Any]) -> str:
    """Kompatibilitaetsalias fuer bestehenden Code und CLI-Ausgaben."""

    if isinstance(config, Config):
        return config.fingerprint
    return get_fingerprint(config)


def public_config(config: Config | dict[str, Any]) -> dict[str, Any]:
    """Gibt eine serialisierbare, secrets-freie Diagnosekonfiguration zurueck."""

    return config.to_dict() if isinstance(config, Config) else copy.deepcopy(config)
