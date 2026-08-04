"""app/family_recognition.py — Family-Face-Matching, Selection-Fingerprint.

Spezifikation v10.2 - AP7
"""
from __future__ import annotations
import hashlib
from typing import Any


def selection_fingerprint(selection: dict[str, Any], person_slug: str) -> str:
    """Berechnet Fingerprint aus aktiven Referenz-Hashes."""
    h = hashlib.sha256()
    for f in selection.get("files", []):
        if f.get("status") == "active" and "reference/" in f.get("relative_path", ""):
            h.update(f.get("sha256", "").encode())
    h.update(person_slug.encode())
    return h.hexdigest()[:12]


def forbidden_unknown_artifact(face_result: dict[str, Any]) -> bool:
    """Prueft ob unbekanntes Face-Match (darf nie Candidate werden)."""
    return face_result.get("status") == "unmatched" and face_result.get("person_slug") == "unknown"


def candidate_allowed(
    status: str,
    decision: str,
    score: float,
    is_family: bool,
) -> bool:
    """Prueft ob Match als Candidate erlaubt ist."""
    if status == "unmatched":
        return False
    return True
