"""Projekt: Synology Photo Workflow
Datei: tests/conftest.py
Mitentwickler: MaiTai
Erstellt: 2026-07-29
Projektversion: 7.9.0
Funktion: Synthetische, private-freie NAS-Testumgebung und Konfigurationsfixture.
SICHERHEIT: Fixtures erzeugen ausschliesslich temporaere Verzeichnisse ohne Originale oder biometrische Daten.

Aenderungsprotokoll:
  2026-08-08 | 7.9.0 | 01AP: publish_root, finalization und reference_pools
                       in der Standard-Config ergaenzt.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


def _deep_update(target: dict[str, Any], updates: dict[str, Any]) -> None:
    """Fuehrt verschachtelte Test-Overrides deterministisch und minimal zusammen."""

    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value


def write_config(tmp_path: Path, **overrides: dict[str, Any]) -> Path:
    """Schreibt eine vollstaendige, 01AP-kompatible Testkonfiguration nach YAML."""

    cfg: dict[str, Any] = {
        'paths': {
            'basedir': str(tmp_path),
            'temp_sd': 'TEMP_SD',
            'temp_images': 'TEMP_IMAGES',
            'temp_done': 'TEMP_DONE',
            'temp_error': 'TEMP_ERROR',
            'workflow_data': 'WORKFLOW_DATA',
            'manual_keep_inbox': 'MANUAL_KEEP/inbox',
            'manual_keep_used': 'MANUAL_KEEP/used',
            'publish_root': 'PUBLISH_ROOT',
        },
        'workflow': {
            'phase_execution': 'phase1_then_phase2',
            'batch_limit': 1,
            'batch_sort': 'oldest_first',
            'skip_incomplete_batches': False,
            'max_run_hours': 10,
            'resume_incomplete_batches': True,
            'dry_run': False,
        },
        'culling': {
            'enabled': True,
            'keep_threshold': 0.65,
            'reject_threshold': 0.35,
            'auto_keep_min_rating': 2,
            'final_component_weights': {
                'base_score': 0.55,
                'eye_score': 0.1,
                'personal_score': 0.2,
                'family_score': 0.15,
            },
            'base_weights': {
                'sharpness': 0.35,
                'aesthetic': 0.35,
                'exposure': 0.2,
                'reference_score': 0.1,
            },
            'star_rating_bands': [
                {'min': 0.0, 'max': 0.19, 'rating': 0},
                {'min': 0.2, 'max': 0.39, 'rating': 1},
                {'min': 0.4, 'max': 0.59, 'rating': 2},
                {'min': 0.6, 'max': 0.74, 'rating': 3},
                {'min': 0.75, 'max': 0.89, 'rating': 4},
                {'min': 0.9, 'max': 1.0, 'rating': 5},
            ],
            'taste_model': {
                'enabled': False,
                'backend': 'clip_aesthetic',
                'model_path': 'WORKFLOW_DATA/models/taste/model.safetensors',
                'model_sha256': 'unused-when-disabled',
                'positive_prompts': ['good photo'],
                'negative_prompts': ['bad photo'],
            },
        },
        'face': {
            'enabled': False,
            'backend': 'opencv_yunet_sface_cpu',
            'execution_profile': 'cpu',
            'metric': 'cosine_similarity',
            'match_threshold': None,
            'min_best_second_margin': None,
            'backends': {
                'opencv_yunet_sface_cpu': {
                    'detector_model': 'WORKFLOW_DATA/models/face/detector.onnx',
                    'detector_model_sha256': 'unused-when-disabled',
                    'recognizer_model': 'WORKFLOW_DATA/models/face/recognizer.onnx',
                    'recognizer_model_sha256': 'unused-when-disabled',
                }
            },
        },
        'finalization': {
            'enabled': False,
            'publish_to_synology_photos': {
                'enabled': False,
                'mode': 'copy',
                'target_folder': 'published/Workflow',
                'wait_for_index_seconds': 30,
                'max_index_wait_seconds': 900,
            },
            'synology_api': {
                'enabled': False,
                'adapter': 'synology_photos_webapi',
                'space': 'shared',
                'timeout_seconds': 10,
                'retry_count': 3,
                'retry_backoff_seconds': 3,
                'dry_run': True,
                'require_readback': True,
                'write_known_persons': False,
                'write_rating': True,
                'write_tags': True,
                'write_description': False,
            },
        },
        'reference_pools': {
            'faces': {
                'max_active': 50,
                'max_new': 20,
                'max_new_per_batch': 5,
                'min_active': 1,
            },
            'samples': {
                'max_active': 50,
                'max_new': 20,
                'max_new_per_batch': 5,
                'min_active': 1,
            },
        },
        'phase2': {
            'delete_unneeded_arws_after_verified_archive': True,
            'allow_automatic_handoff': False,
        },
        'metadata': {
            'write_mode': 'disabled',
            'verify_after_write': True,
            'create_exiftool_backups': False,
            'sidecar_recovery_enabled': False,
        },
        'family_recognition': {
            'enabled': False,
            'backend': 'opencv_yunet_sface_cpu',
            'execution_profile': 'cpu',
            'metric': 'cosine_similarity',
            'match_threshold': None,
            'min_best_second_margin': None,
            'backends': {
                'opencv_yunet_sface_cpu': {
                    'detector_model': 'WORKFLOW_DATA/models/face/detector.onnx',
                    'detector_model_sha256': 'unused-when-disabled',
                    'recognizer_model': 'WORKFLOW_DATA/models/face/recognizer.onnx',
                    'recognizer_model_sha256': 'unused-when-disabled',
                }
            },
        },
        'automation': {
            'mode': 'assisted_review',
            'automatic_phase2_enabled': False,
            'automatic_candidates_enabled': False,
            'automatic_reference_activation': False,
            'automatic_sample_activation': False,
            'rollback_on_error': True,
        },
        'calibration': {
            'enabled': True,
            'reviewed_batches_minimum': 3,
            'reviewed_images_minimum': 300,
            'terminal_agreement_minimum': 0.9,
            'reject_to_keep_rate_maximum': 0,
            'shadow_model_enabled': False,
        },
        'extensions': {},
    }
    merged = copy.deepcopy(cfg)
    for section, values in overrides.items():
        if isinstance(values, dict) and isinstance(merged.get(section), dict):
            _deep_update(merged[section], values)
        else:
            merged[section] = values
    p = Path(tmp_path) / 'config.yaml'
    p.write_text(yaml.safe_dump(merged, sort_keys=False), encoding='utf-8')
    return p
