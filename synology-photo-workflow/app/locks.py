"""Locks: Run-Lock, Batch-Lock."""

from .result_contract import atomic_json_write
from . import VERSION
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


def write_run_lock(workflow_data: Path, run_id: str) -> dict[str, Any]:
    """Schreibe Run-Lock atomar."""
    data = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
    }
    lock_path = workflow_data / "runtime" / "run_lock.json"
    atomic_json_write(str(lock_path), data)
    return data
