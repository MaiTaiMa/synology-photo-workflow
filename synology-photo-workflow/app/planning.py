"""Planning: Batch/WorkUnit-Auswahl, Resume-Prioritaet."""

from . import VERSION
from .work_units import select_next_work_units, WorkUnitPlan
from .runtime import process_work_unit, process_physical_batch
from pathlib import Path
from typing import Any


def select_next_batches(config: dict[str, Any], phase: str) -> list[WorkUnitPlan]:
    """Waehle naechste Batches/WorkUnits gem. Konfiguration.
    
    Prioritaet (B5):
    1. recovery_required
    2. paused_runtime, paused_budget, in_progress (Resume-Prioritaet)
    3. Neue physische Batches, sortiert nach batch_sort (oldest_first | newest_first)
    
    Paket 1: Delegiert an work_units.py select_next_work_units()
    """
    return select_next_work_units(config, phase)


def process_physical_batch_or_work_unit(batch_or_unit: Path | WorkUnitPlan, config: dict[str, Any]) -> None:
    """Verarbeite physischen Batch oder WorkUnit.
    
    Paket 1: WorkUnit-Checkpoints, Resume-Logik
    """
    if isinstance(batch_or_unit, WorkUnitPlan):
        process_work_unit(batch_or_unit, config)
    else:
        process_physical_batch(batch_or_unit, config)
