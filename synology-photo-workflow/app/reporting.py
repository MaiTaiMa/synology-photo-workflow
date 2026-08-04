"""app/reporting.py — Action, Summary fuer Run-Reports.

Spezifikation v10.2 - AP5
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from .safety import atomic_json, utcnow


def action(
    severity: str,
    scope: str,
    description: str,
    doc_link: str,
) -> dict[str, Any]:
    """Erstellt User-Action-Eintrag."""
    return {
        "severity": severity,
        "scope": scope,
        "description": description,
        "doc_link": doc_link,
    }


def summary(
    workflow_data: Path | str,
    status: str,
    fingerprint: str,
    config: dict[str, Any],
    actions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Erstellt Run-Summary."""
    from . import VERSION
    now = utcnow()
    return {
        "schema_version": 1,
        "created_at": now,
        "updated_at": now,
        "producer_version": VERSION,
        "status": status,
        "config_fingerprint": fingerprint,
        "requested_automation_mode": config.get("automation", {}).get("mode", "assisted_review"),
        "user_actions_required": actions,
    }
