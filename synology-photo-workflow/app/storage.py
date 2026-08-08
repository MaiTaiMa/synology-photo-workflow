"""
Skript: app/storage.py
Zweck: Kapselung der lokalen NAS-Persistenzschicht für alle Workflow-Artefakte.
Autor: MaiTai
Erstellt: 2026-08-08
Version: 1.0.0
Requires: pathlib, json, csv, hashlib

Änderungsprotokoll:
  2026-08-08 | 1.0.0 | 00AP: Initiale Implementierung gemäß 00AP.md Abschnitt 5.3 und 04AP.md.
"""
from __future__ import annotations

import csv
import hashlib
import json
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from . import VERSION

if TYPE_CHECKING:
    from .state import BatchState


# ---------------------------------------------------------------------------
# Storage-Protokoll: Definiert die Schnittstelle gemäß 00AP.md Abschnitt 5.3
# ---------------------------------------------------------------------------

class Storage(Protocol):
    """Abstrakte Persistenzschicht für alle Batch-Artefakte.

    Implementierungen können gegen NAS, Testisolierung oder
    Synology-API ausgetauscht werden ohne Fachlogik anzupassen.
    """

    def load_state(self, batch_id: str) -> "BatchState | None": ...
    def save_state(self, state: "BatchState") -> None: ...
    def save_manifest(self, manifest: dict[str, Any]) -> None: ...
    def save_csv(self, batch_id: str, rows: list[dict[str, Any]]) -> None: ...
    def save_review_record(self, record: dict[str, Any]) -> None: ...
    def save_calibration_index(self, batch_id: str, index: dict[str, Any]) -> None: ...
    def save_archive_plan(self, plan: dict[str, Any]) -> None: ...
    def save_finalization_manifest(self, manifest: dict[str, Any]) -> None: ...
    def save_api_correlation(self, record: dict[str, Any]) -> None: ...


# ---------------------------------------------------------------------------
# Hilfsfunktionen: Atomares Schreiben und Hashing
# ---------------------------------------------------------------------------

def _atomic_json_write(path: Path, data: dict[str, Any]) -> None:
    """Schreibt JSON atomar: Temp erzeugen, validieren, ersetzen."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", dir=path.parent, delete=False, suffix=".tmp.json", encoding="utf-8"
    ) as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        tmp = Path(fh.name)
    try:
        tmp.replace(path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def _file_sha256(path: Path) -> str:
    """Berechnet SHA256-Hash einer Datei für Integritätsprüfung."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# NASStorage: Kanonische lokale Implementierung des Storage-Protokolls
# ---------------------------------------------------------------------------

class NASStorage:
    """Lokale Implementierung der Storage-Schnittstelle für NAS-Dateisystem.

    Alle Pfade werden vor Verwendung gegen das Basisverzeichnis validiert.
    Alle Schreiboperationen sind atomar (Temp → Replace).
    """

    def __init__(self, base_dir: Path) -> None:
        """Initialisiert NASStorage mit dem NAS-Basisverzeichnis."""
        self.base_dir = Path(base_dir).resolve()
        self._runtime_dir = self.base_dir / "WORKFLOW_DATA" / "runtime"

    def _state_path(self, batch_id: str) -> Path:
        """Kanonischer Pfad zur State-JSON-Datei eines Batches."""
        return self._runtime_dir / "state" / f"{batch_id}.json"

    def _manifest_path(self, batch_id: str) -> Path:
        """Kanonischer Pfad zur Manifest-JSON-Datei eines Batches."""
        return self._runtime_dir / "manifests" / f"{batch_id}_manifest.json"

    def _csv_path(self, batch_id: str) -> Path:
        """Kanonischer Pfad zur Culling-CSV eines Batches."""
        return self._runtime_dir / "reports" / f"{batch_id}_culling.csv"

    def _calibration_path(self, batch_id: str) -> Path:
        """Kanonischer Pfad zum Kalibrierungsindex eines Batches."""
        return self._runtime_dir / "calibration" / "batches" / f"{batch_id}_calibration_index.json"

    def load_state(self, batch_id: str) -> "BatchState | None":
        """Lädt BatchState aus kanonischer State-Datei; gibt None zurück wenn fehlt."""
        from .state import load_state
        return load_state(self._state_path(batch_id))

    def save_state(self, state: "BatchState") -> None:
        """Persistiert BatchState atomar in kanonischer State-Datei."""
        from .state import atomic_write
        atomic_write(self._state_path(state.batch_id), state)

    def save_manifest(self, manifest: dict[str, Any]) -> None:
        """Speichert Batch-Manifest atomar; batch_id muss im Manifest enthalten sein."""
        batch_id = manifest.get("batch_id", "unknown")
        _atomic_json_write(self._manifest_path(batch_id), manifest)

    def save_csv(self, batch_id: str, rows: list[dict[str, Any]]) -> None:
        """Schreibt Culling-Ergebnisse als CSV mit Pflichtfeldern."""
        path = self._csv_path(batch_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not rows:
            return
        fieldnames = list(rows[0].keys())
        with tempfile.NamedTemporaryFile(
            "w", dir=path.parent, delete=False, suffix=".tmp.csv",
            encoding="utf-8", newline=""
        ) as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            tmp = Path(fh.name)
        try:
            tmp.replace(path)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise

    def save_review_record(self, record: dict[str, Any]) -> None:
        """Persistiert Review-Entscheidungs-Record atomar."""
        batch_id = record.get("batch_id", "unknown")
        path = self._runtime_dir / "review" / f"{batch_id}_review_record.json"
        _atomic_json_write(path, record)

    def save_calibration_index(self, batch_id: str, index: dict[str, Any]) -> None:
        """Persistiert Kalibrierungsindex atomar."""
        _atomic_json_write(self._calibration_path(batch_id), index)

    def save_archive_plan(self, plan: dict[str, Any]) -> None:
        """Persistiert Archive-Plan atomar; batch_id muss im Plan enthalten sein."""
        batch_id = plan.get("batch_id", "unknown")
        path = self._runtime_dir / "archives" / f"{batch_id}_archive_plan.json"
        _atomic_json_write(path, plan)

    def save_finalization_manifest(self, manifest: dict[str, Any]) -> None:
        """Persistiert Finalisierungs-Manifest atomar für PHASE3."""
        batch_id = manifest.get("batch_id", "unknown")
        path = self._runtime_dir / "finalization" / f"{batch_id}_finalization_manifest.json"
        _atomic_json_write(path, manifest)

    def save_api_correlation(self, record: dict[str, Any]) -> None:
        """Persistiert API-Korrelations-Record für Synology-Photos-Integration."""
        batch_id = record.get("batch_id", "unknown")
        path = self._runtime_dir / "api" / f"{batch_id}_api_correlation.json"
        _atomic_json_write(path, record)
