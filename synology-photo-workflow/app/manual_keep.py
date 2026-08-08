"""Projekt: Synology Photo Workflow
Datei: app/manual_keep.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Konservative Manual-Keep-Zuordnung für mehrere Kandidaten mit eindeutigem Bestwert, Marge und auditierbarem Used-Move.
SICHERHEIT: Manual Keep bleibt konservativ; keine Datei wird ohne eindeutigen Vergleich verschoben.
"""
from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .safety import sha256

Similarity = Callable[[Path, Path], float | None]


def _rank(source: Path, candidates: list[Path], similarity: Similarity) -> list[tuple[float, Path]]:
    """Bewertet alle Kandidaten, verwirft unbekannte Werte und sortiert reproduzierbar nach Score und Pfad."""
    scores = []
    for candidate in candidates:
        value = similarity(source, candidate)
        if value is not None:
            scores.append((float(value), candidate))
    return sorted(scores, key=lambda item: (-item[0], item[1].as_posix()))


def process_inbox(inbox: str | Path, used: str | Path, candidates: list[Path], similarity: Similarity | None = None, threshold: float = 0.95, margin: float = 0.03) -> list[dict[str, Any]]:
    """Verschiebt nur Dateien mit sicherem globalem Bestmatch; jede andere Datei verbleibt unverändert in inbox."""
    source_dir, used_dir = Path(inbox), Path(used)
    used_dir.mkdir(parents=True, exist_ok=True)
    outcomes: list[dict[str, Any]] = []
    eligible = sorted(path for path in candidates if path.is_file() and not path.is_symlink())
    for source in sorted(path for path in source_dir.iterdir() if path.is_file() and not path.is_symlink()):
        if similarity is None:
            outcomes.append({'file': source.name, 'status': 'unmatched', 'reason': 'manual_keep_adapter_unavailable'})
            continue
        ranking = _rank(source, eligible, similarity)
        if not ranking:
            outcomes.append({'file': source.name, 'status': 'unmatched', 'reason': 'manual_keep_no_comparable_candidate'})
            continue
        best_score, best_candidate = ranking[0]
        second_score = ranking[1][0] if len(ranking) > 1 else None
        unique_enough = second_score is None or best_score - second_score >= margin
        if best_score < threshold or not unique_enough:
            outcomes.append({'file': source.name, 'status': 'unmatched', 'reason': 'manual_keep_ambiguous_or_below_threshold', 'best_score': best_score, 'second_score': second_score})
            continue
        destination = used_dir / source.name
        if destination.exists():
            outcomes.append({'file': source.name, 'status': 'unmatched', 'reason': 'used_destination_exists'})
            continue
        shutil.move(source, destination)
        outcomes.append({'file': source.name, 'status': 'matched', 'source_sha256': sha256(destination), 'candidate_relative_path': best_candidate.as_posix(), 'best_score': best_score, 'second_score': second_score, 'manual_keep': True})
    return outcomes
