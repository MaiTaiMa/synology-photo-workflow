"""app/face_backend.py — MatchMetric, match_valid, diagnose, FaceBackendDiagnosis.

Spezifikation v10.2 - AP6
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MatchMetric:
    """Beschreibt eine Face-Matching-Metrik mit Threshold und Margin."""
    name: str
    direction: str  # 'higher_is_better' | 'lower_is_better'
    threshold: float
    margin: float


@dataclass(frozen=True)
class BackendDiagnosis:
    """Ergebnis der Backend-Bereitschaftspruefung."""
    backend: str
    execution_profile: str
    ready: bool
    reason: str | None = None
    message: str | None = None


@dataclass(frozen=True)
class FaceBackendDiagnosis:
    """Erweitertes Diagnoseergebnis mit Modellhashes und Metrik."""
    ready: bool
    backend_id: str
    message: str
    version: str | None
    metric: MatchMetric
    execution_provider: str
    model_hashes: tuple


def match_valid(score: float, second_best: float | None, metric: MatchMetric) -> bool:
    """Prueft ob ein Match gueltig ist (threshold + margin eingehalten)."""
    if second_best is None:
        return False
    if metric.direction == "higher_is_better":
        return score >= metric.threshold and (score - second_best) >= metric.margin
    elif metric.direction == "lower_is_better":
        return score <= metric.threshold and (second_best - score) >= metric.margin
    return False


_CUDA_BACKENDS = {"onnx_face_cuda"}
_CPU_BACKENDS = {
    "opencv_yunet_sface_cpu",
    "onnx_face_cpu",
    "face_recognition_dlib_cpu",
    "insightface_onnx",
}


def diagnose(backend: str, execution_profile: str) -> BackendDiagnosis:
    """Prueft Backend-Bereitschaft (Stub)."""
    if backend in _CUDA_BACKENDS and execution_profile != "cuda":
        return BackendDiagnosis(
            backend=backend,
            execution_profile=execution_profile,
            ready=False,
            reason="execution_profile_mismatch",
            message="execution_profile_mismatch",
        )
    return BackendDiagnosis(
        backend=backend,
        execution_profile=execution_profile,
        ready=False,  # Standard: nicht bereit ohne Modelle
        reason="models_missing",
        message="models_missing",
    )
