"""WorkUnits: KI-Contract, Batch-Chunking, State, Resume, Recovery."""

from .batch_state import load_state, load_work_unit_state
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


def _get_image_files(batch_path: Path) -> list[Path]:
    """Hole alle Image-Dateien aus einem Batch-Verzeichnis."""
    extensions = {".jpg", ".jpeg", ".png", ".gif", ".heic", ".heif", ".tiff", ".tif", ".webp"}
    return sorted([f for f in batch_path.iterdir() if f.is_file() and f.suffix.lower() in extensions])


def _chunk_into_work_units(batch_path: Path, work_unit_size: int) -> list[WorkUnitPlan]:
    """Chunking: Teile Batch-Images in WorkUnits der Groesse work_unit_size."""
    images = _get_image_files(batch_path)
    units = []
    for i in range(0, len(images), work_unit_size):
        chunk = images[i:i + work_unit_size]
        units.append(WorkUnitPlan(
            unit_id=f"{batch_path.name}_unit_{i // work_unit_size}",
            batch_path=batch_path,
            image_paths=chunk
        ))
    return units


def _get_batch_state(batch_path: Path) -> str:
    """Lade Batch-State fuer Priorisierung."""
    state = load_state(batch_path)
    return state.get("state", "new")


def _has_pending_work_units(batch_path: Path) -> bool:
    """Pruefe, ob Batch noch unverarbeitete WorkUnits hat."""
    # TODO: Vollstaendige Implementierung mit WorkUnit-State-Tracking
    return False


def select_next_work_units(config: dict[str, Any], phase: str) -> list[WorkUnitPlan]:
    """Waehle naechste WorkUnits gem. Konfiguration.
    
    Prioritaet (B5):
    1. recovery_required (pending_mutation in WorkUnit-State)
    2. paused_runtime, paused_budget, in_progress (Resume-Prioritaet)
    3. Neue physische Batches, sortiert nach batch_sort
    
    Paket 5: Vollstaendige Implementierung mit Batch-Chunking.
    """
    batches_pending = Path(config["paths"]["batches_pending"])
    batch_sort: BatchSort = config.get("batch_sort", "oldest_first")
    work_unit_size = config.get("work_unit_size", 100)
    
    if not batches_pending.exists():
        return []
    
    # Alle Batches sammeln
    batches = [b for b in batches_pending.iterdir() if b.is_dir()]
    
    # B5 Prioritaet 1: Recovery (pending_mutation)
    recovery_units: list[WorkUnitPlan] = []
    for batch in batches:
        state = _get_batch_state(batch)
        if state == "recovery_required":
            recovery_units.extend(_chunk_into_work_units(batch, work_unit_size))
    if recovery_units:
        return recovery_units
    
    # B5 Prioritaet 2: Resume (paused, in_progress)
    resume_units: list[WorkUnitPlan] = []
    for batch in batches:
        state = _get_batch_state(batch)
        if state in {"paused_runtime", "paused_budget", "in_progress"}:
            resume_units.extend(_chunk_into_work_units(batch, work_unit_size))
    if resume_units:
        return resume_units
    
    # B5 Prioritaet 3: Neue Batches sortieren
    if batch_sort == "oldest_first":
        batches.sort(key=lambda b: b.stat().st_mtime)
    else:  # newest_first
        batches.sort(key=lambda b: b.stat().st_mtime, reverse=True)
    
    # Erste Batch in WorkUnits chunken
    if batches:
        return _chunk_into_work_units(batches[0], work_unit_size)
    
    return []
