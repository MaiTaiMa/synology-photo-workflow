"""
Skript: app/batch_state.py
Zweck: Kanonische State-JSON-Machine, state_path, write_state und load_state
       für Batch-Recovery und Pause-Erkennung.
Autor: MaiTai
Erstellt: 2026-07-30
Version: 7.9.0
Requires: json, pathlib, datetime

Änderungsprotokoll:
  2026-08-08 | 7.9.0 | 00AP: state_path, write_state (neues Schema), load_state ergänzt.
"""
from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import VERSION

if TYPE_CHECKING:
    from .work_units import WorkUnitPlan


# ---------------------------------------------------------------------------
# Kanonischer State-Pfad (pro Batch im runtime/state-Verzeichnis)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Kanonische Zustandsreihenfolge (00AP.md Abschnitt 7)
# ---------------------------------------------------------------------------
_STATE_ORDER: dict[str, int] = {
    "phase1_started": 0,
    "phase1_moving": 1,
    "phase1_completed": 2,
    "review_comparison_pending": 3,
    "review_record_committed": 4,
    "calibration_index_committed": 5,
    "automatic_handoff": 6,
    "phase2_archiving": 7,
    "phase2_completed": 8,
    "phase3_finalization_planned": 9,
    "phase3_transfer_in_progress": 10,
    "phase3_transferred_to_target": 11,
    "phase3_index_waiting": 12,
    "phase3_item_resolution_pending": 13,
    "phase3_api_metadata_pending": 14,
    "phase3_api_metadata_completed": 15,
}

# Fehler-/Ausnahmezustände erlauben keinen Rücksprung aus Sicherheitsgründen
_EXCEPTION_STATES: frozenset[str] = frozenset({
    "paused", "quarantine", "review_state_invalid",
    "phase3_publish_disabled", "phase3_transfer_failed",
    "phase3_indexing_timeout", "phase3_item_resolution_failed",
    "phase3_api_metadata_partial", "phase3_api_metadata_failed",
    "finalization_state_invalid",
})


def state_path(runtime_dir: str | Path, batch_id: str) -> Path:
    """Gibt den kanonischen Pfad zur State-JSON-Datei eines Batches zurück.

    Alle State-Dateien liegen unter runtime_dir/state/<batch_id>.json.
    Dadurch ist der State unabhängig vom physischen Batch-Verzeichnis.
    """
    return Path(runtime_dir) / "state" / f"{batch_id}.json"


# ---------------------------------------------------------------------------
# Schreiben und Lesen des Batch-State
# ---------------------------------------------------------------------------

def write_state(
    path: str | Path,
    batch_id: str,
    state: str,
    *,
    status: str | None = None,
    pause_reason: str | None = None,
) -> None:
    """Schreibt den Batch-State atomar als JSON-Datei.

    Das state-Feld folgt der Zustandsautomaten-Logik aus 00AP.md Abschnitt 7.
    Optionale Felder: status (z. B. 'paused') und pause_reason.
    Der Schreibvorgang legt das Elternverzeichnis bei Bedarf an.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # Vorwärts-Zustandsvalidierung: Rückwärts-Übergänge nur bei Ausnahmezuständen erlaubt
    if p.exists():
        existing = json.loads(p.read_text(encoding="utf-8"))
        existing_state = existing.get("state", "")
        if (
            existing_state in _STATE_ORDER
            and state in _STATE_ORDER
            and _STATE_ORDER[state] < _STATE_ORDER[existing_state]
        ):
            raise ValueError(
                f"backwards_state_transition:{existing_state}->{state}"
            )
    data: dict[str, Any] = {
        "schema_version": 1,
        "batch_id": batch_id,
        "state": state,
        "status": status,
        "pause_reason": pause_reason,
        "producer_version": VERSION,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_state(path: str | Path) -> dict[str, Any] | None:
    """Liest den Batch-State aus der angegebenen JSON-Datei.

    Gibt None zurück, wenn die Datei nicht existiert. Wirft bei ungültigem
    JSON eine ValueError, damit Aufrufer explizit entscheiden.
    """
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Legacy-Hilfsfunktionen (WorkUnit-Checkpoint-Logik, intern)
# ---------------------------------------------------------------------------

def _state_file_path(batch_path: Path) -> Path:
    """Pfad zur State-JSON-Datei für einen Batch (Legacy-Konvention)."""
    return batch_path.parent / f"{batch_path.name}.state.json"


def _work_unit_state_file_path(unit: WorkUnitPlan) -> Path:
    """Pfad zur State-JSON-Datei für eine WorkUnit."""
    return unit.batch_path / f"work_unit_{unit.unit_id}.state.json"


def write_work_unit_state(
    unit: WorkUnitPlan,
    state: str,
    phase: str = "phase1",
    image_path: str | None = None,
    pending_mutation: dict[str, Any] | None = None,
) -> None:
    """Schreibt WorkUnit-State als Checkpoint nach jedem Bild."""
    state_file = _work_unit_state_file_path(unit)
    data: dict[str, Any] = {
        "unit_id": unit.unit_id,
        "batch_name": unit.batch_path.name,
        "phase": phase,
        "state": state,
        "image_path": image_path,
        "pending_mutation": pending_mutation,
        "metadata": {
            "total_images": len(unit.image_paths),
            "completed_images": (
                unit.image_paths.index(Path(image_path)) + 1
                if image_path and image_path in [str(p) for p in unit.image_paths]
                else 0
            ),
        },
    }
    state_file.write_text(json.dumps(data, indent=2))


def load_work_unit_state(unit: WorkUnitPlan) -> dict[str, Any]:
    """Lädt WorkUnit-State für Resume-Logik."""
    state_file = _work_unit_state_file_path(unit)
    if not state_file.exists():
        return {"state": "new", "phase": None, "image_path": None, "pending_mutation": None}
    return json.loads(state_file.read_text())


def recover_pending_mutation(
    unit: WorkUnitPlan, state: dict[str, Any], config: dict[str, Any]
) -> None:
    """Stellt eine unterbrochene Move-Operation wieder her (Recovery nach Crash)."""
    pending = state.get("pending_mutation")
    if not pending:
        return
    source = Path(pending["source"])
    dest = Path(pending["dest"])
    if source.exists():
        if not dest.parent.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))
        write_work_unit_state(
            unit, "completed",
            image_path=pending.get("image_path"),
            pending_mutation=None,
        )
