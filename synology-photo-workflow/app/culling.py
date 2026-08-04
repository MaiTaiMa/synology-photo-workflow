"""app/culling.py — Score-Berechnung, Series-Fields, Metadata-Tags.

Spezifikation v10.2 - AP6
"""
from __future__ import annotations
from typing import Any


def final_score(
    partial: dict[str, Any],
    weights: dict[str, float],
) -> float:
    """Berechnet final_score aus base_score + eye_score (renormiert bei None)."""
    base = partial.get("base_score")
    eye = partial.get("eye_score")
    
    if base is not None and eye is None:
        return base  # Renormierung: nur base_score
    
    if base is None or eye is None:
        return 0.0
    
    return base * weights.get("base_score", 0.5) + eye * weights.get("eye_score", 0.5)


def stars(score: float | None, bands: list[dict[str, Any]]) -> int | None:
    """Bestimmt Star-Rating aus Score und Bands."""
    if score is None:
        return None
    for band in bands:
        if band["min"] <= score <= band["max"]:
            return band["rating"]
    return None


def apply_series(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fuegt series_rank, series_best, series_size hinzu."""
    # Vereinfacht: alle als eine Serie
    sorted_recs = sorted(records, key=lambda r: r.get("final_score", 0), reverse=True)
    for i, rec in enumerate(sorted_recs):
        rec["series_rank"] = i + 1
        rec["series_best"] = (i == 0)
        rec["series_size"] = len(sorted_recs)
    return sorted_recs
