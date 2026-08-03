"""Face-Cache: Manifest."""

from .result_contract import atomic_json_write
from . import VERSION
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


def write_cache_manifest(workflow_data: Path, faces: list[dict[str, Any]]) -> dict[str, Any]:
    """Schreibe Face-Cache-Manifest atomar."""
    data = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "faces": faces,
    }
    manifest_path = workflow_data / "runtime" / "face_cache" / "manifest.json"
    atomic_json_write(str(manifest_path), data)
    return data
