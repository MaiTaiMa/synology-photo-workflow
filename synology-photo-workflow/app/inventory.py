"""app/inventory.py — Batch-Inventur, ARW-Bindung, Safety-Checks.

Spezifikation v10.2 - AP4
"""
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any

from .safety import SafetyError


def batch_id(batch_dir: Path | str) -> str:
    """Berechnet Batch-ID (SHA256 aller Dateinamen + Groessen)."""
    p = Path(batch_dir)
    h = hashlib.sha256()
    for f in sorted(p.rglob("*")):
        if f.is_file() and not f.is_symlink():
            h.update(f.name.encode())
            h.update(str(f.stat().st_size).encode())
    return h.hexdigest()[:12]


def assert_safe_batch(batch_dir: Path | str) -> None:
    """Prueft Batch auf Symlinks (verboten)."""
    p = Path(batch_dir)
    for f in p.rglob("*"):
        if f.is_symlink():
            raise SafetyError(f"symlink_detected:{f}")


def arw_bindings(batch_dir: Path | str) -> dict[Path, bool]:
    """Prueft welche ARWs durch aktive JPGs geschuetzt sind.

    Returns: {arw_path: is_protected, ...}
    """
    p = Path(batch_dir)
    arw_dir = p / "ARW"
    if not arw_dir.exists():
        return {}
    
    arws = {f.stem.lower(): f for f in arw_dir.glob("*.arw")}
    
    # Aktive JPGs sammeln (nur Review/ und Root, nicht Review/*.jpg)
    active_jpgs: set[str] = set()
    for jpg in list(p.glob("*.jpg")) + list(p.glob("*.jpeg")):
        if jpg.parent == p:  # Nur Root-level
            active_jpgs.add(jpg.stem.lower())
    
    # Ambiguitaet pruefen (z.B. IMG_1.jpg + IMG_1.jpeg)
    jpg_stems = [f.stem.lower() for f in p.glob("*.jpg") if f.parent == p]
    jpeg_stems = [f.stem.lower() for f in p.glob("*.jpeg") if f.parent == p]
    if set(jpg_stems) & set(jpeg_stems):
        raise SafetyError("ambiguous_jpg_jpeg_pairing")
    
    result: dict[Path, bool] = {}
    for arw_path in arws.values():
        stem = arw_path.stem.lower()
        result[arw_path] = stem in active_jpgs
    
    return result
