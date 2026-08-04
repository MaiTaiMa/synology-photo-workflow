"""app/locks.py — RunLock, BatchLock fuer exklusive Zugriffskontrolle.

Spezifikation v10.2 - AP3
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any

from .safety import utcnow, atomic_json, SafetyError


class RunLock:
    """Exklusiver Lock fuer Workflow-Run (verhindert parallele Laeufe)."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    def __enter__(self) -> "RunLock":
        if self._path.exists():
            raise RuntimeError("run_lock_active")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(self._path, {
            "schema_version": 1,
            "created_at": utcnow(),
            "updated_at": utcnow(),
            "producer_version": "7.8.0",
            "locked_at": utcnow(),
            "owner": os.getenv("USER", "unknown"),
        }, "locked_at")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._path.exists():
            self._path.unlink()


class BatchLock:
    """Exklusiver Lock fuer Batch-Verarbeitung."""

    def __init__(self, basedir: Path | str, batch_id: str) -> None:
        self._path = Path(basedir) / f"{batch_id}.lock"

    def __enter__(self) -> "BatchLock":
        if self._path.exists():
            raise SafetyError("batch_lock_active")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(self._path, {
            "schema_version": 1,
            "created_at": utcnow(),
            "updated_at": utcnow(),
            "producer_version": "7.8.0",
            "batch_id": self._path.stem.replace(".lock", ""),
            "locked_at": utcnow(),
        }, "batch_id")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._path.exists():
            self._path.unlink()
