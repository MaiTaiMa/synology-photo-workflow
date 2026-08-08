"""
Skript: app/planning.py
Zweck: Batch-Planung plan_phase1/plan_phase2 (lesend) und WorkUnit-Selektion.
Autor: MaiTai
Erstellt: 2026-07-30
Version: 7.9.0
Requires: pathlib

Änderungsprotokoll:
  2026-08-08 | 7.9.0 | 00AP: plan_phase1, plan_phase2 ergänzt.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .work_units import WorkUnitPlan, select_next_work_units


def plan_phase1(config: dict[str, Any], folder: str | None = None) -> list[dict[str, Any]]:
    """Liest alle Batch-Verzeichnisse aus temp_sd und gibt einen Plan zurück.

    Strikt lesend: keine Mutation, keine Steuerdateien werden angelegt.
    Gibt eine Liste von {'batch_id': …, 'path': …, 'status': 'ready'} zurück.
    """
    sd_dir = Path(config["paths"]["temp_sd"])
    result = []
    if not sd_dir.is_dir():
        return result
    limit = config.get("workflow", {}).get("batch_limit", 999)
    for batch in sorted(sd_dir.iterdir()):
        if not batch.is_dir() or batch.is_symlink():
            continue
        result.append({"batch_id": batch.name, "path": str(batch), "status": "ready"})
        if len(result) >= limit:
            break
    return result


def plan_phase2(config: dict[str, Any], folder: str | None = None) -> list[dict[str, Any]]:
    """Liest alle Batch-Verzeichnisse aus temp_images für Phase 2.

    Strikt lesend; gibt {'batch_id': …, 'path': …, 'status': 'ready'} zurück.
    """
    images_dir = Path(config["paths"]["temp_images"])
    result = []
    if not images_dir.is_dir():
        return result
    limit = config.get("workflow", {}).get("batch_limit", 999)
    for batch in sorted(images_dir.iterdir()):
        if not batch.is_dir() or batch.is_symlink():
            continue
        result.append({"batch_id": batch.name, "path": str(batch), "status": "ready"})
        if len(result) >= limit:
            break
    return result


def select_next_batches(
    config: dict[str, Any], phase: str
) -> list[WorkUnitPlan | Path]:
    """Wählt nächste Batches/WorkUnits gemäß Konfiguration (Legacy-Wrapper)."""
    return select_next_work_units(config, phase)


def process_physical_batch_or_work_unit(
    batch_or_unit: Path | WorkUnitPlan, config: dict[str, Any]
) -> None:
    """Verarbeitet physischen Batch (Legacy-Wrapper, WorkUnits werden nicht unterstützt)."""
    from .runtime import process_physical_batch
    from .work_units import WorkUnitPlan as WUP
    if isinstance(batch_or_unit, WUP):
        # WorkUnit-Verarbeitung wird in einem späteren AP implementiert
        raise NotImplementedError("WorkUnit-Verarbeitung ist noch nicht implementiert")
    else:
        process_physical_batch(batch_or_unit, config)
