"""app/calibration.py — Calibration-Reports, Fingerprint-Tracking.

Spezifikation v10.2 - AP5
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from .safety import atomic_json, utcnow


def rebuild(
    batches_dir: Path | str,
    summary_path: Path | str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Liest alle review_decision_record.json und schreibt summary.json.

    active_config_fingerprint = Fingerprint des neuesten Records.
    record_count = Anzahl Records MIT aktivem Fingerprint.
    """
    base = Path(batches_dir)
    records: list[tuple[str, int, dict[str, Any]]] = []

    for record_file in base.rglob("review_decision_record.json"):
        try:
            data = json.loads(record_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "config_fingerprint" in data:
                mtime_ns = record_file.stat().st_mtime_ns
                created_at = data.get("created_at", "")
                records.append((created_at, mtime_ns, data))
        except (json.JSONDecodeError, OSError):
            continue

    active_fingerprint: str | None = None
    if records:
        newest = max(records, key=lambda r: (r[0], r[1]))
        active_fingerprint = newest[2].get("config_fingerprint")

    active_records = [
        r for r in records
        if r[2].get("config_fingerprint") == active_fingerprint
    ]
    record_count = len(active_records)

    records_by_fingerprint: dict[str, int] = {}
    for _, _, d in records:
        fp = d.get("config_fingerprint", "unknown")
        records_by_fingerprint[fp] = records_by_fingerprint.get(fp, 0) + 1

    from . import VERSION
    now = utcnow()
    summary_data: dict[str, Any] = {
        "schema_version": 1,
        "created_at": now,
        "updated_at": now,
        "producer_version": VERSION,
        "built_at": now,
        "active_config_fingerprint": active_fingerprint,
        "record_count": record_count,
        "total_records": len(records),
        "records_by_fingerprint": records_by_fingerprint,
    }

    out = Path(summary_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(out, summary_data, "built_at")

    return summary_data
