"""Projekt: Synology Photo Workflow
Datei: app/runtime.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Laufzeitgrenzen für Zeitbudget, Batch-Locks, sichere Quarantäne und dokumentierte Recovery-Inspektion.
SICHERHEIT: Recovery verschiebt oder löscht keine Originale ohne expliziten, geprüften Transaktionszustand.
"""
from __future__ import annotations

import os
import shutil
import socket
import time
import uuid
from pathlib import Path
from typing import Any
from .safety import SafetyError, atomic_json, canonical_hash, read_control_json, require_within, utcnow


class RunBudget:
    """Prüft ausschließlich zwischen diskreten Schritten das konfigurierbare Zeitbudget."""

    def __init__(self, hours: float):
        self.deadline = time.monotonic() + float(hours) * 3600

    def checkpoint(self, step: str) -> None:
        """Stoppt vor einem neuen teuren oder mutierenden Schritt und ermöglicht sauberes Pausieren."""
        if time.monotonic() >= self.deadline:
            raise SafetyError(f'run_budget_exhausted_before:{step}')


class BatchLock:
    """Exklusiver Batch-Lock; nebenläufige Prozesse dürfen denselben Batch nicht bearbeiten."""

    def __init__(self, runtime: str | Path, batch_id: str):
        self.path = Path(runtime) / 'batch_locks' / f'{batch_id}.lock.json'
        self.batch_id = batch_id
        self.lock_id = str(uuid.uuid4())

    def __enter__(self) -> 'BatchLock':
        if self.path.exists():
            prior = read_control_json(self.path, 'batch_id')
            raise SafetyError(f'batch_lock_active:{prior["batch_id"]}:{prior.get("host")}:{prior.get("pid")}')
        now = utcnow()
        atomic_json(self.path, {'schema_version': 1, 'batch_id': self.batch_id, 'lock_id': self.lock_id, 'created_at': now, 'updated_at': now, 'producer_version': '7.7.0', 'host': socket.gethostname(), 'pid': os.getpid()}, 'batch_id')
        return self

    def __exit__(self, *_: object) -> None:
        if self.path.exists() and read_control_json(self.path, 'batch_id').get('lock_id') == self.lock_id:
            self.path.unlink()


def quarantine_batch(batch: str | Path, basedir: str | Path, temp_error: str | Path, reason: str, evidence: dict[str, Any] | None = None) -> Path:
    """Verschiebt nur einen geprüften Batch innerhalb basedir nach TEMPERROR und schreibt ein Audit-Manifest."""
    source = require_within(basedir, batch)
    destination_root = require_within(basedir, temp_error)
    if not source.is_dir() or source == destination_root or destination_root in source.parents:
        raise SafetyError('quarantine_invalid_source')
    destination_root.mkdir(parents=True, exist_ok=True)
    suffix = canonical_hash({'source': str(source), 'reason': reason, 'at': utcnow()})[:8]
    destination = destination_root / f'{source.name}__{suffix}'
    if destination.exists():
        raise SafetyError('quarantine_destination_exists')
    shutil.move(str(source), str(destination))
    now = utcnow()
    manifest = {'schema_version': 1, 'batch_id': destination.name, 'created_at': now, 'updated_at': now, 'producer_version': '7.7.0', 'original_relative_path': source.relative_to(Path(basedir).resolve()).as_posix(), 'reason': reason, 'evidence': evidence or {}, 'recovery_required': True}
    atomic_json(destination / 'SAVE' / 'quarantine_manifest.json', manifest, 'batch_id')
    return destination


def inspect_recovery(runtime: str | Path, batch_id: str) -> dict[str, Any]:
    """Liest nur State, Review-Record und Archivmanifest; es führt keine Recovery-Mutation aus."""
    base = Path(runtime)
    state = read_control_json(base / 'state' / f'{batch_id}.json', 'batch_id')
    result: dict[str, Any] = {'batch_id': batch_id, 'state': state, 'required_actions': []}
    if state['phase'] == 'phase2_archiving':
        result['required_actions'].append('Archivmanifest und ZIP-Integrität vor Fortsetzung prüfen.')
    if state['status'] in {'paused', 'failed', 'recovery_required'}:
        result['required_actions'].append('Fehlergrund und sichtbaren Batchzustand manuell prüfen.')
    review = base / 'calibration' / 'batches' / batch_id / 'review_decision_record.json'
    result['review_record_present'] = review.exists()
    result['safe_to_auto_resume'] = False
    return result
