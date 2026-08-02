"""Runtime: Batch/WorkUnit-Verarbeitung, Checkpoints, Recovery."""

from .safety import SafetyError, validate_move_safe
from .batch_state import write_state, load_state
from .work_units import WorkUnitPlan, load_work_unit_state, write_work_unit_state, recover_pending_mutation
from pathlib import Path
import shutil
from typing import Any


def quarantine_batch(batch_path: Path, basedir: Path, quarantine_dir: Path, reason: str) -> None:
    """Verschiebe einen Batch in die Quarantaene."""
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    target = quarantine_dir / batch_path.name
    if target.exists():
        target = quarantine_dir / f"{batch_path.name}_{reason[:20]}"
    shutil.move(str(batch_path), str(target))


def process_physical_batch(batch_path: Path, config: dict[str, Any]) -> None:
    """Verarbeite physischen Batch mit State-Machine."""
    # T2: State-Machine wird vor/nach Operationen geschrieben
    write_state(batch_path, "phase1", "phase1_moving")
    target_path = Path(config["paths"]["temp_images"]) / batch_path.name
    shutil.move(str(batch_path), str(target_path))
    write_state(batch_path, "phase1", "phase1_completed")


def process_work_unit(unit: WorkUnitPlan, config: dict[str, Any]) -> None:
    """Verarbeite WorkUnit mit Checkpoint-Logik.
    
    Paket 1:
    - load_work_unit_state() fuer Resume
    - recover_pending_mutation() fuer Recovery
    - write_work_unit_state() nach jedem Bild/Checkpoint
    """
    # Resume: Lade bestehenden State
    state = load_work_unit_state(unit)
    
    # Recovery: Falls pending_mutation, erst wiederherstellen
    if state.get("pending_mutation"):
        recover_pending_mutation(unit, state, config)
    
    # Verarbeite Bilder mit Checkpoints
    for image_path in unit.image_paths:
        # Checkpoint VOR Operation
        write_work_unit_state(unit, "processing", image_path=str(image_path))
        
        # TODO: Tatsaechliche Bildverarbeitung
        # - validate_move_safe()
        # - shutil.move()
        
        # Checkpoint NACH Operation
        write_work_unit_state(unit, "completed", image_path=str(image_path))
    
    # WorkUnit abgeschlossen
    write_work_unit_state(unit, "completed")
