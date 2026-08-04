"""app/metadata.py — Metadata-Tags, build_tags.

Spezifikation v10.2 - AP7
"""
from __future__ import annotations
from typing import Any


def build_tags(decision_data: dict[str, Any]) -> dict[str, list[str]]:
    """Erstellt Tags aus Decision-Daten (keine 'person-unknown' Tags)."""
    tags: dict[str, list[str]] = {"keywords": []}
    
    if decision_data.get("predicted_decision") == "keep":
        tags["keywords"].append("kept")
    
    rating = decision_data.get("star_rating")
    if rating:
        tags["keywords"].append(f"rating-{rating}")
    
    person = decision_data.get("person_slug")
    if person and person != "unknown":
        tags["keywords"].append(f"person-{person}")
    
    return tags
