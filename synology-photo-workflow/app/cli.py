"""Projekt: Synology Photo Workflow
Datei: app/cli.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Kanonische CLI mit klaren Exit-Codes, Signal-zu-Pause-Vertrag, Diagnose und read-only Recovery.
SICHERHEIT: Signale pausieren nur vor neuen Schritten; Recovery bleibt explizit und lesend.
"""
from __future__ import annotations

import argparse
import json
import signal
import sys
from pathlib import Path
from .calibration import rebuild
from .configuration import fingerprint, load_config, public_config
from .face_backend import diagnose
from .locks import RunLock
from .phases import phase1, phase2
from .reporting import action, summary
from .runtime import inspect_recovery
from .planning import plan_phase1, plan_phase2

EXIT = {'success': 0, 'validation': 2, 'recoverable': 3, 'recovery_required': 4, 'configuration': 5, 'internal': 6}


class StopRequested(RuntimeError):
    """Interner Marker: SIGTERM/SIGINT wird erst am nächsten definierten Checkpoint verarbeitet."""


def parser() -> argparse.ArgumentParser:
    """Definiert ausschließlich den kanonischen Python-Moduleinstieg und stabile Befehlsnamen."""
    command_parser = argparse.ArgumentParser()
    command_parser.add_argument('--config', required=True)
    subcommands = command_parser.add_subparsers(dest='command', required=True)
    for name in ('run', 'phase1', 'phase2'):
        child = subcommands.add_parser(name)
        child.add_argument('--folder')
        child.add_argument('--dry_run', action='store_true')
    for name in ('rebuild_family_cache', 'rebuild_personal_model', 'diagnose_face_backend', 'validate_config', 'print_effective_config', 'rebuild_calibration_index'):
        subcommands.add_parser(name)
    child = subcommands.add_parser('recover_batch')
    child.add_argument('batch_id')
    child = subcommands.add_parser('reopen_review')
    child.add_argument('batch_id')
    return command_parser


def _signal_guard() -> tuple[dict[str, bool], dict[int, object]]:
    """Registriert minimale Handler; sie setzen nur ein Flag und führen keinerlei Dateisystemaktion aus."""
    requested = {'value': False}
    previous = {}
    def handler(_signum: int, _frame: object) -> None:
        requested['value'] = True
    for signum in (signal.SIGTERM, signal.SIGINT):
        previous[signum] = signal.signal(signum, handler)
    return requested, previous


def _restore_signals(previous: dict[int, object]) -> None:
    """Stellt die Handler nach dem CLI-Lauf wieder her, wichtig für eingebettete Tests."""
    for signum, handler in previous.items():
        signal.signal(signum, handler)


def main(argv: list[str] | None = None) -> int:
    """Führt Diagnosebefehle ohne Lock aus und schützt produktive Befehle mit globalem Lock."""
    arguments = parser().parse_args(argv)
    try:
        config = load_config(arguments.config)
    except Exception as error:
        print(str(error), file=sys.stderr)
        return EXIT['configuration']
    try:
        if arguments.command == 'validate_config':
            print(json.dumps({'valid': True, 'config_fingerprint': fingerprint(config)}))
            return EXIT['success']
        if arguments.command == 'print_effective_config':
            print(json.dumps(public_config(config), indent=2))
            return EXIT['success']
        if arguments.command == 'diagnose_face_backend':
            face = config['family_recognition']
            diagnosis = diagnose(face['backend'], face['execution_profile'], face.get('backends', {}).get(face['backend'], {}))
            print(json.dumps(diagnosis.__dict__, default=lambda value: value.__dict__))
            return EXIT['success'] if diagnosis.ready else EXIT['configuration']
        runtime = Path(config['paths']['workflow_data']) / 'runtime'
        if arguments.command == 'rebuild_calibration_index':
            print(json.dumps(rebuild(runtime / 'calibration' / 'batches', runtime / 'calibration' / 'calibration_summary.json', config)))
            return EXIT['success']
        if arguments.command == 'recover_batch':
            print(json.dumps(inspect_recovery(runtime, arguments.batch_id), indent=2))
            return EXIT['recoverable']
        if arguments.command in {'rebuild_family_cache', 'rebuild_personal_model', 'reopen_review'}:
            print(json.dumps({'status': 'not_implemented_safely', 'command': arguments.command}))
            return EXIT['recoverable']
        if arguments.dry_run:
            if arguments.command == 'phase1':
                print(json.dumps({'status': 'dry_run', 'phase1_plan': plan_phase1(config, arguments.folder)}, indent=2))
            elif arguments.command == 'phase2':
                print(json.dumps({'status': 'dry_run', 'phase2_plan': plan_phase2(config, arguments.folder)}, indent=2))
            else:
                print(json.dumps({'status': 'dry_run', 'phase1_plan': plan_phase1(config), 'phase2_plan': plan_phase2(config)}, indent=2))
            return EXIT['success']
        requested, previous = _signal_guard()
        try:
            with RunLock(runtime / 'workflow.lock'):
                if requested['value']:
                    raise StopRequested('signal_before_run')
                if arguments.command == 'phase1':
                    result = phase1(config, arguments.folder)
                elif arguments.command == 'phase2':
                    result = phase2(config, arguments.folder)
                else:
                    result = {'phase1': phase1(config) if config['workflow']['phase_execution'] != 'phase2_only' else [], 'phase2': phase2(config) if config['workflow']['phase_execution'] == 'phase1_then_phase2' else []}
                if requested['value']:
                    raise StopRequested('signal_after_safe_step')
        finally:
            _restore_signals(previous)
        print(json.dumps(summary(runtime, 'success', fingerprint(config), result, requested_mode=config['automation']['mode'], effective_mode='assisted_review')))
        return EXIT['success']
    except StopRequested as error:
        print(str(error), file=sys.stderr)
        return EXIT['recoverable']
    except Exception as error:
        text = str(error)
        code = EXIT['recovery_required'] if 'recovery_required' in text else EXIT['recoverable'] if any(token in text for token in ('review_state_invalid', 'lock_active', 'batch_lock_active', 'run_budget')) else EXIT['internal']
        print(text, file=sys.stderr)
        return code
