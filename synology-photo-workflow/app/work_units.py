"""WorkUnits: KI-Contract, Batch-Chunking, State, Resume, Recovery."""

from .batch_state import write_work_unit_state, load_work_unit_state, recover_pending_mutation
from pathlib import Path
from typing import Any, Literal


BatchSort = Literal["oldest_first", "newest_first"]


class WorkUnitPlan:
    """WorkUnit-Plan: Subset von Images aus einem Batch.
    
    Paket 1: WorkUnit-Struktur fuer AI-Contract.
    """
    def __init__(
        self,
        unit_id: str,
        batch_path: Path,
        image_paths: list[Path],
    ):
        self.unit_id = unit_id
        self.batch_path = batch_path
        self.image_paths = image_paths


def select_next_work_units(config: dict[str, Any], phase: str) -> list[WorkUnitPlan]:
    """Waehle naechste WorkUnits gem. Konfiguration.
    
    Prioritaet (B5):
    1. recovery_required
    2. paused_runtime, paused_budget, in_progress (Resume-Prioritaet)
    3. Neue physische Batches, sortiert nach batch_sort
    
    Paket 1: WorkUnit-Chunking gem. work_unit_size.
    """
    # TODO: Vollstaendige Implementierung
    # - Lade Batches aus batches_pending/
    # - Sortiere gem. batch_sort
    # - Chunking in WorkUnits gem. work_unit_size
    return []
