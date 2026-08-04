"""app/face_cache.py — Cache-Plan, Cache-Manifest.

Spezifikation v10.2 - AP7
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from .face_backend import FaceBackendDiagnosis
from .safety import atomic_json, utcnow, sha256


def rebuild_plan(
    workflow_data: Path | str,
    person_slug: str,
    selection: dict[str, Any],
    diagnosis: FaceBackendDiagnosis,
) -> dict[str, Any]:
    """Erstellt Cache-Plan aus aktiven Referenzen."""
    ref_dir = Path(workflow_data) / "faces" / "reference" / person_slug
    active_refs = [
        f for f in selection.get("files", [])
        if f.get("status") == "active" and "reference/" in f.get("relative_path", "")
    ]
    
    return {
        "schema_version": 1,
        "person_slug": person_slug,
        "reference_count": len(active_refs),
        "status": "ready" if diagnosis.ready else "not_ready",
        "backend_diagnosis": {
            "ready": diagnosis.ready,
            "backend_id": diagnosis.backend_id,
            "message": diagnosis.message,
        },
    }


def write_cache_manifest(
    cache_path: Path | str,
    plan: dict[str, Any],
    diagnosis: FaceBackendDiagnosis,
    vectors: list[Any],
) -> None:
    """Schreibt Cache-Manifest (ohne Vektoren)."""
    from . import VERSION
    data = {
        "schema_version": 1,
        "created_at": utcnow(),
        "updated_at": utcnow(),
        "producer_version": VERSION,
        "cache_fingerprint": plan.get("person_slug", "unknown"),
        "plan": plan,
        "vector_storage": "none",  # Vektoren niemals persistent
        "backend_diagnosis": {
            "ready": diagnosis.ready,
            "backend_id": diagnosis.backend_id,
            "message": diagnosis.message,
        },
    }
    atomic_json(cache_path, data, "cache_fingerprint")
