"""Planning: Batch/WorkUnit-Auswahl, Resume-Prioritaet."""

from . import VERSION
from .work_units import select_next_work_units, WorkUnitPlan
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


def process_physical_batch_or_work_unit(batch_or_unit: Path | WorkUnitPlan, config: dict[str, Any]) -> Any:
    """Verarbeite physischen Batch oder WorkUnit.
    
    Paket 1: WorkUnit-Checkpoints, Resume-Logik
    """
    # TODO: Vollstaendige Implementierung mit WorkUnit-State
    # - load_work_unit_state() fuer Resume
    # - recover_pending_mutation() fuer Recovery
    # - write_work_unit_state() nach jedem Bild/Checkpoint
    return None
