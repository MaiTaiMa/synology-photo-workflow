"""
Skript: app/reporting.py
Zweck: Run-Summary, User-Actions und Logging-Hilfsfunktionen.
Autor: MaiTai
Erstellt: 2026-07-30
Version: 7.9.0
Requires: json, pathlib, datetime

Änderungsprotokoll:
  2026-08-08 | 7.9.0 | 00AP: action, summary ergänzt.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import VERSION
from .result_contract import atomic_json_write


def action(
    severity: str,
    scope: str,
    description: str,
    reference: str,
) -> dict[str, Any]:
    """Erzeugt einen User-Action-Eintrag für die Run-Summary.

    Severity-Werte: 'blocking', 'warning', 'info'.
    scope beschreibt den betroffenen Bereich (z. B. 'batch:a').
    """
    return {
        "severity": severity,
        "scope": scope,
        "description": description,
        "reference": reference,
    }


def summary(
    workflow_data: str | Path,
    status: str,
    config_fingerprint: str,
    config: dict[str, Any],
    user_actions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Erzeugt und schreibt die Run-Summary atomar.

    requested_automation_mode ist immer 'assisted_review', weil automatische
    Modi nur nach expliziter Konfigurationsfreigabe aktiviert werden dürfen.
    Dies sichert den Sicherheits-vor-Nutzen-Grundsatz.
    """
    result: dict[str, Any] = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "status": status,
        "config_fingerprint": config_fingerprint,
        # Automatik wird niemals selbst eingeschaltet (Sicherheit vor Nutzen)
        "requested_automation_mode": config.get("automation", {}).get(
            "mode", "assisted_review"
        ),
        "user_actions_required": user_actions,
    }
    summary_dir = Path(workflow_data) / "runtime" / "reports"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / "run_summary.json"
    atomic_json_write(str(summary_path), result)
    return result


def write_run_summary(
    workflow_data: Path, run_id: str, results: list[dict[str, Any]]
) -> dict[str, Any]:
    """Schreibt Run-Summary atomar (Legacy-Variante mit run_id)."""
    data: dict[str, Any] = {
        "schema_version": 1,
        "producer_version": VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "run_id": run_id,
        "results": results,
    }
    summary_path = workflow_data / "runtime" / "reports" / f"{run_id}.summary.json"
    atomic_json_write(str(summary_path), data)
    return data
