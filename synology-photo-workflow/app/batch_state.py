"""Batch/WorkUnit-State: JSON-State-Machine, Checkpoints, Recovery."""

from .work_units import WorkUnitPlan
from pathlib import Path
import json
from typing import Any


def _state_file_path(batch_path: Path) -> Path:
    """Pfad zur State-JSON-Datei fuer einen Batch."""
    return batch_path.parent / f"{batch_path.name}.state.json"


def _work_unit_state_file_path(unit: WorkUnitPlan) -> Path:
    """Pfad zur State-JSON-Datei fuer eine WorkUnit."""
    # WorkUnit-State wird im Batch-Verzeichnis gespeichert
    return unit.batch_path / f"work_unit_{unit.unit_id}.state.json"


def write_state(batch_path: Path, phase: str, state: str, metadata: dict[str, Any] | None = None) -> None:
    """Schreibe Batch-State in JSON-Datei."""
    state_file = _state_file_path(batch_path)
    data = {
        "batch_name": batch_path.name,
        "phase": phase,
        "state": state,
        "metadata": metadata or {}
    }
    state_file.write_text(json.dumps(data, indent=2))


def load_state(batch_path: Path) -> dict[str, Any]:
    """Lade Batch-State aus JSON-Datei."""
    state_file = _state_file_path(batch_path)
    if not state_file.exists():
        return {"state": "new", "phase": None, "metadata": {}}
    return json.loads(state_file.read_text())


def write_work_unit_state(
    unit: WorkUnitPlan,
    state: str,
    phase: str = "phase1",
    image_path: str | None = None,
    pending_mutation: dict[str, Any] | None = None,
) -> None:
    """Schreibe WorkUnit-State in JSON-Datei.
    
    Paket 2: Checkpoint nach jedem Bild/Operation.
    """
    state_file = _work_unit_state_file_path(unit)
    data = {
        "unit_id": unit.unit_id,
        "batch_name": unit.batch_path.name,
        "phase": phase,
        "state": state,
        "image_path": image_path,
        "pending_mutation": pending_mutation,
        "metadata": {
            "total_images": len(unit.image_paths),
            "completed_images": unit.image_paths.index(Path(image_path)) + 1 if image_path and image_path in [str(p) for p in unit.image_paths] else 0
        }
    }
    state_file.write_text(json.dumps(data, indent=2))


def load_work_unit_state(unit: WorkUnitPlan) -> dict[str, Any]:
    """Lade WorkUnit-State aus JSON-Datei fuer Resume.
    
    Paket 2: Resume-Logik - lade letzten Checkpoint.
    """
    state_file = _work_unit_state_file_path(unit)
    if not state_file.exists():
        return {"state": "new", "phase": None, "image_path": None, "pending_mutation": None}
    return json.loads(state_file.read_text())


def recover_pending_mutation(unit: WorkUnitPlan, state: dict[str, Any], config: dict[str, Any]) -> None:
    """Stelle pending_mutation wieder her (Recovery nach Crash).
    
    Paket 2: Recovery-Logik - fuehre unterbrochene Operation nach.
    """
    # TODO: Tatsaechliche Recovery-Implementierung
    # - Image an Zielort verschieben (falls pending_mutation ein Move war)
    # - State auf "completed" setzen
    pass
