"""Sicherheit: Kontrolldateien, Manifeste, Locks."""

from .result_contract import FileManifest
from . import CONTROL_FILE_VERSION
from typing import Any
import json


class SafetyError(Exception):
    """Sicherheitsfehler bei Kontrolldateien, Manifesten, Locks."""


def validate_control_record(payload: dict[str, Any], scope_key: str | None = None) -> None:
    """Validiere Kontrolldatei-Struktur.
    
    - schema_version: muss CONTROL_FILE_VERSION entsprechen (hart)
    - producer_version: nur Typ/Nichtleere (strukturpruefung, kein exakter Wert)
    """
    if not isinstance(payload, dict):
        raise SafetyError("control_record_not_mapping")
    
    required = {"schema_version", "created_at", "updated_at", "producer_version"}
    if not required.issubset(payload):
        raise SafetyError("control_record_missing_required_field")
    
    # Dateiversion (schema_version) hart pruefen
    if payload["schema_version"] != CONTROL_FILE_VERSION:
        raise SafetyError("control_record_schema_version")
    
    # producer_version nur strukturell (Typ, Nichtleere) - S1 Fix
    if not isinstance(payload["producer_version"], str) or not payload["producer_version"]:
        raise SafetyError("control_record_producer_version")
    
    if scope_key is not None and scope_key not in payload:
        raise SafetyError("control_record_missing_scope_key")


def atomic_json_write(path: Any, data: dict[str, Any], mode: str = "w") -> None:
    """Schreibe JSON atomar mit fsync."""
    import os
    import tempfile
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, mode) as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def write_manifest(path: Any, manifest: FileManifest) -> None:
    """Schreibe FileManifest atomar."""
    atomic_json_write(path, {
        "schema_version": CONTROL_FILE_VERSION,
        "producer_version": CONTROL_FILE_VERSION.__class__.__module__.split('.')[0],
        "created_at": manifest.created_at,
        "updated_at": manifest.updated_at,
        "files": manifest.files,
    })
