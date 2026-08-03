"""Kalibrierung: Gewichte, Readiness."""

from .result_contract import atomic_json_write
from . import VERSION
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


def record(weights: dict[str, float], workflow_data: Path) -> dict[str, Any]:
    """Schreibe Kalibrierungs-Record atomar."""
    data = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "weights": weights,
    }
    record_path = workflow_data / "runtime" / "calibration" / "weights.json"
    atomic_json_write(str(record_path), data)
    return data


def write_readiness_report(workflow_data: Path, ready: bool, reason: str) -> dict[str, Any]:
    """Schreibe Readiness-Report atomar."""
    data = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ready": ready,
        "reason": reason,
    }
    report_path = workflow_data / "runtime" / "calibration" / "readiness.json"
    atomic_json_write(str(report_path), data)
    return data
