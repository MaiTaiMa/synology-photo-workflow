"""Projekt: Synology Photo Workflow
Datei: app/family_recognition.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Bekannte-Personen-Fachlogik ohne ML-Import: aktive Referenzen, Manifestprüfung und sichere Kandidatengrenzen.
SICHERHEIT: Modellwahl ist explizit; keine stillen Backend- oder Metrik-Fallbacks.
"""
from __future__ import annotations

from typing import Any

from .safety import SafetyError, canonical_hash


def active_references(selection: dict[str, Any]) -> list[dict[str, Any]]:
    """Nur explizit aktive Dateien unter reference sind Modellquelle; newfaces/notused nie."""
    return [item for item in selection.get('files', []) if item.get('status') == 'active' and str(item.get('relative_path', '')).startswith('reference/')]


def validate_selection(selection: dict[str, Any], person_slug: str) -> list[dict[str, Any]]:
    """Validiert den minimalen Referenzvertrag vor jedem Backend-Rebuild."""
    if selection.get('person_slug') != person_slug:
        raise SafetyError('selection_person_slug_mismatch')
    refs = active_references(selection)
    for item in refs:
        if not item.get('relative_path') or not item.get('sha256'):
            raise SafetyError('selection_active_reference_incomplete')
    return refs


def selection_fingerprint(selection: dict[str, Any], person_slug: str) -> str:
    """Erzeugt einen datensparsamen Fingerprint der tatsächlich aktiven Modellquelle."""
    refs = validate_selection(selection, person_slug)
    return canonical_hash([(item['relative_path'], item['sha256']) for item in sorted(refs, key=lambda value: value['relative_path'])])


def candidate_allowed(match_status: str, source_final_decision: str, quality: float | None, duplicate: bool) -> bool:
    """Erlaubt einen Face-Crop ausschließlich für sicheren bekannten Match, Keep/Manual-Keep und Nichtduplikat."""
    return match_status == 'matched' and source_final_decision == 'keep' and quality is not None and quality > 0 and not duplicate


def forbidden_unknown_artifact(payload: dict[str, Any]) -> bool:
    """Hilfsprüfung für Tests: Unbekannte Personen dürfen keine Kandidaten-/Referenzartefakte erzeugen."""
    return payload.get('status') in {'unknown', 'unmatched', 'ambiguous', 'noface'} and bool(payload.get('person_slug') or payload.get('crop_path'))
