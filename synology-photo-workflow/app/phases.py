"""Projekt: Synology Photo Workflow
Datei: app/phases.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Orchestriert den konservativen Zwei-Phasen-Ablauf mit Inventar, Scoring, Metadaten, Review-Record und Archivschutz.
SICHERHEIT: Phase 1 mutiert erst nach Inventarprüfung; Phase 2 bleibt freigabegebunden.
"""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any
from .archives import archive_unneeded
from .batch_state import state_path, write_state
from .calibration import record
from .culling import apply_series, final_score, predicted, stars, technical_components
from .inventory import IMG, RAW, assert_safe_batch, batch_fingerprint, batch_id, files, require_complete_phase1_inventory
from .metadata import build_tags, write_metadata
from .safety import SafetyError, atomic_json, canonical_hash, read_control_json, sha256, utcnow
from .runtime import BatchLock, RunBudget
from .result_contract import phase1_result, phase2_result


def _dirs(config: dict[str, Any]) -> dict[str, str]:
    """Kapselt die konfigurierten NAS-Pfade; alle Aufrufer bleiben pfadneutral."""
    return config['paths']


def _phase1_manifest(batch_id_value: str, source_name: str, source_fingerprint: str, images: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    """Erstellt den prüfbaren Snapshot der Phase-1-Prognosen vor sichtbarer Ablage."""
    now = utcnow()
    return {'schema_version': 1, 'batch_id': batch_id_value, 'source_folder_name': source_name, 'source_fingerprint': source_fingerprint, 'created_at': now, 'updated_at': now, 'producer_version': '7.7.0', 'config_fingerprint': canonical_hash(config), 'images': images}


def _write_scores(path: Path, images: list[dict[str, Any]]) -> None:
    """Schreibt den kanonischen CSV-Namen inklusive Komponenten und Serienfeldern."""
    fields = ['image_id', 'relative_path', 'base_score', 'eye_score', 'personal_score', 'family_score', 'final_score', 'star_rating', 'predicted_decision', 'final_decision', 'decision_reason', 'series_id', 'series_size', 'series_rank', 'series_best', 'model_version', 'config_fingerprint']
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fields)
        writer.writeheader()
        for image in images:
            row = {key: image.get('components', {}).get(key, image.get(key)) for key in fields}
            writer.writerow(row)


def phase1(config: dict[str, Any], folder: str | Path | None = None) -> list[dict[str, Any]]:
    """Verarbeitet nur sichere Eingänge und übergibt sie im Standard ausschließlich nach TEMPIMAGES."""
    paths = _dirs(config)
    source = Path(folder) if folder else Path(paths['temp_sd'])
    batches = [source] if folder else sorted(item for item in source.iterdir() if item.is_dir() and not item.is_symlink())
    results = []
    budget = RunBudget(config['workflow'].get('max_run_hours', 10))
    taste_options = config['culling'].get('taste_model')
    for batch in batches[:config['workflow']['batch_limit']]:
        budget.checkpoint('phase1_batch')
        require_complete_phase1_inventory(batch)
        batch = assert_safe_batch(batch)
        source_fingerprint = batch_fingerprint(batch)
        identifier = batch_id(batch)
        runtime = Path(paths['workflow_data']) / 'runtime'
        with BatchLock(runtime, identifier):
            budget.checkpoint('phase1_mutation')
            arw, save, review, rejected = (batch / name for name in ('ARW', 'SAVE', 'Review', 'Rejected'))
            for directory in (arw, save, review, rejected):
                directory.mkdir(exist_ok=True)
            for raw in files(batch, RAW):
                shutil.move(raw, arw / raw.name)
            images = []
            for image in files(batch, IMG):
                technical = technical_components(image, config['culling']['base_weights'], taste_options=taste_options)
                components = {'base_score': technical['base_score'], 'eye_score': None, 'personal_score': None, 'family_score': None}
                score = final_score(components, config['culling']['final_component_weights'])
                decision = predicted(score, config['culling'])
                images.append({'image_id': sha256(image), 'relative_path': image.name, 'components': components, 'technical_features': technical, 'final_score': score, 'star_rating': stars(score, config['culling']['star_rating_bands']), 'predicted_decision': decision, 'final_decision': None, 'decision_reason': 'local_technical_score', 'manual_keep': False, 'model_version': 'rule-v1', 'config_fingerprint': canonical_hash(config)})
            apply_series(images)
            metadata_statuses = []
            for item in images:
                image = batch / item['relative_path']
                metadata_statuses.append(write_metadata(image, build_tags(item), config))
                target = review if item['predicted_decision'] == 'review' else rejected if item['predicted_decision'] == 'reject' else None
                if target:
                    shutil.move(image, target / image.name)
            _write_scores(save / 'culling_scores.csv', images)
            manifest = _phase1_manifest(identifier, batch.name, source_fingerprint, images, config)
            atomic_json(save / 'phase1_manifest.json', manifest, 'batch_id')
            target = Path(paths['temp_images']) / batch.name
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise SafetyError('handoff_destination_exists')
            shutil.move(batch, target)
            write_state(state_path(Path(paths['workflow_data']) / 'runtime', identifier), identifier, 'phase1_completed', current_relative_path=target.relative_to(paths['basedir']).as_posix(), source_fingerprint=source_fingerprint, metadata_status=metadata_statuses)
            results.append(phase1_result(identifier, str(target), images, metadata_statuses))
    return results


def phase2(config: dict[str, Any], folder: str | Path | None = None) -> list[dict[str, Any]]:
    """Leitet Endentscheidungen nur aus sichtbarem Reviewzustand ab und archiviert erst danach ARWs."""
    paths = _dirs(config)
    root = Path(paths['temp_done'])
    batches = [Path(folder)] if folder else sorted(item for item in root.iterdir() if item.is_dir() and not item.is_symlink())
    results = []
    budget = RunBudget(config['workflow'].get('max_run_hours', 10))
    for batch in batches[:config['workflow']['batch_limit']]:
        budget.checkpoint('phase2_batch')
        assert_safe_batch(batch)
        manifest = read_control_json(batch / 'SAVE' / 'phase1_manifest.json', 'batch_id')
        identifier = manifest['batch_id']
        runtime = Path(paths['workflow_data']) / 'runtime'
        with BatchLock(runtime, identifier):
            budget.checkpoint('phase2_mutation')
            decisions: dict[str, str] = {}
            for item in manifest['images']:
                locations = [(name, batch / name / item['relative_path']) for name in ('', 'Review', 'Rejected') if (batch / name / item['relative_path']).exists()]
                if len(locations) != 1:
                    raise SafetyError('review_state_invalid')
                location, image = locations[0]
                final = {'': 'keep', 'Review': 'review', 'Rejected': 'reject'}[location]
                item['final_decision'], item['final_path'] = final, image.relative_to(batch).as_posix()
                decisions[item['image_id']] = final
            state = state_path(Path(paths['workflow_data']) / 'runtime', identifier)
            write_state(state, identifier, 'review_comparison_pending')
            review_record = record(identifier, manifest, decisions, canonical_hash(config), 'rule-v1')
            atomic_json(Path(paths['workflow_data']) / 'runtime' / 'calibration' / 'batches' / identifier / 'review_decision_record.json', review_record, 'batch_id')
            write_state(state, identifier, 'review_record_committed')
            write_state(state, identifier, 'calibration_index_committed')
            write_state(state, identifier, 'phase2_archiving')
            archive = archive_unneeded(batch, config)
            write_state(state, identifier, 'phase2_completed', status='completed', archive=archive)
            results.append(phase2_result(identifier, manifest['images'], archive))
    return results
