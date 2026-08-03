"""Projekt: Synology Photo Workflow
Datei: app/manual_keep_similarity.py
Mitentwickler: MaiTai
Erstellt: 2026-08-02
Projektversion: 7.9.0
Funktion: Berechnet rein technische Aehnlichkeitswerte (perceptual hash, optional CLIP-Serie)
          zwischen einem manuell markierten Keep-Bild und den uebrigen Bildern seiner Serie, um
          der Manual-Keep-Ansicht Vorschlaege zu liefern; trifft selbst keine Entscheidung.
SICHERHEIT: Ohne verfuegbares Feature (Hash oder Embedding) wird das betroffene Bild als
            'similarity_unavailable' markiert statt mit einem Default-Wert von 0.0 oder 1.0.
HINWEIS: Neu, noch nicht in die Manual-Keep-UI verdrahtet (siehe FEATURE_BRANCH_V7_9_0_TODO.md).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .image_features import ImageFeatureService


@dataclass(frozen=True)
class SimilarityResult:
    path: Path
    hash_similarity: float | None
    embedding_similarity: float | None
    available: bool


def _hamming_similarity(hash_a: str, hash_b: str) -> float | None:
    if not hash_a or not hash_b or len(hash_a) != len(hash_b):
        return None
    distance = sum(1 for x, y in zip(hash_a, hash_b) if x != y)
    return 1.0 - (distance / len(hash_a))


def similarity_to_keep(service: ImageFeatureService, keep_path: Path, candidate_paths: list[Path], embedding_lookup: dict[Path, tuple[float, ...] | None] | None = None) -> list[SimilarityResult]:
    keep_features = service.features(keep_path, need_hash=True)
    results: list[SimilarityResult] = []
    for candidate in candidate_paths:
        candidate_features = service.features(candidate, need_hash=True)
        hash_similarity = None
        if keep_features and candidate_features and keep_features.perceptual_hash and candidate_features.perceptual_hash:
            hash_similarity = _hamming_similarity(keep_features.perceptual_hash, candidate_features.perceptual_hash)
        embedding_similarity = None
        if embedding_lookup is not None:
            keep_embedding = embedding_lookup.get(keep_path)
            candidate_embedding = embedding_lookup.get(candidate)
            if keep_embedding and candidate_embedding and len(keep_embedding) == len(candidate_embedding):
                embedding_similarity = sum(x * y for x, y in zip(keep_embedding, candidate_embedding))
        available = hash_similarity is not None or embedding_similarity is not None
        results.append(SimilarityResult(candidate, hash_similarity, embedding_similarity, available))
    return results
