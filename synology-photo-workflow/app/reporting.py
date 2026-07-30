"""Projekt: Synology Photo Workflow
Datei: app/reporting.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Strukturierte JSON-Run-Summaries mit normierten Resultatzählern, Statusaggregaten und priorisierten Nutzeraktionen.
SICHERHEIT: Der Referenzcache speichert keine Roh-Embeddings und aktiviert keine Person ohne explizite Referenzauswahl.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Any
from .safety import atomic_json, utcnow


def action(severity: str, scope: str, message: str, manual_anchor: str | None = None) -> dict[str, str | None]:
    """Erzeugt eine validierbare, priorisierbare Handlungsaufforderung für Menschen."""
    if severity not in {'info', 'warning', 'blocking'}:
        raise ValueError('invalid_action_severity')
    return {'severity': severity, 'scope': scope, 'message': message, 'manual_anchor': manual_anchor}


def aggregate(result: dict[str, Any]) -> dict[str, int]:
    """Leitet reproduzierbare Basiszähler aus Phase-Resultaten ab, ohne fehlende Werte zu erfinden."""
    groups = [result.get('phase1', []), result.get('phase2', [])] if ('phase1' in result or 'phase2' in result) else [result.get('batches', result if isinstance(result, list) else [])]
    batches = [item for group in groups for item in group if isinstance(item, dict)]
    counts = {'found_batches': len(batches), 'processed_batches': 0, 'skipped_batches': 0, 'failed_batches': 0, 'keep': 0, 'review': 0, 'reject': 0}
    for batch in batches:
        if batch.get('status') in {'blocked', 'failed'}: counts['failed_batches'] += 1
        else: counts['processed_batches'] += 1
        for key in ('keep', 'review', 'reject'):
            counts[key] += int(batch.get('decision_counts', {}).get(key, 0))
    return counts


def summary(runtime: str | Path, status: str, config_fingerprint: str, result: dict[str, Any], actions: list[dict[str, Any]] | None = None, requested_mode: str = 'assisted_review', effective_mode: str = 'assisted_review', calibration_status: dict[str, Any] | None = None) -> dict[str, Any]:
    """Persistiert vollständige Summary; stdout zeigt bewusst nur warning/blocking Aktionen."""
    run_id, now = str(uuid.uuid4()), utcnow()
    all_actions = actions or []
    data = {'schema_version': 1, 'run_id': run_id, 'created_at': now, 'updated_at': now, 'producer_version': '7.7.0', 'status': status, 'config_fingerprint': config_fingerprint, 'requested_automation_mode': requested_mode, 'effective_automation_mode': effective_mode, 'result': result, 'counters': aggregate(result), 'metadata_status': result.get('metadata_status', 'not_run'), 'cache_status': result.get('cache_status', 'not_run'), 'zip_conflicts': result.get('zip_conflicts', []), 'calibration_status': calibration_status or {'status': 'not_available'}, 'user_actions_required': all_actions}
    atomic_json(Path(runtime) / 'run_summaries' / f'{run_id}.json', data, 'run_id')
    for item in all_actions:
        if item['severity'] in {'warning', 'blocking'}:
            print(f"{item['severity'].upper()}: {item['scope']}: {item['message']}", file=sys.stdout)
    return data
