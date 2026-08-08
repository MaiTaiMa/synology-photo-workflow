"""
Skript: app/face_cache.py
Zweck: Referenz-Cache-Plan und Manifest für Face-Erkennung. Speichert
       ausschließlich Metadaten – niemals Embeddings oder Pixeldaten.
Autor: MaiTai
Erstellt: 2026-07-30
Version: 7.9.0
Requires: hashlib, pathlib, datetime

Änderungsprotokoll:
  2026-08-08 | 7.9.0 | 00AP: rebuild_plan und write_cache_manifest ergänzt.
"""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import VERSION
from .result_contract import atomic_json_write

if TYPE_CHECKING:
    from .face_backend import FaceBackendDiagnosis


def rebuild_plan(
    base_path: str | Path,
    person_slug: str,
    selection: dict[str, Any],
    diagnosis: FaceBackendDiagnosis,
) -> dict[str, Any]:
    """Erstellt einen Cache-Plan aus der Referenzauswahl für eine Person.

    Zählt ausschließlich Dateien mit status='active' aus dem Ordner
    'reference/'. newfaces/ und andere Unterordner werden ignoriert.
    Embeddings werden nie persistiert – nur Datei-Hashes und Zählungen.
    """
    base = Path(base_path)
    active_refs = [
        entry
        for entry in selection.get("files", [])
        if entry.get("status") == "active"
        and entry.get("relative_path", "").startswith("reference/")
        and (base / entry["relative_path"]).exists()
    ]
    # Fingerprint aus Dateihashes
    selection_fingerprint = hashlib.sha256(
        repr(sorted(e.get("sha256", "") for e in active_refs)).encode()
    ).hexdigest()
    status = "ready" if diagnosis.ready and active_refs else "no_references"
    return {
        "person_slug": person_slug,
        "reference_count": len(active_refs),
        "selection_fingerprint": selection_fingerprint,
        "status": status,
    }


def write_cache_manifest(
    manifest_path: str | Path,
    plan: dict[str, Any],
    diagnosis: FaceBackendDiagnosis,
    vectors: list[Any],
) -> dict[str, Any]:
    """Schreibt das Face-Cache-Manifest atomar. Embeddings werden nie persistiert.

    Der Vertrag: vector_storage ist immer 'none'. Alle Embeddings existieren
    nur RAM-flüchtig während des aktiven Container-Laufs.
    """
    from .face_backend import cache_fingerprint as _cf
    # Fingerprint bindet Cache an Adapter, Metrik und Referenzauswahl
    try:
        fp = _cf(diagnosis, plan.get("selection_fingerprint", ""))
    except ValueError:
        fp = "backend_not_ready"
    data: dict[str, Any] = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "person_slug": plan.get("person_slug"),
        "reference_count": plan.get("reference_count", 0),
        "status": plan.get("status"),
        "cache_fingerprint": fp,
        # Explizite Sicherheitsdeklaration: Embeddings werden nie gespeichert
        "vector_storage": "none",
    }
    atomic_json_write(str(manifest_path), data)
    return data
