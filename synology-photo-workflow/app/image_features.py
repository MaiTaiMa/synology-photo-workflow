"""Projekt: Synology Photo Workflow
Datei: app/image_features.py
Mitentwickler: MaiTai
Erstellt: 2026-08-02
Projektversion: 7.9.0
Funktion: Gemeinsamer, rein technischer Bild-Cache pro Lauf: EXIF-korrigiertes Laden, Vorschauen,
          Perceptual Hash und Serien-Embedding-Slot ohne jede fachliche Entscheidung.
SICHERHEIT: rgb_image lebt ausschliesslich im RAM des laufenden Prozesses und wird nie persistiert,
            geloggt oder in einem Report verwendet.
HINWEIS: Neu, noch nicht in phases.py/manual_keep.py verdrahtet (siehe FEATURE_BRANCH_V7_9_0_TODO.md).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps


@dataclass(frozen=True)
class ImageSourceKey:
    canonical_path: str
    size_bytes: int
    mtime_ns: int


@dataclass(frozen=True)
class NormalizedImage:
    key: ImageSourceKey
    width: int
    height: int
    aspect_ratio: float
    rgb_image: Any


@dataclass(frozen=True)
class ImageFeatures:
    key: ImageSourceKey
    width: int
    height: int
    aspect_ratio: float
    perceptual_hash: str | None
    technical_preview: Any | None
    comparison_preview: Any | None
    series_embedding: tuple[float, ...] | None


class ImageFeatureService:
    def __init__(self) -> None:
        self._cache: dict[ImageSourceKey, NormalizedImage] = {}

    @staticmethod
    def _key(path: Path) -> ImageSourceKey:
        stat = path.stat()
        return ImageSourceKey(str(path.resolve()), stat.st_size, stat.st_mtime_ns)

    def load_rgb(self, path: Path) -> NormalizedImage | None:
        key = self._key(path)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        try:
            with Image.open(path) as source:
                corrected = ImageOps.exif_transpose(source)
                rgb = corrected.convert('RGB')
        except Exception:
            return None
        width, height = rgb.size
        normalized = NormalizedImage(key, width, height, width / max(height, 1), rgb)
        self._cache[key] = normalized
        return normalized

    def preview(self, image: NormalizedImage, long_edge: int) -> Any:
        preview = image.rgb_image.copy()
        preview.thumbnail((long_edge, long_edge))
        return preview

    def perceptual_hash(self, image: NormalizedImage) -> str | None:
        try:
            small = image.rgb_image.convert('L').resize((9, 8))
            pixels = list(small.getdata())
            return ''.join('1' if pixels[row * 9 + col] > pixels[row * 9 + col + 1] else '0' for row in range(8) for col in range(9 - 1))
        except Exception:
            return None

    def features(self, path: Path, *, technical_edge: int | None = None, comparison_edge: int | None = None, need_hash: bool = False) -> ImageFeatures | None:
        image = self.load_rgb(path)
        if image is None:
            return None
        technical = self.preview(image, technical_edge) if technical_edge else None
        comparison = self.preview(image, comparison_edge) if comparison_edge else None
        phash = self.perceptual_hash(image) if need_hash else None
        return ImageFeatures(image.key, image.width, image.height, image.aspect_ratio, phash, technical, comparison, None)

    def clear(self) -> None:
        self._cache.clear()
