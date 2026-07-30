"""Projekt: Synology Photo Workflow
Datei: app/locks.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Globaler produktiver Lock mit Besitzerinformationen und konservativer Stale-Analyse ohne Blindlöschung.
SICHERHEIT: Konfigurations- und Lockfehler stoppen vor jeder produktiven Mutation.
"""
from __future__ import annotations

import os
import socket
import uuid
from pathlib import Path
from .safety import atomic_json, read_control_json, utcnow


class RunLock:
    """Schützt produktive Läufe; vorhandene Locks werden nie automatisch entfernt."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.run_id = str(uuid.uuid4())

    def inspect(self) -> dict:
        """Liest den Eigentümerdatensatz für eine dokumentierte manuelle Stale-Lock-Entscheidung."""
        return read_control_json(self.path, 'run_id')

    def __enter__(self) -> 'RunLock':
        if self.path.exists():
            details = self.inspect()
            raise RuntimeError(f'lock_active:manual_verification_required:host={details.get("host")}:pid={details.get("pid")}')
        now = utcnow()
        atomic_json(self.path, {'schema_version': 1, 'run_id': self.run_id, 'created_at': now, 'updated_at': now, 'producer_version': '7.7.0', 'owner': os.getuid(), 'host': socket.gethostname(), 'pid': os.getpid() }, 'run_id')
        return self

    def __exit__(self, *_: object) -> None:
        if self.path.exists() and self.inspect().get('run_id') == self.run_id:
            self.path.unlink()
