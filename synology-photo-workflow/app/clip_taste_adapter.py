"""Projekt: Synology Photo Workflow
Datei: app/clip_taste_adapter.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.8.0
Funktion: Optionaler CLIP-Adapter für personal_score via safetensors-Modell (CPU).
SICHERHEIT: Ohne explizite Modellpfade und installierte Abhängigkeiten bleibt das Backend deaktiviert.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import torch
except Exception:  # pragma: no cover
    torch = None  # type: ignore

try:
    from PIL import Image as _PILImage
except Exception:  # pragma: no cover
    _PILImage = None  # type: ignore

try:
    from transformers import CLIPModel, CLIPProcessor
except Exception:  # pragma: no cover
    CLIPModel = None  # type: ignore
    CLIPProcessor = None  # type: ignore

_ADAPTER_VERSION = '1.0'
_loaded: dict[str, Any] = {}


def diagnose(options: dict) -> dict:
    """Prüft Abhängigkeiten und Modellpfad ohne Bild-/Cachezugriff."""
    model_path = options.get('model_path', '')
    if torch is None:
        return {'ready': False, 'message': 'torch_not_installed', 'version': _ADAPTER_VERSION}
    if CLIPModel is None:
        return {'ready': False, 'message': 'transformers_not_installed', 'version': _ADAPTER_VERSION}
    if _PILImage is None:
        return {'ready': False, 'message': 'pillow_not_installed', 'version': _ADAPTER_VERSION}
    if not model_path or not Path(model_path).is_file():
        return {'ready': False, 'message': 'model_file_missing', 'version': _ADAPTER_VERSION}
    return {'ready': True, 'message': 'adapter_ready', 'version': _ADAPTER_VERSION}


def _load(model_path: str) -> tuple[Any, Any] | None:
    """Lädt Modell und Processor einmalig aus dem Elternverzeichnis der safetensors-Datei; gibt None bei Fehler zurück."""
    if torch is None or CLIPModel is None or _PILImage is None:
        return None
    key = str(model_path)
    if key not in _loaded:
        try:
            model_dir = str(Path(model_path).parent)
            model = CLIPModel.from_pretrained(model_dir)
            processor = CLIPProcessor.from_pretrained(model_dir)
            model.eval()
            _loaded[key] = (model, processor)
        except Exception:
            return None
    return _loaded.get(key)


def score(image_path: str | Path, options: dict) -> float | None:
    """Berechnet einen ästhetischen personal_score via CLIP-Prompt-Vergleich; None bei Fehler oder fehlendem Modell."""
    model_path = options.get('model_path', '')
    positive_prompts: list[str] = options.get('positive_prompts', [
        'a beautiful photograph',
        'sharp focus professional photo',
        'perfect exposure and composition',
    ])
    negative_prompts: list[str] = options.get('negative_prompts', [
        'blurry photo',
        'bad photo',
        'overexposed underexposed',
    ])
    loaded = _load(model_path)
    if loaded is None:
        return None
    try:
        model, processor = loaded
        image = _PILImage.open(image_path).convert('RGB')
        all_prompts = positive_prompts + negative_prompts
        inputs = processor(text=all_prompts, images=image, return_tensors='pt', padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1)[0].tolist()
        pos_sum = sum(probs[:len(positive_prompts)])
        neg_sum = sum(probs[len(positive_prompts):])
        total = pos_sum + neg_sum
        return round(pos_sum / total, 6) if total > 0 else None
    except Exception:
        return None
