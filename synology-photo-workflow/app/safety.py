"""Safety: Validierungen, SafetyError."""

from .work_units import WorkUnitPlan
from pathlib import Path
from typing import Any


class SafetyError(Exception):
    """Fehler bei Safety-Validierung."""
    pass


def validate_move_safe(source: Path, dest: Path) -> None:
    """Validiere, dass Move-Operation sicher ist.
    
    T1: Validierung vor jedem Move.
    """
    if not source.exists():
        raise SafetyError(f"Source does not exist: {source}")
    if source == dest:
        raise SafetyError(f"Source and dest are identical: {source}")
    if not dest.parent.exists():
        raise SafetyError(f"Destination parent does not exist: {dest.parent}")


def validate_work_unit_images(unit: WorkUnitPlan, config: dict[str, Any]) -> None:
    """Validiere alle Images einer WorkUnit vor Verarbeitung.
    
    Paket 3: Safety-Validierung fuer WorkUnit-Images.
    - Alle Image-Pfade muessen existieren
    - Alle Images muessen im Batch-Verzeichnis sein
    - Keine symlinks oder spezielle Dateien
    """
    for image_path in unit.image_paths:
        # Existenz-Check
        if not image_path.exists():
            raise SafetyError(f"WorkUnit image does not exist: {image_path}")
        
        # Kein Symlink
        if image_path.is_symlink():
            raise SafetyError(f"WorkUnit image is a symlink: {image_path}")
        
        # Regulare Datei
        if not image_path.is_file():
            raise SafetyError(f"WorkUnit image is not a regular file: {image_path}")
        
        # Im Batch-Verzeichnis
        try:
            image_path.relative_to(unit.batch_path)
        except ValueError:
            raise SafetyError(f"WorkUnit image is outside batch directory: {image_path}")
        
        # Move-Validierung (Vorbereitung)
        temp_images = Path(config["paths"]["temp_images"])
        validate_move_safe(image_path, temp_images / image_path.name)
