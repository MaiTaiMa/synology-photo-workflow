"""Projekt: Synology Photo Workflow
Datei: app/face_adapter_yunet_sface_cpu.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Optionaler CPU-Referenzadapter für YuNet/SFace mit klaren Modellpfaden und defensiver Fehlergrenze.
SICHERHEIT: Ohne explizite Modellpfade und installierte OpenCV-Contrib-Komponenten bleibt das Backend deaktiviert.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .face_backend import FaceBackendDiagnosis, FaceBackendProtocol, FaceEmbedding, FaceMatch, MatchMetric, match_valid

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None


@dataclass
class YuNetSFaceCPUAdapter(FaceBackendProtocol):
    """Kleiner optionaler Referenzadapter; produktive Nutzung setzt explizite Modelle voraus."""
    detector_model: str
    recognizer_model: str
    threshold: float = 0.95
    margin: float = 0.03
    name: str = 'opencv_yunet_sface_cpu'
    adapter_version: str = '1.1'

    @property
    def metric(self) -> MatchMetric:
        return MatchMetric('cosine_similarity', 'higher_is_better', self.threshold, self.margin)

    def diagnose(self) -> FaceBackendDiagnosis:
        if cv2 is None:
            return FaceBackendDiagnosis(False, self.name, 'opencv_not_installed', self.adapter_version)
        detector = Path(self.detector_model)
        recognizer = Path(self.recognizer_model)
        missing = [p.name for p in (detector, recognizer) if not p.is_file()]
        if missing:
            return FaceBackendDiagnosis(False, self.name, f'model_file_missing:{",".join(missing)}', self.adapter_version)
        if not hasattr(cv2, 'FaceDetectorYN') or not hasattr(cv2, 'FaceRecognizerSF'):
            return FaceBackendDiagnosis(False, self.name, 'opencv_face_modules_unavailable', self.adapter_version)
        return FaceBackendDiagnosis(True, self.name, 'adapter_ready_for_explicit_rebuild', self.adapter_version, self.metric, 'CPUExecutionProvider', ())

    def detect_and_embed(self, image_path: Path) -> list[FaceEmbedding]:
        diagnosis = self.diagnose()
        if not diagnosis.ready:
            raise RuntimeError(diagnosis.message)
        image = cv2.imread(str(image_path))
        if image is None:
            return []
        detector = cv2.FaceDetectorYN.create(self.detector_model, '', (image.shape[1], image.shape[0]))
        _, faces = detector.detect(image)
        if faces is None:
            return []
        recognizer = cv2.FaceRecognizerSF.create(self.recognizer_model, '')
        embeddings: list[FaceEmbedding] = []
        for face in faces:
            aligned = recognizer.alignCrop(image, face)
            feature = recognizer.feature(aligned).flatten().tolist()
            x, y, w, h = [int(v) for v in face[:4]]
            embeddings.append(FaceEmbedding(tuple(float(v) for v in feature), self.name, 'explicit-model-paths', len(feature), (x, y, w, h)))
        return embeddings

    def compare(self, embedding: FaceEmbedding, references: dict[str, Sequence[FaceEmbedding]]) -> FaceMatch:
        diagnosis = self.diagnose()
        if not diagnosis.ready:
            raise RuntimeError(diagnosis.message)
        recognizer = cv2.FaceRecognizerSF.create(self.recognizer_model, '')
        best_slug, best_score, second_score = None, None, None
        query = tuple(float(v) for v in embedding.vector)
        for slug, items in references.items():
            for item in items:
                score = float(recognizer.match(query, tuple(float(v) for v in item.vector), cv2.FaceRecognizerSF_FR_COSINE))
                if best_score is None or score > best_score:
                    second_score = best_score
                    best_score = score
                    best_slug = slug
                elif second_score is None or score > second_score:
                    second_score = score
        if match_valid(best_score, second_score, self.metric):
            return FaceMatch('matched', best_slug, best_score, second_score, self.metric.name, self.name)
        return FaceMatch('unknown', None, best_score, second_score, self.metric.name, self.name)
