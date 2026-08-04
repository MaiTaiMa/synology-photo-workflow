"""app/planning.py — Phase-Planning, Batch-Sortierung.

Spezifikation v10.2 - AP3
"""
from __future__ import annotations
from pathlib import Path
from typing import Any


def plan_phase1(
    config: dict[str, Any],
    folder: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Plant Phase-1-Batches (Stub)."""
    paths = config.get("paths", {})
    temp_sd = Path(paths.get("temp_sd", "TEMP_SD"))
    
    batches: list[dict[str, Any]] = []
    for camera_dir in temp_sd.iterdir():
        if camera_dir.is_dir():
            batches.append({
                "batch_id": camera_dir.name,
                "path": str(camera_dir),
                "status": "ready",
            })
    
    return batches


def plan_phase2(
    config: dict[str, Any],
    folder: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Plant Phase-2-Batches (Stub)."""
    return []
