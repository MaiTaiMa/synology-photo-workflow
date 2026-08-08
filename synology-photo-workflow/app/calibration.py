"""
Skript: app/calibration.py
Zweck: Kalibrierungsindex rebuild, Readiness-Report und Kalibrierungsgewichte.
Autor: MaiTai
Erstellt: 2026-07-30
Version: 7.9.0
Requires: json, pathlib, datetime

Änderungsprotokoll:
  2026-08-08 | 7.9.0 | 00AP: rebuild-Funktion ergänzt.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import VERSION
from .result_contract import atomic_json_write


def rebuild(basedir: str | Path, output_path: str | Path) -> dict[str, Any]:
    """Liest alle review_decision_record.json aus Unterverzeichnissen und
    baut einen Kalibrierungsindex mit dem aktiven Config-Fingerprint auf.

    Strategie: Der aktive Fingerprint ist der Fingerprint des zeitlich
    neuesten Records (höchstes created_at). Nur Records mit diesem
    Fingerprint fließen in den Index ein. So werden keine Fingerprints
    gemischt, was die Kalibrierungsqualität sicherstellt.
    Gibt {'active_config_fingerprint': str, 'record_count': int} zurück.
    """
    basedir = Path(basedir)
    records = []
    # Alle review_decision_record.json in unmittelbaren Unterverzeichnissen lesen
    for sub in sorted(basedir.iterdir()):
        record_file = sub / "review_decision_record.json"
        if sub.is_dir() and record_file.exists():
            try:
                data = json.loads(record_file.read_text(encoding="utf-8"))
                records.append(data)
            except Exception:
                continue
    if not records:
        result: dict[str, Any] = {
            "active_config_fingerprint": None,
            "record_count": 0,
        }
        atomic_json_write(output_path, result)
        return result
    # Neuesten Record nach created_at bestimmen
    latest = max(records, key=lambda r: r.get("created_at", ""))
    active_fingerprint = latest.get("config_fingerprint")
    # Nur Records mit dem aktiven Fingerprint behalten
    active_records = [
        r for r in records if r.get("config_fingerprint") == active_fingerprint
    ]
    result = {
        "active_config_fingerprint": active_fingerprint,
        "record_count": len(active_records),
        "records": active_records,
    }
    atomic_json_write(output_path, result)
    return result


def record(weights: dict[str, float], workflow_data: Path) -> dict[str, Any]:
    """Schreibt Kalibrierungsgewichte-Record atomar."""
    data: dict[str, Any] = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "weights": weights,
    }
    record_path = workflow_data / "runtime" / "calibration" / "weights.json"
    atomic_json_write(str(record_path), data)
    return data


def write_readiness_report(
    workflow_data: Path, ready: bool, reason: str
) -> dict[str, Any]:
    """Schreibt Readiness-Report atomar."""
    data: dict[str, Any] = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "ready": ready,
        "reason": reason,
    }
    report_path = workflow_data / "runtime" / "calibration" / "readiness.json"
    atomic_json_write(str(report_path), data)
    return data
