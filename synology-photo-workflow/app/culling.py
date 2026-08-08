"""Projekt: Synology Photo Workflow
Datei: app/culling.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Erklärbares lokales Culling: robuste Score-Komposition, optionale Vorschauanalyse und deterministische Serienentscheidung.
SICHERHEIT: Bildanalyse ist optional, lokal und darf keine Originale verändern.
"""
from __future__ import annotations

from math import sqrt
from pathlib import Path
from typing import Any


def clamp(value: float) -> float:
    """Begrenzt jeden fachlichen Teilscore auf den normativen Bereich 0 bis 1."""
    return max(0.0, min(1.0, float(value)))


def final_score(components: dict[str, float | None], weights: dict[str, float]) -> float | None:
    """Kombiniert nur verfügbare Komponenten und renormiert deren Gewichte proportional auf 1."""
    active = {key: value for key, value in components.items() if value is not None and weights.get(key, 0) > 0}
    if not active:
        return None
    denominator = sum(weights[key] for key in active)
    return clamp(sum(clamp(active[key]) * weights[key] for key in active) / denominator)


def predicted(score: float | None, culling: dict[str, Any]) -> str:
    """Erzeugt ausschließlich die Prognose; die menschliche Endentscheidung bleibt getrennt."""
    if score is None:
        return 'review'
    if score >= culling['keep_threshold']:
        return 'keep'
    if score < culling['reject_threshold']:
        return 'reject'
    return 'review'


def stars(score: float | None, bands: list[dict[str, Any]]) -> int | None:
    """Ordnet einen finalen Score einem konfigurierten Sternband zu; unbekannt bleibt unbekannt."""
    if score is None:
        return None
    for band in bands:
        if band['min'] <= score <= band['max']:
            return band['rating']
    raise ValueError('score_outside_star_bands')


def technical_components(
    image: str | Path,
    base_weights: dict[str, float],
    longest_edge: int = 512,
    taste_options: dict | None = None,
) -> dict[str, float | None]:
    """Berechnet leichte CPU-Metriken und optionalen CLIP-personal_score; bei Fehler bleiben Werte None."""
    try:
        from PIL import Image, ImageFilter, ImageStat
        with Image.open(image) as source:
            preview = source.convert('RGB')
            preview.thumbnail((longest_edge, longest_edge))
            gray = preview.convert('L')
            stat = ImageStat.Stat(gray)
            mean = stat.mean[0] / 255.0
            deviation = stat.stddev[0] / 128.0
            edges = ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES)).mean[0] / 255.0
            width, height = preview.size
            detail = min(1.0, sqrt(width * height) / 512.0)
            sharpness = clamp(edges * 3.0)
            aesthetic = clamp(0.55 * min(1.0, deviation) + 0.25 * detail + 0.20 * (1.0 - abs(width / max(height, 1) - 1.5) / 2.5))
            exposure = clamp(1.0 - abs(mean - 0.5) * 1.8)
            reference_score = None
            if taste_options and taste_options.get('enabled'):
                from .clip_taste_adapter import score as clip_score
                reference_score = clip_score(image, taste_options)
            values = {'sharpness': sharpness, 'aesthetic': aesthetic, 'exposure': exposure, 'reference_score': reference_score}
            usable = {key: value for key, value in values.items() if value is not None and base_weights.get(key, 0) > 0}
            base = sum(usable[key] * base_weights[key] for key in usable) / sum(base_weights[key] for key in usable) if usable else None
            return {'base_score': base, 'sharpness': sharpness, 'aesthetic': aesthetic, 'exposure': exposure, 'reference_score': reference_score}
    except Exception:
        return {'base_score': None, 'sharpness': None, 'aesthetic': None, 'exposure': None, 'reference_score': None}


def apply_series(images: list[dict[str, Any]], enabled: bool = True) -> list[dict[str, Any]]:
    """Markiert deterministisch ein Bestbild je bereits zugeordneter Serie, ohne einen Schwachwert aggressiv zu retten."""
    if not enabled:
        return images
    groups: dict[str, list[dict[str, Any]]] = {}
    for image in images:
        series_id = image.get('series_id') or image['relative_path'].rsplit('_', 1)[0]
        image['series_id'] = series_id
        groups.setdefault(series_id, []).append(image)
    for group in groups.values():
        ranked = sorted(group, key=lambda item: (item.get('final_score') is not None, item.get('final_score') or -1, item['relative_path']), reverse=True)
        best = ranked[0]
        for rank, image in enumerate(ranked, 1):
            image['series_size'] = len(group); image['series_rank'] = rank; image['series_best'] = image is best
            image['series_distance_to_best'] = None if image.get('final_score') is None or best.get('final_score') is None else round(best['final_score'] - image['final_score'], 6)
    return images
