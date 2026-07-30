"""Projekt: Synology Photo Workflow
Datei: app/face_cache.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Datensparsame Referenzcache-Manifeste, deterministische Rebuild-Planung und sichere Match-Fachgrenze.
SICHERHEIT: Der Referenzcache speichert keine Roh-Embeddings und aktiviert keine Person ohne explizite Referenzauswahl.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from .face_backend import FaceBackendDiagnosis, FaceEmbedding, FaceMatch, FaceBackendProtocol, cache_fingerprint
from .family_recognition import selection_fingerprint, validate_selection
from .safety import SafetyError, atomic_json, sha256, utcnow


def rebuild_plan(person_root: str | Path, person_slug: str, selection: dict[str, Any], diagnosis: FaceBackendDiagnosis) -> dict[str, Any]:
    """Erstellt einen lesenden Plan: nur aktive Referenzen sind Quelle, nie newfaces oder notused."""
    root = Path(person_root)
    references = validate_selection(selection, person_slug)
    fingerprint = selection_fingerprint(selection, person_slug)
    cache_key = cache_fingerprint(diagnosis, fingerprint)
    items = []
    for reference in references:
        source = root / reference['relative_path']
        if not source.is_file() or source.is_symlink() or sha256(source) != reference['sha256']:
            raise SafetyError('reference_file_missing_or_changed')
        items.append({'relative_path': reference['relative_path'], 'sha256': reference['sha256']})
    return {'person_slug': person_slug, 'reference_count': len(items), 'selection_fingerprint': fingerprint, 'cache_fingerprint': cache_key, 'references': items, 'status': 'ready' if diagnosis.ready and items else 'blocked'}


def write_cache_manifest(cache_path: str | Path, plan: dict[str, Any], diagnosis: FaceBackendDiagnosis, embeddings: list[FaceEmbedding]) -> dict[str, Any]:
    """Schreibt ausschließlich Cache-Metadaten; rohe Vektoren verbleiben im flüchtigen Backendprozess."""
    if not diagnosis.ready or plan['status'] != 'ready':
        raise SafetyError('face_cache_rebuild_not_ready')
    now = utcnow()
    payload = {'schema_version': 1, 'cache_fingerprint': plan['cache_fingerprint'], 'created_at': now, 'updated_at': now, 'producer_version': '7.7.0', 'person_slug': plan['person_slug'], 'selection_fingerprint': plan['selection_fingerprint'], 'backend': diagnosis.backend, 'adapter_version': diagnosis.adapter_version, 'provider': diagnosis.provider, 'model_fingerprints': list(diagnosis.model_fingerprints), 'metric': diagnosis.metric.__dict__ if diagnosis.metric else None, 'reference_count': plan['reference_count'], 'embedding_count': len(embeddings), 'embedding_dimensions': sorted({embedding.dimension for embedding in embeddings}), 'vector_storage': 'none'}
    atomic_json(cache_path, payload, 'cache_fingerprint')
    return payload


def match_known(backend: FaceBackendProtocol, embedding: FaceEmbedding, references: dict[str, list[FaceEmbedding]]) -> FaceMatch:
    """Delegiert ausschließlich an einen expliziten Adapter; unbekannte/mehrdeutige Matches bleiben ohne Artefaktauftrag."""
    result = backend.compare(embedding, references)
    if result.status not in {'matched', 'unknown', 'ambiguous', 'noface', 'unmatched'}:
        raise SafetyError('face_match_status_invalid')
    return result
