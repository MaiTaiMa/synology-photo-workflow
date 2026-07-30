"""Projekt: Synology Photo Workflow
Datei: tests/test_cli_recovery_v77.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Prüft recovery_batch als read-only CLI-Vertrag und den sicheren Dry-Run-Blocker.
SICHERHEIT: Signale pausieren nur vor neuen Schritten; Recovery bleibt explizit und lesend.
"""
import json
from app.batch_state import state_path, write_state
from app.cli import EXIT, main
from .conftest import write_config


def test_recover_batch_is_read_only_and_recoverable(tmp_path, capsys):
    config = write_config(tmp_path)
    runtime = tmp_path/'WORKFLOW_DATA'/'runtime'
    write_state(state_path(runtime, 'b'), 'b', 'phase1_completed', status='paused', pause_reason='test')
    assert main(['--config', str(config), 'recover_batch', 'b']) == EXIT['recoverable']
    assert json.loads(capsys.readouterr().out)['safe_to_auto_resume'] is False


def test_dry_run_uses_non_mutating_planner(tmp_path, capsys):
    config = write_config(tmp_path)
    assert main(['--config', str(config), 'phase1', '--dry_run']) == EXIT['success']
    assert '"dry_run"' in capsys.readouterr().out
