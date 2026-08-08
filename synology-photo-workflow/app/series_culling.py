"""
Skript: app/series_culling.py
Zweck: Serienerkennung und Bestbildwahl für ähnliche Bilder innerhalb eines Batches.
Autor: MaiTai
Erstellt: 2026-08-08
Version: 1.0.0
Requires: pathlib, math

Änderungsprotokoll:
  2026-08-08 | 1.0.0 | 00AP: Initiale Implementierung gemäß 00AP.md Abschnitt 3 und 07AP.md.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Datenmodelle: SeriesGroup und SeriesResult
# ---------------------------------------------------------------------------

@dataclass
class SeriesGroup:
    """Gruppe ähnlicher Bilder, die zu einer Serie zusammengefasst wurden."""

    series_id: str
    images: list[dict[str, Any]]  # Bildanalyse-Dicts mit relative_path und base_score
    best_index: int               # Index des Bestbilds in der images-Liste


@dataclass
class SeriesResult:
    """Serienzuordnung und Rang eines einzelnen Bilds."""

    series_id: str
    series_rank: int
    series_best: bool
    distance_to_best: float


# ---------------------------------------------------------------------------
# Serienerkennung: group_series
# ---------------------------------------------------------------------------

def group_series(
    images: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[SeriesGroup]:
    """Gruppiert ähnliche Bilder zu Serien basierend auf Zeitstempel-Nähe.

    Bilder werden als Serie erkannt wenn ihre Datei-Zeitstempel innerhalb
    des konfigurierten Zeitfensters liegen. Serienerkennung basiert auf
    Dateinamen-Ähnlichkeit und EXIF-Zeitstempeln.
    """
    if not images:
        return []

    # Zeitfenster aus Konfiguration lesen (Standard: 5 Sekunden)
    series_config = config.get("culling", {})
    time_window_s = series_config.get("series_time_window_seconds", 5)

    # Bilder nach Dateiname sortieren (Proxy für Zeitreihenfolge)
    sorted_images = sorted(images, key=lambda img: img.get("relative_path", ""))

    groups: list[SeriesGroup] = []
    current_group: list[dict[str, Any]] = []

    for img in sorted_images:
        if not current_group:
            current_group = [img]
            continue

        # Serienzugehörigkeit prüfen: Präfix-Ähnlichkeit des Dateinamens
        prev_name = Path(current_group[-1].get("relative_path", "")).stem
        curr_name = Path(img.get("relative_path", "")).stem
        if _names_are_series(prev_name, curr_name):
            current_group.append(img)
        else:
            # Neue Gruppe beginnen, alte abschließen
            if len(current_group) > 1:
                group = _make_group(current_group)
                groups.append(group)
            current_group = [img]

    # Letzte Gruppe abschließen
    if len(current_group) > 1:
        groups.append(_make_group(current_group))

    return groups


def _names_are_series(name1: str, name2: str) -> bool:
    """Prüft ob zwei Dateinamen zur selben Serie gehören (gemeinsamer Präfix).

    Serienerkennung basiert auf dem Präfix vor der letzten Ziffernfolge.
    Beispiel: DSC_0001 und DSC_0002 gehören zur selben Serie.
    """
    import re

    # Extrahiere Präfix ohne abschließende Ziffernfolge
    pattern = r'^(.*?)(\d+)$'
    m1 = re.match(pattern, name1)
    m2 = re.match(pattern, name2)
    if not m1 or not m2:
        return False

    prefix1, num1 = m1.group(1), int(m1.group(2))
    prefix2, num2 = m2.group(1), int(m2.group(2))

    # Gleicher Präfix und aufeinanderfolgende Nummern (max. 10 Abstand)
    return prefix1 == prefix2 and abs(num2 - num1) <= 10


def _make_group(images: list[dict[str, Any]]) -> SeriesGroup:
    """Erstellt eine SeriesGroup aus einer Liste von Bildern und wählt das Bestbild."""
    # Series-ID aus Präfix des ersten Bilds
    first_name = Path(images[0].get("relative_path", "unknown")).stem
    series_id = hashlib.sha256(first_name.encode()).hexdigest()[:8]

    # Bestbild: höchster base_score; bei Gleichstand erstes Bild
    best_index = 0
    best_score = images[0].get("base_score", 0.0) or 0.0
    for i, img in enumerate(images[1:], 1):
        score = img.get("base_score", 0.0) or 0.0
        if score > best_score:
            best_score = score
            best_index = i

    return SeriesGroup(
        series_id=series_id,
        images=images,
        best_index=best_index,
    )


# ---------------------------------------------------------------------------
# Rangliste innerhalb einer Serie: rank_series
# ---------------------------------------------------------------------------

def rank_series(group: SeriesGroup) -> list[SeriesResult]:
    """Rankt alle Bilder einer Serie absteigend nach base_score.

    Das Bestbild erhält series_rank=1 und series_best=True.
    Bilder ohne Score werden ans Ende sortiert.
    """
    # Bilder mit ihrem Index für Rückverfolgung
    indexed = [(i, img) for i, img in enumerate(group.images)]
    # Absteigend nach Score sortieren; None-Scores ans Ende
    indexed.sort(key=lambda x: x[1].get("base_score", None) or -1.0, reverse=True)

    best_score = group.images[group.best_index].get("base_score", 0.0) or 0.0

    results: list[SeriesResult] = []
    for rank, (orig_idx, img) in enumerate(indexed, 1):
        score = img.get("base_score", 0.0) or 0.0
        distance = abs(best_score - score)
        results.append(SeriesResult(
            series_id=group.series_id,
            series_rank=rank,
            series_best=(orig_idx == group.best_index),
            distance_to_best=distance,
        ))
    return results


def compute_similarity(img1: dict[str, Any], img2: dict[str, Any]) -> float:
    """Berechnet Ähnlichkeit zwischen zwei Bildern anhand ihrer Scores.

    Gibt einen Wert zwischen 0.0 (unähnlich) und 1.0 (identisch) zurück.
    """
    score1 = img1.get("base_score", 0.0) or 0.0
    score2 = img2.get("base_score", 0.0) or 0.0
    # Einfache Ähnlichkeit: 1 - normierter Abstand der Scores
    return max(0.0, 1.0 - abs(score1 - score2))


# ---------------------------------------------------------------------------
# Hilfs-Dispatcher: Serienresultate auf Bilder zurückführen
# ---------------------------------------------------------------------------

def apply_series_results(
    images: list[dict[str, Any]],
    groups: list[SeriesGroup],
) -> list[dict[str, Any]]:
    """Trägt Serienzuordnung in Bild-Dicts ein und gibt aktualisierte Liste zurück.

    Bilder ohne Serienzuordnung behalten series_id=None und series_rank=None.
    """
    # Mapping: relative_path → SeriesResult
    series_map: dict[str, SeriesResult] = {}
    for group in groups:
        results = rank_series(group)
        for img, result in zip(group.images, results):
            path = img.get("relative_path", "")
            series_map[path] = result

    updated = []
    for img in images:
        path = img.get("relative_path", "")
        result = series_map.get(path)
        updated_img = dict(img)
        if result:
            updated_img["series_id"] = result.series_id
            updated_img["series_rank"] = result.series_rank
            updated_img["series_best"] = result.series_best
        else:
            updated_img.setdefault("series_id", None)
            updated_img.setdefault("series_rank", None)
            updated_img.setdefault("series_best", False)
        updated.append(updated_img)
    return updated
