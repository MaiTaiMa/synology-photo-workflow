"""Projekt: Synology Photo Workflow
Datei: tests/test_runtime_recovery_v77.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Prüft Budget-Grenze, Batch-Lock, Quarantäne-Audit und ausschließlich lesende Recovery-Inspektion.
SICHERHEIT: Recovery verschiebt oder löscht keine Originale ohne expliziten, geprüften Transaktionszustand.
"""
import pytest
from app.batch_state import state_path, write_state
from app.runtime import BatchLock, RunBudget, inspect_recovery, quarantine_batch
from app.safety import SafetyError, read_control_json


def test_budget_blocks_before_following_step():
    budget = RunBudget(0)
    with pytest.raises(SafetyError, match='run_budget_exhausted_before:archive'):
        budget.checkpoint('archive')


def test_batch_lock_is_exclusive(tmp_path):
    with BatchLock(tmp_path, 'b'):
        with pytest.raises(SafetyError, match='batch_lock_active'):
            with BatchLock(tmp_path, 'b'):
                pass


def test_quarantine_creates_auditable_manifest(tmp_path):
    batch = tmp_path/'TEMP_SD'/'camera'; batch.mkdir(parents=True); (batch/'IMG.jpg').write_bytes(b'x')
    destination = quarantine_batch(batch, tmp_path, tmp_path/'TEMP_ERROR', 'incomplete_transfer', {'age_seconds': 2})
    manifest = read_control_json(destination/'SAVE'/'quarantine_manifest.json', 'batch_id')
    assert manifest['reason'] == 'incomplete_transfer' and manifest['recovery_required']


def test_recovery_inspection_never_auto_resumes(tmp_path):
    write_state(state_path(tmp_path, 'b'), 'b', 'phase1_completed', status='paused', pause_reason='signal')
    result = inspect_recovery(tmp_path, 'b')
    assert not result['safe_to_auto_resume'] and result['state']['pause_reason'] == 'signal'
