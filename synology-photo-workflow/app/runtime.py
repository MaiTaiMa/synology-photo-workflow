"""
Skript: app/runtime.py
Zweck: Laufzeitklassen RunBudget, BatchLock, quarantine_batch und
       inspect_recovery für Budget-Steuerung, Batch-Locking und Recovery.
Autor: MaiTai
Erstellt: 2026-07-30
Version: 7.9.0
Requires: time, json, shutil, pathlib, datetime

Änderungsprotokoll:
  2026-08-08 | 7.9.0 | 00AP: RunBudget, BatchLock, quarantine_batch (mit
                               Manifest), inspect_recovery ergänzt.
"""
from __future__ import annotations

import json
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import VERSION
from .batch_state import load_state, state_path
from .safety import SafetyError

# ---------------------------------------------------------------------------
# Zeit-Budget-Kontrolle
# ---------------------------------------------------------------------------

class RunBudget:
    """Verhindert das Starten neuer teurer Schritte nach Budgetablauf.

    Der Konstruktor merkt sich den Startzeitpunkt. checkpoint() prüft
    vor jedem Schritt, ob das Budget erschöpft ist; Sekunden=0 bedeutet
    sofort erschöpft. Dies entspricht dem Not-Stop-Vertrag aus 00AP.md.
    """

    def __init__(self, budget_seconds: float) -> None:
        """Initialisiert das Budget; budget_seconds=0 führt sofort zu Ablauf."""
        self._deadline = time.monotonic() + budget_seconds

    def checkpoint(self, step_name: str) -> None:
        """Wirft SafetyError, wenn das Zeitbudget vor diesem Schritt erschöpft ist.

        Gemäß 00AP.md: keinen neuen teuren Schritt beginnen, wenn Budget
        erschöpft; aktuellen Schritt sicher abschließen war Aufgabe des Callers.
        """
        if time.monotonic() >= self._deadline:
            raise SafetyError(f"run_budget_exhausted_before:{step_name}")


# ---------------------------------------------------------------------------
# Exklusiver Batch-Lock (pro Batch, innerhalb eines Laufs)
# ---------------------------------------------------------------------------

class BatchLock:
    """Exklusiver Lock für einen einzelnen Batch.

    Verhindert parallele Verarbeitung desselben Batches. Erstellt eine
    Lock-Datei in runtime_dir/locks/<batch_id>.lock. Wirft SafetyError
    ('batch_lock_active:…') wenn der Lock bereits gesetzt ist.
    """

    def __init__(self, runtime_dir: str | Path, batch_id: str) -> None:
        """Legt Lock-Pfad fest; noch kein Dateisystem-Zugriff."""
        self._lock_file = Path(runtime_dir) / "locks" / f"{batch_id}.lock"
        self._batch_id = batch_id

    def __enter__(self) -> BatchLock:
        """Setzt den Lock oder wirft SafetyError bei Kollision."""
        self._lock_file.parent.mkdir(parents=True, exist_ok=True)
        # Atomare Erstellung via O_EXCL – verhindert TOCTOU-Race
        try:
            with self._lock_file.open("x", encoding="utf-8") as fh:
                fh.write(json.dumps({"batch_id": self._batch_id,
                                     "locked_at": datetime.now(UTC).isoformat()}))
        except FileExistsError:
            raise SafetyError(f"batch_lock_active:{self._batch_id}") from None
        return self

    def __exit__(self, *_: object) -> None:
        """Entfernt den Lock-Datei beim Verlassen des Kontexts."""
        self._lock_file.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Quarantäne-Funktion
# ---------------------------------------------------------------------------

def quarantine_batch(
    batch_path: Path,
    basedir: Path,
    quarantine_dir: Path,
    reason: str,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Verschiebt einen Batch in das Quarantäneverzeichnis und erstellt ein Manifest.

    Gibt den Zielpfad des quarantänisierten Batches zurück. Das Manifest
    wird unter SAVE/quarantine_manifest.json abgelegt; es enthält batch_id,
    reason und recovery_required=True für die spätere Inspektion.
    """
    quarantine_dir = Path(quarantine_dir)
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    batch_path = Path(batch_path)
    destination = quarantine_dir / batch_path.name
    if destination.exists():
        # Kollision: eindeutigen Namen wählen ohne Überschreibung
        idx = 1
        while (quarantine_dir / f"{batch_path.name}_{idx}").exists():
            idx += 1
        destination = quarantine_dir / f"{batch_path.name}_{idx}"
    shutil.move(str(batch_path), str(destination))
    # Quarantäne-Manifest schreiben
    save_dir = destination / "SAVE"
    save_dir.mkdir(exist_ok=True)
    now = datetime.now(UTC).isoformat()
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": now,
        "updated_at": now,
        "batch_id": batch_path.name,
        "reason": reason,
        "recovery_required": True,
    }
    if metadata:
        manifest["metadata"] = metadata
    (save_dir / "quarantine_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return destination


# ---------------------------------------------------------------------------
# Lesende Recovery-Inspektion
# ---------------------------------------------------------------------------

def inspect_recovery(runtime_dir: str | Path, batch_id: str) -> dict[str, Any]:
    """Liest den Batch-State und gibt eine lesende Recovery-Diagnose zurück.

    Gibt immer safe_to_auto_resume=False zurück, weil Recovery immer explizit
    durch den Menschen bestätigt werden muss (Sicherheit vor Nutzen).
    """
    path = state_path(runtime_dir, batch_id)
    state = load_state(path) or {}
    return {"safe_to_auto_resume": False, "state": state, "state_path": str(path)}


# ---------------------------------------------------------------------------
# Legacy-Hilfsfunktionen (WorkUnit-Checkpoint-Logik, intern)
# ---------------------------------------------------------------------------

def process_physical_batch(batch_path: Path, config: dict[str, Any]) -> None:
    """Verarbeite physischen Batch mit State-Machine (Legacy-Wrapper)."""
    target_path = Path(config["paths"]["temp_images"]) / batch_path.name
    shutil.move(str(batch_path), str(target_path))
