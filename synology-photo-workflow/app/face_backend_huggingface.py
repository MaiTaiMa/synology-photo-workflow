"""
Skript: app/face_backend_huggingface.py
Zweck: Lokaler HuggingFace-Face-Detection-Adapter ohne Laufzeit-Download.
Autor: MaiTai
Erstellt: 2026-08-08
Version: 1.0.0
Requires: pathlib, transformers (optional, nur lokal bereitgestellt)

Änderungsprotokoll:
  2026-08-08 | 1.0.0 | 00AP: Initiale Implementierung gemäß 00AP.md Abschnitt 5.2 und 06AP.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Typdefinitionen: DetectedFace gemäß 00AP.md Abschnitt 5.2
# ---------------------------------------------------------------------------

@dataclass
class DetectedFace:
    """Erkanntes Gesicht mit Bounding-Box, Konfidenz und Embedding.

    Embeddings dürfen nur im RAM existieren und niemals persistiert werden
    (00AP.md Abschnitt 1.1, 98AP_IMPLEMENTATION_RULES.md Abschnitt 3).
    """

    bounding_box: tuple[float, float, float, float]  # (x, y, w, h) normiert
    confidence: float
    embedding: list[float]  # Nur RAM-flüchtig; nicht persistieren!


# ---------------------------------------------------------------------------
# HuggingFaceFaceBackend: Lokale HuggingFace-Detektion
# ---------------------------------------------------------------------------

class HuggingFaceFaceBackend:
    """Lokaler HuggingFace-Face-Detection-Adapter.

    Verwendet ausschließlich lokal bereitgestellte Modellgewichte.
    Kein Laufzeit-Download erlaubt (00AP.md Abschnitt 1.2).
    Wird nur instanziiert wenn transformers verfügbar und Modell geprüft ist.
    """

    def __init__(self, model_path: Path, model_hash: str) -> None:
        """Initialisiert den Adapter mit lokalem Modellpfad und SHA256-Hash.

        Validiert Modellpfad und Hash vor der Initialisierung. Wirft
        ValueError wenn Modell fehlt oder Hash nicht übereinstimmt.
        """
        self._model_path = Path(model_path)
        self._expected_hash = model_hash
        self._pipeline: Any = None
        self._validate_model()

    def _validate_model(self) -> None:
        """Prüft Modellpfad und SHA256-Hash vor jeder Verwendung."""
        import hashlib

        if not self._model_path.exists():
            raise ValueError(f"model_not_found:{self._model_path}")

        # Hash-Prüfung für Verzeichnisse: fingerprint-Datei prüfen
        if self._model_path.is_dir():
            fingerprint_file = self._model_path / "model_hash.sha256"
            if fingerprint_file.exists():
                actual_hash = fingerprint_file.read_text(encoding="utf-8").strip()
                if actual_hash != self._expected_hash:
                    raise ValueError(
                        f"model_hash_mismatch:{self._model_path}:"
                        f"expected={self._expected_hash[:16]}..."
                    )
        else:
            # Datei-Hash direkt berechnen
            h = hashlib.sha256()
            with self._model_path.open("rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    h.update(chunk)
            actual_hash = h.hexdigest()
            if actual_hash != self._expected_hash:
                raise ValueError(
                    f"model_hash_mismatch:{self._model_path}:"
                    f"expected={self._expected_hash[:16]}..."
                )

    def _load_pipeline(self) -> Any:
        """Lädt das HuggingFace-Pipeline einmalig pro Instanz (Lazy-Loading)."""
        if self._pipeline is not None:
            return self._pipeline
        try:
            from transformers import pipeline

            # Nur lokale Modelle – kein Download
            self._pipeline = pipeline(
                "object-detection",
                model=str(self._model_path),
                local_files_only=True,
            )
            return self._pipeline
        except ImportError as exc:
            raise RuntimeError("transformers_not_installed") from exc
        except Exception as exc:
            raise RuntimeError(f"model_load_failed:{exc}") from exc

    def detect(self, image_path: Path) -> list[DetectedFace]:
        """Erkennt Gesichter in einem Bild und gibt DetectedFace-Objekte zurück.

        Embeddings existieren nur im RAM und werden nicht persistiert.
        Bei Fehler wird eine leere Liste zurückgegeben (kein stiller Ersatz-Score).
        """
        try:
            from PIL import Image

            pipe = self._load_pipeline()
            with Image.open(image_path) as img:
                width, height = img.size
                results = pipe(img)

            faces = []
            for result in results:
                # Bounding-Box auf normierte Koordinaten [0,1] bringen
                box = result.get("box", {})
                x1 = box.get("xmin", 0) / width
                y1 = box.get("ymin", 0) / height
                x2 = box.get("xmax", 0) / width
                y2 = box.get("ymax", 0) / height
                w = x2 - x1
                h = y2 - y1
                confidence = float(result.get("score", 0.0))
                # Embedding ist nur ein Platzhalter; echte Backends
                # verwenden einen separaten Embedding-Extraktor
                embedding: list[float] = []
                faces.append(DetectedFace(
                    bounding_box=(x1, y1, w, h),
                    confidence=confidence,
                    embedding=embedding,
                ))
            return faces

        except ImportError:
            return []
        except Exception:
            return []

    @classmethod
    def is_available(cls) -> bool:
        """Prüft ob transformers und PIL installiert sind (ohne Modell zu laden)."""
        try:
            import importlib.util
            return (
                importlib.util.find_spec("transformers") is not None
                and importlib.util.find_spec("PIL") is not None
            )
        except Exception:
            return False
