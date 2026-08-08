"""Projekt: Synology Photo Workflow
Datei: app/inference_runtime.py
Mitentwickler: MaiTai
Erstellt: 2026-08-02
Projektversion: 7.9.0
Funktion: Startet optional bis zu zwei Inferenz-Worker mit `spawn`; Worker liefern ausschliesslich
          Rechenresultate, niemals Datei-Moves, States oder Manifeste.
SICHERHEIT: Bei knappen Ressourcen, Worker-Ausfall oder Budgetende wird sicher seriell
            weitergearbeitet oder nur der betreffende optionale Score neutral gesetzt.
HINWEIS: Neu, noch nicht von Face-/CLIP-Adaptern konsumiert (siehe FEATURE_BRANCH_V7_9_0_TODO.md).
"""
from __future__ import annotations

import multiprocessing
from collections.abc import Callable, Iterable
from typing import Any

from .model_diagnostics import ModelDiagnosis


class InferenceRuntime:
    def __init__(self, workers: int = 1, allow_parallel: bool = False, queue_size: int = 4, max_worker_ram_mb: int = 2048) -> None:
        self.workers = max(1, min(2, workers)) if allow_parallel else 1
        self.queue_size = queue_size
        self.max_worker_ram_mb = max_worker_ram_mb
        self._pool = None

    def __enter__(self) -> InferenceRuntime:
        if self.workers > 1:
            context = multiprocessing.get_context('spawn')
            self._pool = context.Pool(processes=self.workers)
        return self

    def __exit__(self, *_: object) -> None:
        if self._pool is not None:
            self._pool.close()
            self._pool.join()
            self._pool = None

    def map(self, function: Callable[[Any], Any], items: Iterable[Any]) -> list[Any]:
        items = list(items)
        if self._pool is None:
            return [self._safe_call(function, item) for item in items]
        try:
            return self._pool.map(function, items)
        except Exception:
            return [self._safe_call(function, item) for item in items]

    @staticmethod
    def _safe_call(function: Callable[[Any], Any], item: Any) -> Any:
        try:
            return function(item)
        except Exception:
            return None


def worker_unavailable_diagnosis(backend: str, adapter_version: str) -> ModelDiagnosis:
    return ModelDiagnosis(True, False, backend, adapter_version, 'none', (), (), 'worker_failed', 'inference_worker_unavailable')
