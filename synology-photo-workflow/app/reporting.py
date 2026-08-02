"""Reporting: Run-Summary."""

from .result_contract import atomic_json_write
from . import VERSION
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


def write_run_summary(workflow_data: Path, run_id: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    """Schreibe Run-Summary atomar."""
    data = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "results": results,
    }
    summary_path = workflow_data / "runtime" / "reports" / f"{run_id}.summary.json"
    atomic_json_write(str(summary_path), data)
    return data
