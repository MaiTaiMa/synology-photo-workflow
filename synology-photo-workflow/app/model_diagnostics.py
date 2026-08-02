"""Projekt: Synology Photo Workflow
Datei: app/model_diagnostics.py
Mitentwickler: MaiTai
Erstellt: 2026-08-02
Projektversion: 7.9.0
Funktion: Gemeinsamer ModelDiagnosis-Vertrag und standardisierte reason_code-Werte fuer alle
          KI-Adapter (CLIP, Serienmodell, Face, Eye-State).
SICHERHEIT: Kein Adapter wechselt bei einem Fehler unbemerkt Modell oder Backend; ein deaktiviertes
            oder fehlerhaftes Modell erzeugt niemals einen Dummy-Score.
HINWEIS: Neu, noch nicht in bestehende Adapter verdrahtet (siehe FEATURE_BRANCH_V7_9_0_TODO.md).
"""
from __future__ import annotations

from dataclasses import dataclass

REASON_CODES = frozenset({
    'disabled', 'dependency_missing', 'model_path_invalid', 'model_file_missing',
    'model_manifest_invalid', 'model_hash_mismatch', 'model_load_failed',
    'budget_exhausted', 'worker_failed', 'unsupported_backend', 'ready',
})


@dataclass(frozen=True)
class ModelDiagnosis:
    enabled: bool
    ready: bool
    backend: str
    adapter_version: str
    provider: str
    model_paths: tuple[str, ...]
    model_fingerprints: tuple[str, ...]
    reason_code: str
    message: str

    def __post_init__(self) -> None:
        if self.reason_code not in REASON_CODES:
            raise ValueError(f'unknown_reason_code:{self.reason_code}')
        if self.ready and self.reason_code != 'ready':
            raise ValueError('ready_requires_reason_code_ready')
        if not self.enabled and self.ready:
            raise ValueError('disabled_model_cannot_be_ready')


def disabled(backend: str) -> ModelDiagnosis:
    return ModelDiagnosis(False, False, backend, 'none', 'none', (), (), 'disabled', 'model_disabled_by_configuration')


def dependency_missing(backend: str, module_name: str) -> ModelDiagnosis:
    return ModelDiagnosis(True, False, backend, 'none', 'none', (), (), 'dependency_missing', f'module_not_installed:{module_name}')
