"""Phasen: Phase 1 (Move), Phase 2 (Review)."""

from .result_contract import FileManifest
from .runtime import quarantine_batch, process_physical_batch
from .planning import select_next_batches, process_physical_batch_or_work_unit
from .safety import SafetyError
from .batch_state import write_state
from pathlib import Path
import shutil
from typing import Any


def run_phase1(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Fuehre Phase 1 fuer alle geplanten Batches/WorkUnits aus.
    
    Paket 1: Verwendet select_next_batches() fuer WorkUnit-Planung.
    T1: Jeder Batch ist mit try/except SafetyError isoliert.
    T2: phase1_moving wird VOR shutil.move geschrieben, phase1_completed NACH Move.
    """
    results: list[dict[str, Any]] = []
    
    # Paket 1: WorkUnit-Planung ueber planning.py
    scheduled = select_next_batches(config, "phase1")
    
    for batch_or_unit in scheduled:
        # T1: Quarantne-Anbindung mit try/except
        try:
            # Paket 1: WorkUnit-Verarbeitung
            process_physical_batch_or_work_unit(batch_or_unit, config)
            
            # T2: phase1_moving VOR shutil.move (fuer physische Batches)
            if isinstance(batch_or_unit, Path):
                write_state(batch_or_unit, "phase1", "phase1_moving")
                target_path = Path(config["paths"]["temp_images"]) / batch_or_unit.name
                shutil.move(str(batch_or_unit), str(target_path))
                write_state(batch_or_unit, "phase1", "phase1_completed")
            
            results.append({"batch_id": str(batch_or_unit), "status": "completed"})
            
        except SafetyError as error:
            # T1: Quarantne bei SafetyError
            batch_path = batch_or_unit if isinstance(batch_or_unit, Path) else batch_or_unit.batch_path
            quarantine_batch(
                batch_path,
                config["paths"]["basedir"],
                config["paths"]["temp_error"],
                str(error),
            )
            results.append({"batch_id": str(batch_or_unit), "status": "quarantined", "reason": str(error)})
            continue
    
    return results


def run_phase2(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Fuehre Phase 2 (Review) fuer alle geplanten Batches/WorkUnits aus."""
    results: list[dict[str, Any]] = []
    
    # Paket 1: WorkUnit-Planung ueber planning.py
    scheduled = select_next_batches(config, "phase2")
    
    for batch_or_unit in scheduled:
        # TODO: Phase-2-Implementierung mit WorkUnit-State
        results.append({"batch_id": str(batch_or_unit), "status": "completed"})
    
    return results
