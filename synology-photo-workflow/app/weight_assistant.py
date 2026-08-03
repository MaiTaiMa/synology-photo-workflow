"""Projekt: Synology Photo Workflow
Datei: app/weight_assistant.py
Mitentwickler: MaiTai
Erstellt: 2026-08-02
Projektversion: 7.9.0
Funktion: Schlaegt auf Basis vorhandener manueller Keep/Delete-Entscheidungen einer Session
          moegliche Gewichtsanpassungen fuer die Scoring-Formel vor, ohne die Konfiguration
          jemals selbst zu schreiben.
SICHERHEIT: Der Assistent liefert ausschliesslich einen Vorschlag (Diff + Begruendung); die
            Aktivierung erfolgt stets durch einen expliziten, separaten Schreibvorgang.
HINWEIS: Neu, noch nicht an ein CLI-Kommando angebunden (siehe FEATURE_BRANCH_V7_9_0_TODO.md).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WeightSuggestion:
    weight_name: str
    current_value: float
    suggested_value: float
    reason: str
    sample_size: int


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def suggest_weight_adjustments(decisions: list[dict[str, Any]], current_weights: dict[str, float], learning_rate: float = 0.05, minimum_sample_size: int = 20) -> list[WeightSuggestion]:
    if len(decisions) < minimum_sample_size:
        return []
    suggestions: list[WeightSuggestion] = []
    for weight_name, current_value in current_weights.items():
        kept = [d for d in decisions if d.get('kept') and weight_name in d.get('scores', {})]
        deleted = [d for d in decisions if not d.get('kept') and weight_name in d.get('scores', {})]
        if not kept or not deleted:
            continue
        avg_kept = sum(d['scores'][weight_name] for d in kept) / len(kept)
        avg_deleted = sum(d['scores'][weight_name] for d in deleted) / len(deleted)
        separation = avg_kept - avg_deleted
        if abs(separation) < 0.05:
            continue
        direction = 1.0 if separation > 0 else -1.0
        suggested = _clamp(current_value + direction * learning_rate)
        if abs(suggested - current_value) < 1e-6:
            continue
        suggestions.append(WeightSuggestion(
            weight_name, current_value, suggested,
            f'kept_avg={avg_kept:.3f} deleted_avg={avg_deleted:.3f} separation={separation:.3f}',
            len(kept) + len(deleted),
        ))
    return suggestions
