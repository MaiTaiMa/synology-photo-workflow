"""Projekt: Synology Photo Workflow
Datei: app/clip_series_adapter.py
Mitentwickler: MaiTai
Erstellt: 2026-08-02
Projektversion: 7.9.0
Funktion: Adapter fuer CLIP-basierte Serien-Embeddings; liefert ausschliesslich Aehnlichkeits-
          Scores zwischen Bildern derselben Serie, niemals eine Keep/Delete-Entscheidung.
SICHERHEIT: Bei fehlendem Modell, fehlender Abhaengigkeit oder Ladefehler liefert der Adapter eine
            ModelDiagnosis mit reason_code != 'ready' und wird von aufrufendem Code als optional
            behandelt; niemals ein Dummy-Embedding oder Zufallswert.
HINWEIS: Neu, noch nicht in phases.py verdrahtet (siehe FEATURE_BRANCH_V7_9_0_TODO.md).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .image_features import ImageFeatureService, NormalizedImage
from .model_diagnostics import ModelDiagnosis, dependency_missing
from .model_runtime import ModelRuntime

ADAPTER_VERSION = '1.0.0'
BACKEND = 'clip_series'


class ClipSeriesAdapter:
    def __init__(self, runtime: ModelRuntime, config: dict[str, Any]) -> None:
        self.runtime = runtime
        self.config = config.get('models', {}).get('clip_series', {})
        self.enabled = bool(self.config.get('enabled', False))
        self._model: Any = None
        self._diagnosis: ModelDiagnosis | None = None

    def diagnose(self) -> ModelDiagnosis:
        if self._diagnosis is not None:
            return self._diagnosis
        if not self.enabled:
            from .model_diagnostics import disabled
            self._diagnosis = disabled(BACKEND)
            return self._diagnosis
        try:
            import open_clip  # noqa: F401
        except ImportError:
            self._diagnosis = dependency_missing(BACKEND, 'open_clip')
            return self._diagnosis
        relative_paths = {'weights': self.config.get('weights_path', '')}
        diagnosis = self.runtime.diagnose_paths(BACKEND, ADAPTER_VERSION, relative_paths, self.enabled)
        if diagnosis is not None:
            self._diagnosis = diagnosis
            return diagnosis
        self._diagnosis = ModelDiagnosis(True, True, BACKEND, ADAPTER_VERSION, 'local', tuple(relative_paths.values()), (self.runtime.fingerprint(self.runtime.resolve_model_path(relative_paths['weights'])),), 'ready', 'model_ready')
        return self._diagnosis

    def _load(self) -> Any | None:
        diagnosis = self.diagnose()
        if not diagnosis.ready:
            return None
        def loader() -> Any:
            import open_clip
            weights_path = self.runtime.resolve_model_path(self.config['weights_path'])
            model, _, preprocess = open_clip.create_model_and_transforms(self.config.get('model_name', 'ViT-B-32'), pretrained=str(weights_path))
            model.eval()
            return (model, preprocess)
        try:
            return self.runtime.get_or_load(BACKEND, loader)
        except Exception:
            return None

    def embed(self, image: NormalizedImage) -> tuple[float, ...] | None:
        loaded = self._load()
        if loaded is None:
            return None
        model, preprocess = loaded
        try:
            import torch
            tensor = preprocess(image.rgb_image).unsqueeze(0)
            with torch.no_grad():
                features = model.encode_image(tensor)
                normalized = features / features.norm(dim=-1, keepdim=True)
            return tuple(normalized.squeeze(0).tolist())
        except Exception:
            return None

    @staticmethod
    def cosine_similarity(a: tuple[float, ...], b: tuple[float, ...]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        return sum(x * y for x, y in zip(a, b))

    def series_similarity(self, service: ImageFeatureService, paths: list[Path]) -> dict[Path, float | None]:
        embeddings: dict[Path, tuple[float, ...] | None] = {}
        for path in paths:
            image = service.load_rgb(path)
            embeddings[path] = self.embed(image) if image is not None else None
        results: dict[Path, float | None] = {}
        valid = [(p, e) for p, e in embeddings.items() if e is not None]
        for path, embedding in embeddings.items():
            if embedding is None or len(valid) < 2:
                results[path] = None
                continue
            others = [self.cosine_similarity(embedding, other) for p, other in valid if p != path]
            results[path] = sum(others) / len(others) if others else None
        return results
