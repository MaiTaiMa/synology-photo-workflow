"""
Skript: app/culling_baseline_adapter.py
Zweck: Lokaler technischer Baseline-Culling-Adapter ohne externe Abhängigkeiten.
Autor: MaiTai
Erstellt: 2026-08-08
Version: 1.0.0
Requires: pathlib, PIL (optional)

Änderungsprotokoll:
  2026-08-08 | 1.0.0 | 00AP: Initiale Implementierung gemäß 00AP.md Abschnitt 5.1 und 05AP.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


# ---------------------------------------------------------------------------
# Culling-Schnittstelle gemäß 00AP.md Abschnitt 5.1
# ---------------------------------------------------------------------------

@dataclass
class CullingInput:
    """Eingabedaten für einen Culling-Adapter-Aufruf."""

    image_path: str
    config: dict[str, Any]


@dataclass
class CullingOutput:
    """Ausgabe eines Culling-Adapter-Aufrufs mit vollständiger Score-Dokumentation."""

    base_score: float | None
    personal_score: float | None
    eye_score: float | None
    family_score: float | None
    analysis_error: bool
    error_reason: str | None


class CullingAdapter(Protocol):
    """Protokoll für austauschbare Culling-Adapter gemäß 00AP.md Abschnitt 5.1."""

    def evaluate(self, input: CullingInput) -> CullingOutput: ...


# ---------------------------------------------------------------------------
# BaselineCullingAdapter: Technische Baseline ohne externe KI-Abhängigkeiten
# ---------------------------------------------------------------------------

class BaselineCullingAdapter:
    """Lokaler technischer Baseline-Culling-Adapter.

    Berechnet einen technischen Basis-Score aus Schärfe, Belichtung und
    Ästhetik ohne CLIP oder HuggingFace. Läuft vollständig offline.
    """

    def evaluate(self, input: CullingInput) -> CullingOutput:
        """Bewertet ein Bild anhand technischer Basismetriken (CPU-only).

        Bei nicht lesbaren oder fehlerhaften Bildern wird analysis_error=True
        gesetzt statt eines stillen Ersatz-Scores (Regel aus 98AP §5).
        """
        try:
            base_score = self._compute_base_score(Path(input.image_path))
            return CullingOutput(
                base_score=base_score,
                personal_score=None,
                eye_score=None,
                family_score=None,
                analysis_error=False,
                error_reason=None,
            )
        except FileNotFoundError:
            return CullingOutput(
                base_score=None,
                personal_score=None,
                eye_score=None,
                family_score=None,
                analysis_error=True,
                error_reason="image_not_found",
            )
        except Exception as exc:
            return CullingOutput(
                base_score=None,
                personal_score=None,
                eye_score=None,
                family_score=None,
                analysis_error=True,
                error_reason=f"analysis_error:{type(exc).__name__}",
            )

    def _compute_base_score(self, image_path: Path) -> float | None:
        """Berechnet technischen Basis-Score aus Bildmetriken (Schärfe, Belichtung).

        Gibt None zurück wenn PIL nicht verfügbar ist, statt einen Fehler zu werfen.
        """
        try:
            from math import sqrt

            from PIL import Image, ImageFilter, ImageStat
        except ImportError:
            return None

        with Image.open(image_path) as img:
            # Vorschau auf 512px reduzieren für Performance
            preview = img.convert("RGB")
            preview.thumbnail((512, 512))
            gray = preview.convert("L")
            stat = ImageStat.Stat(gray)

            mean = stat.mean[0] / 255.0
            stddev = stat.stddev[0] / 128.0
            edges = ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES)).mean[0] / 255.0
            w, h = preview.size
            detail = min(1.0, (w * h) ** 0.5 / 512.0)

            # Sharpness: Kantenenergie normiert
            sharpness = min(1.0, edges * 3.0)
            # Exposure: Abstand von Mitte (0.5 = optimal)
            exposure = max(0.0, 1.0 - abs(mean - 0.5) * 1.8)
            # Aesthetic: gewichtete Kombination
            aesthetic = max(0.0, min(1.0, 0.55 * min(1.0, stddev) + 0.25 * detail + 0.20 * (1.0 - abs(w / max(h, 1) - 1.5) / 2.5)))

            # Basis-Score als gewichtetes Mittel
            base = 0.4 * sharpness + 0.35 * exposure + 0.25 * aesthetic
            return max(0.0, min(1.0, base))
