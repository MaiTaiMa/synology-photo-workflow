"""Runtime: Batch-Verarbeitung, Quarantaene, Manifeste."""

from .result_contract import atomic_json_write, FileManifest
from . import VERSION
from .safety import SafetyError
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
import shutil
import os


def write_batch_lock(workflow_data: Path, batch_id: str) -> dict[str, Any]:
    """Schreibe Batch-Lock atomar."""
    data = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "batch_id": batch_id,
    }
    lock_path = workflow_data / "runtime" / "batch_locks" / f"{batch_id}.json"
    atomic_json_write(str(lock_path), data)
    return data


def quarantine_batch(batch_path: Path, basedir: str, temp_error: str, reason: str) -> dict[str, Any]:
    """Verschiebe fehlerhaften Batch in Quarantaene und schreibe Manifest."""
    quarantine_dir = Path(basedir) / temp_error
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    quarantine_path = quarantine_dir / batch_path.name
    
    if batch_path.exists():
        shutil.move(str(batch_path), str(quarantine_path))
    
    manifest = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "batch_path": str(batch_path),
        "quarantine_path": str(quarantine_path),
        "reason": reason,
    }
    manifest_path = quarantine_path.with_suffix(".quarantine.json")
    atomic_json_write(str(manifest_path), manifest)
    return manifest


def process_physical_batch(batch_path: Path, config: dict[str, Any]) -> FileManifest:
    """Verarbeite physischen Batch - Placeholder."""
    # TODO: Vollstaendige Implementierung in phases.py
    return FileManifest(
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        files=[],
    )
