"""Runtime: Batch/WorkUnit-Verarbeitung, Checkpoints, Recovery."""

from .safety import SafetyError, validate_move_safe, validate_work_unit_images
from .batch_state import write_state, load_state, write_work_unit_state, load_work_unit_state, recover_pending_mutation
from .work_units import WorkUnitPlan
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
    """Verarbeite WorkUnit mit Checkpoint-Logik und tatsaechlicher Bildverarbeitung.
    
    Paket 1:
    - load_work_unit_state() fuer Resume
    - recover_pending_mutation() fuer Recovery
    - write_work_unit_state() nach jedem Bild/Checkpoint
    
    Paket 3:
    - validate_work_unit_images() VOR Verarbeitung
    
    Paket 4:
    - validate_move_safe() pro Bild
    - shutil.move() pro Bild
    - pending_mutation fuer atomare Checkpoints
    """
    # Paket 3: Safety-Validierung VOR Verarbeitung
    validate_work_unit_images(unit, config)
    
    # Resume: Lade bestehenden State
    state = load_work_unit_state(unit)
    
    # Recovery: Falls pending_mutation, erst wiederherstellen
    if state.get("pending_mutation"):
        recover_pending_mutation(unit, state, config)
    
    # Verarbeite Bilder mit Checkpoints
    temp_images = Path(config["paths"]["temp_images"])
    for image_path in unit.image_paths:
        target_path = temp_images / image_path.name
        
        # Checkpoint VOR Operation mit pending_mutation
        write_work_unit_state(
            unit, "processing",
            image_path=str(image_path),
            pending_mutation={"source": str(image_path), "dest": str(target_path)}
        )
        
        # Paket 4: Tatsaechliche Bildverarbeitung
        validate_move_safe(image_path, target_path)
        shutil.move(str(image_path), str(target_path))
        
        # Checkpoint NACH Operation (pending_mutation entfernt)
        write_work_unit_state(
            unit, "completed",
            image_path=str(image_path),
            pending_mutation=None
        )
    
    # WorkUnit abgeschlossen
    write_work_unit_state(unit, "completed")
