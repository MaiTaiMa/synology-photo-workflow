"""Projekt: Synology Photo Workflow
Datei: app/eye_state_adapter_onnx.py
Mitentwickler: MaiTai
Erstellt: 2026-08-02
Projektversion: 7.9.0
Funktion: Adapter fuer ein ONNX-Modell zur Augenzustandserkennung (offen/geschlossen); liefert
          pro Gesicht ausschliesslich einen optionalen open_eye_score, niemals eine Entscheidung.
SICHERHEIT: Ohne onnxruntime, ohne gueltiges Modell oder bei Inferenzfehler liefert der Adapter
            eine ModelDiagnosis mit reason_code != 'ready'; aufrufender Code behandelt den Score
            dann als nicht verfuegbar statt als neutral 'Augen offen'.
HINWEIS: Neu, noch nicht in Face-Pipeline verdrahtet (siehe FEATURE_BRANCH_V7_9_0_TODO.md).
"""
from __future__ import annotations

from typing import Any

import numpy as np

from .model_diagnostics import ModelDiagnosis, dependency_missing, disabled
from .model_runtime import ModelRuntime

ADAPTER_VERSION = '1.0.0'
BACKEND = 'eye_state_onnx'


class EyeStateAdapterOnnx:
    def __init__(self, runtime: ModelRuntime, config: dict[str, Any]) -> None:
        self.runtime = runtime
        self.config = config.get('models', {}).get('eye_state', {})
        self.enabled = bool(self.config.get('enabled', False))
        self.input_size = int(self.config.get('input_size', 64))
        self._session: Any = None
        self._diagnosis: ModelDiagnosis | None = None

    def diagnose(self) -> ModelDiagnosis:
        if self._diagnosis is not None:
            return self._diagnosis
        if not self.enabled:
            self._diagnosis = disabled(BACKEND)
            return self._diagnosis
        try:
            import onnxruntime  # noqa: F401
        except ImportError:
            self._diagnosis = dependency_missing(BACKEND, 'onnxruntime')
            return self._diagnosis
        relative_paths = {'model': self.config.get('model_path', '')}
        diagnosis = self.runtime.diagnose_paths(BACKEND, ADAPTER_VERSION, relative_paths, self.enabled)
        if diagnosis is not None:
            self._diagnosis = diagnosis
            return diagnosis
        self._diagnosis = ModelDiagnosis(True, True, BACKEND, ADAPTER_VERSION, 'onnxruntime', tuple(relative_paths.values()), (self.runtime.fingerprint(self.runtime.resolve_model_path(relative_paths['model'])),), 'ready', 'model_ready')
        return self._diagnosis

    def _load(self) -> Any | None:
        diagnosis = self.diagnose()
        if not diagnosis.ready:
            return None
        def loader() -> Any:
            import onnxruntime
            model_path = self.runtime.resolve_model_path(self.config['model_path'])
            return onnxruntime.InferenceSession(str(model_path), providers=['CPUExecutionProvider'])
        try:
            return self.runtime.get_or_load(BACKEND, loader)
        except Exception:
            return None

    def open_eye_score(self, eye_crop_rgb: Any) -> float | None:
        session = self._load()
        if session is None:
            return None
        try:
            resized = eye_crop_rgb.resize((self.input_size, self.input_size))
            array = np.asarray(resized, dtype=np.float32) / 255.0
            array = np.transpose(array, (2, 0, 1))[np.newaxis, ...]
            input_name = session.get_inputs()[0].name
            outputs = session.run(None, {input_name: array})
            score = float(outputs[0].reshape(-1)[0])
            return max(0.0, min(1.0, score))
        except Exception:
            return None
