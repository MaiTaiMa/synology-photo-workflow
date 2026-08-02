"""Phasen: Phase 1 (Move), Phase 2 (Review)."""

from .result_contract import FileManifest
from .runtime import quarantine_batch, process_physical_batch
from .safety import SafetyError
from .batch_state import write_state
from pathlib import Path
import shutil
from typing import Any


def process_phase1(batches: list[Path], config: dict[str, Any]) -> list[dict[str, Any]]:
    """Verarbeite Phase 1 für alle Batches.
    
    T1: Jeder Batch ist mit try/except SafetyError isoliert.
    T2: phase1_moving wird VOR shutil.move geschrieben, phase1_completed NACH Move.
    """
    results: list[dict[str, Any]] = []
    
    for batch_path in batches:
        # T1: Quarantne-Anbindung mit try/except
        try:
            # Phase-1-Verarbeitung
            manifest = process_physical_batch(batch_path, config)
            
            # T2: phase1_moving VOR shutil.move
            write_state(batch_path, "phase1", "phase1_moving")
            
            # Batch nach temp_images bewegen
            target_path = Path(config["paths"]["temp_images"]) / batch_path.name
            shutil.move(str(batch_path), str(target_path))
            
            # T2: phase1_completed NACH erfolgreichem Move
            write_state(batch_path, "phase1", "phase1_completed")
            
            results.append({"batch_id": batch_path.name, "status": "completed", "manifest": manifest})
            
        except SafetyError as error:
            # T1: Quarantne bei SafetyError
            quarantine_batch(
                batch_path,
                config["paths"]["basedir"],
                config["paths"]["temp_error"],
                str(error),
            )
            results.append({"batch_id": batch_path.name, "status": "quarantined", "reason": str(error)})
            continue
    
    return results


def process_phase2(batches: list[Path], config: dict[str, Any]) -> list[dict[str, Any]]:
    """Verarbeite Phase 2 (Review) für alle Batches."""
    results: list[dict[str, Any]] = []
    
    for batch_path in batches:
        # TODO: Phase-2-Implementierung
        results.append({"batch_id": batch_path.name, "status": "completed"})
    
    return results
