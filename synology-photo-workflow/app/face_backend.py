"""Projekt: Synology Photo Workflow
Datei: app/face_backend.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Modellneutraler Face-Backend-Vertrag, deterministische Registry, Diagnose und richtungsbewusste Match-Prüfung.
SICHERHEIT: Modellwahl ist explizit; keine stillen Backend- oder Metrik-Fallbacks.
"""
from __future__ import annotations

import hashlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence


@dataclass(frozen=True)
class MatchMetric:
    """Beschreibt Richtung, Schwelle und Sicherheitsmarge einer Vergleichsmetrik."""
    name: str
    direction: str
    threshold: float | None = None
    margin: float | None = None


@dataclass(frozen=True)
class FaceEmbedding:
    """Backendinterne Repräsentation; Vektoren dürfen nie in Reports oder Metadaten erscheinen."""
    vector: tuple[float, ...]
    backend: str
    model_fingerprint: str
    dimension: int
    bounding_box: tuple[int, int, int, int]


@dataclass(frozen=True)
class FaceMatch:
    """Datensparsame fachliche Match-Antwort ohne Roh-Embedding."""
    status: str
    person_slug: str | None = None
    score: float | None = None
    second_best_score: float | None = None
    metric: str | None = None
    backend: str | None = None


@dataclass(frozen=True)
class FaceBackendDiagnosis:
    """Seiteneffektfreie Diagnose für CLI und Betriebsdokumentation."""
    ready: bool
    backend: str
    message: str
    adapter_version: str
    metric: MatchMetric | None = None
    provider: str | None = None
    model_fingerprints: tuple[str, ...] = ()


class FaceBackendProtocol(Protocol):
    """Die einzige adapterübergreifende Schnittstelle für family_recognition."""
    name: str
    adapter_version: str
    metric: MatchMetric

    def diagnose(self) -> FaceBackendDiagnosis: ...
    def detect_and_embed(self, image_path: Path) -> list[FaceEmbedding]: ...
    def compare(self, embedding: FaceEmbedding, references: dict[str, Sequence[FaceEmbedding]]) -> FaceMatch: ...


REGISTRY = {
    'opencv_yunet_sface_cpu': {'status': 'stable', 'profile': 'cpu', 'module': 'cv2'},
    'onnx_face_cpu': {'status': 'advanced', 'profile': 'cpu', 'module': 'onnxruntime'},
    'onnx_face_cuda': {'status': 'advanced', 'profile': 'cuda', 'module': 'onnxruntime'},
    'face_recognition_dlib_cpu': {'status': 'experimental', 'profile': 'cpu', 'module': 'face_recognition'},
    'insightface_onnx': {'status': 'experimental', 'profile': 'cpu_or_cuda', 'module': 'insightface'},
}


def _model_hashes(options: dict) -> tuple[str, ...]:
    """Fingerprinted lokale Modelldateien ohne Modellinhalt in Logs zu geben."""
    values = []
    for key in ('detector_model', 'recognizer_model'):
        value = options.get(key)
        if value and Path(value).is_file():
            values.append(hashlib.sha256(Path(value).read_bytes()).hexdigest())
    return tuple(values)


def diagnose(name: str, profile: str, options: dict | None = None) -> FaceBackendDiagnosis:
    """Prüft Registry, Profil, Dependency und konfigurierte Modelldateien ohne Bild-/Cachezugriff."""
    options = options or {}
    entry = REGISTRY.get(name)
    if not entry:
        return FaceBackendDiagnosis(False, name, 'backend_not_registered', 'none')
    allowed = entry['profile']
    if allowed != 'cpu_or_cuda' and profile != allowed:
        return FaceBackendDiagnosis(False, name, 'execution_profile_mismatch', 'none')
    if importlib.util.find_spec(entry['module']) is None:
        return FaceBackendDiagnosis(False, name, 'adapter_dependency_not_installed', 'none')
    required = [key for key in ('detector_model', 'recognizer_model') if options.get(key)]
    missing = [key for key in required if not Path(options[key]).is_file()]
    if missing:
        return FaceBackendDiagnosis(False, name, f'model_file_missing:{",".join(missing)}', 'none')
    metric = MatchMetric(options.get('metric_name', 'cosine_similarity'), options.get('metric_direction', 'higher_is_better'), options.get('match_threshold'), options.get('min_best_second_margin'))
    if metric.direction not in {'higher_is_better', 'lower_is_better'}:
        return FaceBackendDiagnosis(False, name, 'metric_direction_invalid', 'none')
    provider = 'CUDAExecutionProvider' if profile == 'cuda' else 'CPUExecutionProvider'
    return FaceBackendDiagnosis(True, name, 'adapter_ready_for_explicit_rebuild', '1.0', metric, provider, _model_hashes(options))


def match_valid(best: float | None, second: float | None, metric: MatchMetric) -> bool:
    """Wendet Schwelle und Marge nur gemäß deklarierter Richtung an; fehlende Werte bleiben unsicher."""
    if best is None or second is None or metric.threshold is None or metric.margin is None:
        return False
    if metric.direction == 'higher_is_better':
        return best >= metric.threshold and best - second >= metric.margin
    if metric.direction == 'lower_is_better':
        return best <= metric.threshold and second - best >= metric.margin
    return False


def cache_fingerprint(diagnosis: FaceBackendDiagnosis, selection_fingerprint: str, preprocessing_version: str = '1') -> str:
    """Bindet Cache strikt an Adapter, Metrik, Provider, Modelle, Vorverarbeitung und Auswahl."""
    if not diagnosis.ready or diagnosis.metric is None:
        raise ValueError('face_backend_not_ready')
    parts = (diagnosis.backend, diagnosis.adapter_version, diagnosis.provider, diagnosis.metric.name, diagnosis.metric.direction, diagnosis.model_fingerprints, selection_fingerprint, preprocessing_version)
    return hashlib.sha256(repr(parts).encode()).hexdigest()
