"""
Skript: app/locks.py
Zweck: Globaler Run-Lock (RunLock) als exklusiver Schutz vor parallelen
       produktiven Läufen. Nutzt Dateisystem-Lock-Semantik.
Autor: MaiTai
Erstellt: 2026-07-30
Version: 7.9.0
Requires: json, pathlib, datetime

Änderungsprotokoll:
  2026-08-08 | 7.9.0 | 00AP: RunLock-Klasse ergänzt, atomic_json_write-Nutzung.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import VERSION
from .result_contract import atomic_json_write


class RunLock:
    """Globaler Lauf-Lock, der parallele produktive Läufe verhindert.

    Erstellt beim Eintritt eine Lock-Datei und löscht sie beim Verlassen.
    Wirft RuntimeError('manual_verification:…') wenn die Lock-Datei bereits
    existiert, weil ein manueller Eingriff nötig sein könnte. Dies folgt
    dem Sicherheitsprinzip: kein automatisches Überschreiben von Locks.
    """

    def __init__(self, lock_file: str | Path) -> None:
        """Legt den Lock-Pfad fest; noch kein Dateisystem-Zugriff."""
        self._lock_file = Path(lock_file)

    def __enter__(self) -> RunLock:
        """Setzt den globalen Lock oder wirft RuntimeError bei Kollision."""
        self._lock_file.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now(UTC).isoformat()
        data: dict[str, Any] = {
            "schema_version": 1,
            "producer_version": VERSION,
            "created_at": now,
            "updated_at": now,
            "lock_holder": "run",
        }
        # Atomare Erstellung via O_EXCL – verhindert TOCTOU-Race bei parallelen Läufen
        try:
            with self._lock_file.open("x", encoding="utf-8") as fh:
                fh.write(json.dumps(data, indent=2))
        except FileExistsError:
            raise RuntimeError(
                f"manual_verification:lock_file_exists:{self._lock_file}"
            ) from None
        return self

    def __exit__(self, *_: object) -> None:
        """Entfernt den Lock beim Verlassen des Kontexts."""
        self._lock_file.unlink(missing_ok=True)


def write_run_lock(workflow_data: Path, run_id: str) -> dict[str, Any]:
    """Schreibt Run-Lock-Record atomar (Legacy-Hilfsfunktion)."""
    data: dict[str, Any] = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "run_id": run_id,
    }
    lock_path = workflow_data / "runtime" / "run_lock.json"
    atomic_json_write(str(lock_path), data)
    return data
