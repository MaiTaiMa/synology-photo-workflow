"""Batch-State: phase1_moving, phase1_completed."""

from .result_contract import atomic_json_write
from . import VERSION
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


def write_state(batch_path: Path, phase: str, status: str, **extra: Any) -> dict[str, Any]:
    """Schreibe Batch-State atomar."""
    data = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "batch_path": str(batch_path),
        "phase": phase,
        "status": status,
        **extra,
    }
    state_path = batch_path.parent / f"{batch_path.name}.state.json"
    atomic_json_write(str(state_path), data)
    return data
