"""app/face_adapter_yunet_sface_cpu.py — Optionaler YuNet/SFace CPU-Adapter.

Diagnose-only: Prueft Modellpfade und OpenCV-Verfuegbarkeit ohne biometrische Daten.
"""
from __future__ import annotations
from pathlib import Path
from .face_backend import FaceBackendDiagnosis, MatchMetric


_DEFAULT_METRIC = MatchMetric("cosine_similarity", "higher_is_better", 0.363, 0.03)


class YuNetSFaceCPUAdapter:
    """Adapter fuer YuNet (Detektion) + SFace (Embedding), CPU-only."""

    BACKEND_ID = "opencv_yunet_sface_cpu"

    def __init__(self, yunet_model_path: str, sface_model_path: str) -> None:
        self._yunet = Path(yunet_model_path)
        self._sface = Path(sface_model_path)

    def diagnose(self) -> FaceBackendDiagnosis:
        # OpenCV-Verfuegbarkeit pruefen
        try:
            import cv2  # noqa: F401
            has_face = hasattr(cv2, "FaceDetectorYN")
        except ImportError:
            return FaceBackendDiagnosis(
                ready=False,
                backend_id=self.BACKEND_ID,
                message="opencv_not_installed",
                version=None,
                metric=_DEFAULT_METRIC,
                execution_provider="CPUExecutionProvider",
                model_hashes=(),
            )

        if not has_face:
            return FaceBackendDiagnosis(
                ready=False,
                backend_id=self.BACKEND_ID,
                message="opencv_not_installed",
                version=None,
                metric=_DEFAULT_METRIC,
                execution_provider="CPUExecutionProvider",
                model_hashes=(),
            )

        missing = [p for p in (self._yunet, self._sface) if not p.is_file()]
        if missing:
            return FaceBackendDiagnosis(
                ready=False,
                backend_id=self.BACKEND_ID,
                message="model_file_missing:" + ",".join(p.name for p in missing),
                version=None,
                metric=_DEFAULT_METRIC,
                execution_provider="CPUExecutionProvider",
                model_hashes=(),
            )

        import cv2
        version = cv2.__version__
        return FaceBackendDiagnosis(
            ready=True,
            backend_id=self.BACKEND_ID,
            message="ready",
            version=version,
            metric=_DEFAULT_METRIC,
            execution_provider="CPUExecutionProvider",
            model_hashes=(),
        )
