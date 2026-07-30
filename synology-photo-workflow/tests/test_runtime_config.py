"""Projekt: Synology Photo Workflow
Datei: tests/test_runtime_config_v77.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Prüft Alias-Konflikte, vollständige Automatikgates und den Lock-Eigentümerschutz.
SICHERHEIT: Konfigurations- und Lockfehler stoppen vor jeder produktiven Mutation.
"""
import pytest
from app.configuration import load_config
from app.locks import RunLock
from .conftest import write_config


def test_automatic_phase2_requires_all_explicit_gates(tmp_path):
    with pytest.raises(ValueError, match='automatic_phase2 gates'):
        load_config(write_config(tmp_path, automation={'mode': 'automatic_phase2', 'automatic_phase2_enabled': True}))


def test_legacy_alias_conflict_is_rejected(tmp_path):
    with pytest.raises(ValueError, match='conflicts'):
        load_config(write_config(tmp_path, culling={'decision_mode': 'automaticphase2'}))


def test_lock_can_only_be_removed_by_its_owner(tmp_path):
    lock = RunLock(tmp_path/'workflow.lock')
    with lock:
        with pytest.raises(RuntimeError, match='manual_verification'):
            with RunLock(tmp_path/'workflow.lock'):
                pass
    assert not (tmp_path/'workflow.lock').exists()
