"""Projekt: Synology Photo Workflow
Datei: app/batch_state.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Schema-validierter, vorwärtsgerichteter Batch-Zustandsautomat mit Fortschritts-, Pause- und Recovery-Informationen.
SICHERHEIT: Recovery verschiebt oder löscht keine Originale ohne expliziten, geprüften Transaktionszustand.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from .safety import atomic_json, read_control_json, utcnow

MANUAL_ORDER = ['phase1_completed', 'review_comparison_pending', 'review_record_committed', 'calibration_index_committed', 'phase2_archiving', 'phase2_completed']
AUTOMATIC_ORDER = ['phase1_completed', 'automatic_handoff', 'phase2_archiving', 'phase2_completed']
VALID_STATUS = {'pending', 'running', 'paused', 'completed', 'failed', 'recovery_required'}


def state_path(runtime: str | Path, batch_id: str) -> Path:
    """Liefert den einzigen zentralen State-Pfad für eine unveränderliche batch_id."""
    return Path(runtime) / 'state' / f'{batch_id}.json'


def _order_for(phase: str, old_phase: str | None) -> list[str]:
    return AUTOMATIC_ORDER if phase == 'automatic_handoff' or old_phase == 'automatic_handoff' else MANUAL_ORDER


def write_state(path: str | Path, batch_id: str, phase: str, status: str = 'running', **extra: Any) -> dict[str, Any]:
    """Schreibt vorwärts gerichtete Zustände inklusive Fortschritt, Fehler und Pausengrund atomar."""
    if status not in VALID_STATUS:
        raise ValueError(f'invalid_batch_status:{status}')
    destination, old = Path(path), {}
    if destination.exists():
        old = read_control_json(destination, 'batch_id')
        if old['batch_id'] != batch_id:
            raise ValueError('batch_id_changed')
        order = _order_for(phase, old.get('phase'))
        if phase not in order or (old.get('phase') in order and order.index(phase) < order.index(old['phase'])):
            raise ValueError('state_transition_backwards')
    now = utcnow()
    data = {**old, 'schema_version': 1, 'batch_id': batch_id, 'source_folder_name': old.get('source_folder_name', batch_id.rsplit('_', 1)[0]), 'current_relative_path': old.get('current_relative_path'), 'source_fingerprint': old.get('source_fingerprint'), 'phase': phase, 'status': status, 'created_at': old.get('created_at', now), 'updated_at': now, 'producer_version': '7.7.0', 'config_fingerprint': old.get('config_fingerprint'), 'completed_steps': old.get('completed_steps', []), 'current_step': extra.pop('current_step', phase), 'progress': old.get('progress', {}), 'counters': old.get('counters', {}), 'errors': old.get('errors', []), 'pause_reason': extra.pop('pause_reason', None if status != 'paused' else 'unspecified'), 'recovery_reason': extra.pop('recovery_reason', None), **extra}
    atomic_json(destination, data, 'batch_id')
    return data
