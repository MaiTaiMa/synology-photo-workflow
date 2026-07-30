"""Projekt: Synology Photo Workflow
Datei: app/result_contract.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Normiert Batch-Ergebnisse und reduziert Metadaten-/Archivstatus auf verständliche, vollständige Run-Summary-Felder.
SICHERHEIT: Ergebnisdaten sind vollständig, aber enthalten keine Bildbytes oder biometrischen Vektoren.
"""
from __future__ import annotations

from typing import Any


def decision_counts(images: list[dict[str, Any]], field: str = 'predicted_decision') -> dict[str, int]:
    """Zählt nur die drei kanonischen Entscheidungen und ignoriert unvollständige Felder defensiv."""
    counts = {'keep': 0, 'review': 0, 'reject': 0}
    for image in images:
        value = image.get(field)
        if value in counts:
            counts[value] += 1
    return counts


def status_summary(values: list[str]) -> dict[str, int]:
    """Aggregiert Statuswerte deterministisch, damit Reports nicht an Listenformate gebunden sind."""
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return result


def phase1_result(batch_id: str, path: str, images: list[dict[str, Any]], metadata_statuses: list[str]) -> dict[str, Any]:
    """Erzeugt den vollständigen Phase-1-Result-Vertrag für CLI und Run-Summary."""
    return {'batch_id': batch_id, 'status': 'completed', 'path': path, 'decision_counts': decision_counts(images), 'metadata_status': status_summary(metadata_statuses), 'cache_status': 'not_run', 'zip_conflicts': []}


def phase2_result(batch_id: str, images: list[dict[str, Any]], archive: dict[str, Any]) -> dict[str, Any]:
    """Erzeugt den vollständigen Phase-2-Result-Vertrag nach sichtbarer Endentscheidung und Archivierung."""
    conflicts = [archive['zip_target_collision']] if archive.get('zip_target_collision') else []
    return {'batch_id': batch_id, 'status': 'completed', 'decision_counts': decision_counts(images, 'final_decision'), 'metadata_status': 'not_run', 'cache_status': 'not_run', 'archive_path': archive.get('archive_path'), 'archive_status': 'verified' if archive.get('archive_hash') else 'no_unneeded_arws', 'zip_conflicts': conflicts}
