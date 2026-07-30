"""Projekt: Synology Photo Workflow
Datei: app/planning.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Strikt nicht-mutierender Planer für Phase 1 und Phase 2 mit verständlichen Blockern.
SICHERHEIT: Planung ist strikt lesend; produktive Batch-Schritte sind gelockt und zeitbudgetiert.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from .inventory import IMG, RAW, assert_safe_batch, batch_id, files
from .safety import SafetyError, read_control_json


def plan_phase1(config: dict[str, Any], folder: str | Path | None = None) -> list[dict[str, Any]]:
    """Inventarisiert potenzielle Phase-1-Batches ohne Ordner, Dateien, States oder Metadaten zu verändern."""
    source = Path(folder) if folder else Path(config['paths']['temp_sd'])
    batches = [source] if folder else (sorted(path for path in source.iterdir() if path.is_dir() and not path.is_symlink()) if source.is_dir() else [])
    plan = []
    for batch in batches[:config['workflow']['batch_limit']]:
        try:
            safe = assert_safe_batch(batch)
            plan.append({'batch': safe.name, 'batch_id': batch_id(safe), 'status': 'ready', 'jpg_count': len(files(safe, IMG)), 'arw_count': len(files(safe, RAW)), 'would_create': ['ARW/', 'SAVE/', 'Review/', 'Rejected/', 'SAVE/culling_scores.csv', 'SAVE/phase1_manifest.json'], 'would_handoff_to': str(Path(config['paths']['temp_images']) / safe.name)})
        except SafetyError as error:
            plan.append({'batch': batch.name, 'status': 'blocked', 'reason': str(error)})
    return plan


def plan_phase2(config: dict[str, Any], folder: str | Path | None = None) -> list[dict[str, Any]]:
    """Prüft Manifest- und sichtbaren Entscheidungszustand ohne Archive zu erstellen oder ARWs anzufassen."""
    source = Path(folder) if folder else Path(config['paths']['temp_done'])
    batches = [source] if folder else (sorted(path for path in source.iterdir() if path.is_dir() and not path.is_symlink()) if source.is_dir() else [])
    plan = []
    for batch in batches[:config['workflow']['batch_limit']]:
        try:
            manifest = read_control_json(batch / 'SAVE' / 'phase1_manifest.json', 'batch_id')
            decisions = {'keep': 0, 'review': 0, 'reject': 0}
            blockers = []
            for image in manifest['images']:
                hits = [name for name in ('', 'Review', 'Rejected') if (batch / name / image['relative_path']).exists()]
                if len(hits) != 1:
                    blockers.append(f'review_state_invalid:{image["relative_path"]}')
                elif hits[0] == '': decisions['keep'] += 1
                else: decisions[hits[0].lower()] += 1
            plan.append({'batch': batch.name, 'batch_id': manifest['batch_id'], 'status': 'blocked' if blockers else 'ready', 'blockers': blockers, 'final_decision_counts': decisions, 'would_create': ['review_decision_record.json', 'SAVE/archive_manifest.json'], 'would_delete_arws': bool(config['phase2']['delete_unneeded_arws_after_verified_archive']) and not blockers})
        except (SafetyError, OSError) as error:
            plan.append({'batch': batch.name, 'status': 'blocked', 'reason': str(error)})
    return plan
