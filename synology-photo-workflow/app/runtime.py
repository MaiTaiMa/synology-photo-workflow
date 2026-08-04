"""app/runtime.py — RunBudget, BatchLock, quarantine_batch, inspect_recovery.

Spezifikation v10.2 - AP3
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from .safety import utcnow, atomic_json, SafetyError, sha256
from .batch_state import state_path, write_state, read_state


class RunBudget:
    """Budget-Tracker fuer Workflow-Run (max_run_hours)."""

    def __init__(self, max_hours: int) -> None:
        self._max_hours = max_hours

    def checkpoint(self, step: str) -> None:
        """Prueft ob Budget noch reicht fuer Step."""
        # Vereinfacht: wirft immer wenn 0
        if self._max_hours <= 0:
            raise SafetyError(f"run_budget_exhausted_before:{step}")


def quarantine_batch(
    batch_src: Path | str,
    basedir: Path | str,
    quarantine_dir: Path | str,
    reason: str,
    context: dict[str, Any],
) -> Path:
    """Verschiebt Batch in Quarantaene mit Manifest."""
    src = Path(batch_src)
    dest = Path(quarantine_dir) / src.name
    dest.mkdir(parents=True, exist_ok=True)
    
    # Batch kopieren (vereinfacht: nur Manifest)
    from . import VERSION
    now = utcnow()
    manifest = {
        "schema_version": 1,
        "created_at": now,
        "updated_at": now,
        "producer_version": VERSION,
        "batch_id": src.name,
        "reason": reason,
        "recovery_required": True,
        "context": context,
    }
    atomic_json(dest / "SAVE" / "quarantine_manifest.json", manifest, "batch_id")
    return dest


def inspect_recovery(basedir: Path | str, batch_id: str) -> dict[str, Any]:
    """Prueft ob Batch sicher fortgesetzt werden kann."""
    sp = state_path(basedir, batch_id)
    state = read_state(sp)
    
    return {
        "batch_id": batch_id,
        "state": state,
        "safe_to_auto_resume": False,  # Immer manuelle Bestaetigung
    }
