"""Projekt: Synology Photo Workflow
Datei: app/model_runtime.py
Mitentwickler: MaiTai
Erstellt: 2026-08-02
Projektversion: 7.9.0
Funktion: Laedt und cached lokale Modellverzeichnisse pro Lauf im Speicher, ohne Netzwerkzugriff
          und ohne implizite Installation; reine Laufzeitschicht unterhalb der Adapter.
SICHERHEIT: Kein Modell wird aus dem Netz nachgeladen; fehlende oder ungueltige Pfade fuehren zu
            einer ModelDiagnosis, nie zu einem Absturz oder stillen Fallback.
HINWEIS: Neu, noch nicht von Adaptern konsumiert (siehe FEATURE_BRANCH_V7_9_0_TODO.md).
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .model_diagnostics import ModelDiagnosis, disabled
from .safety import require_within, sha256


class ModelRuntime:
    def __init__(self, models_root: str | Path) -> None:
        self.models_root = Path(models_root)
        self._loaded: dict[str, Any] = {}

    def resolve_model_path(self, relative_path: str) -> Path:
        return require_within(self.models_root, self.models_root / relative_path)

    def fingerprint(self, path: Path) -> str:
        return sha256(path)

    def get_or_load(self, key: str, loader: Callable[[], Any]) -> Any:
        if key not in self._loaded:
            self._loaded[key] = loader()
        return self._loaded[key]

    def diagnose_paths(self, backend: str, adapter_version: str, relative_paths: dict[str, str], enabled: bool) -> ModelDiagnosis | None:
        if not enabled:
            return disabled(backend)
        for name, relative in relative_paths.items():
            try:
                resolved = self.resolve_model_path(relative)
            except Exception:
                return ModelDiagnosis(True, False, backend, adapter_version, 'none', (), (), 'model_path_invalid', f'model_path_outside_models_dir:{name}')
            if not resolved.is_file():
                return ModelDiagnosis(True, False, backend, adapter_version, 'none', (), (), 'model_file_missing', f'model_file_missing:{name}')
        return None

    def clear(self) -> None:
        self._loaded.clear()
