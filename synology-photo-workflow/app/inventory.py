"""Projekt: Synology Photo Workflow
Datei: app/inventory.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Inventarisiert stabile Batches, bildet sichere IDs und erzwingt exakte JPG-ARW-Paarungen.
SICHERHEIT: Keine Mutation bei unvollständigem oder widersprüchlichem Inventar.
"""
from __future__ import annotations

from pathlib import Path
from .safety import SafetyError, canonical_hash, sha256

IMG = {'.jpg', '.jpeg'}
RAW = {'.arw'}
REQUIRED_BATCH_DIRS = ('ARW', 'SAVE', 'Review', 'Rejected')


def files(path: str | Path, extensions: set[str]) -> list[Path]:
    """Liefert nur unmittelbare, reguläre und case-insensitiv erlaubte Dateien."""
    directory = Path(path)
    if not directory.is_dir() or directory.is_symlink():
        return []
    return sorted(item for item in directory.iterdir() if item.is_file() and not item.is_symlink() and item.suffix.lower() in extensions)


def assert_safe_batch(folder: str | Path) -> Path:
    """Lehnt Symlinks, nicht unterstützte Medien und ungültige Batchnamen vor jeder Mutation ab."""
    batch = Path(folder)
    if not batch.is_dir() or batch.is_symlink() or not batch.name or '/' in batch.name or chr(92) in batch.name:
        raise SafetyError('batch_invalid')
    for item in batch.rglob('*'):
        if item.is_symlink():
            raise SafetyError('batch_symlink')
        if item.is_file() and item.suffix and item.suffix.lower() not in IMG | RAW | {'.json', '.csv', '.zip'}:
            raise SafetyError(f'batch_unsupported_file:{item.name}')
    return batch


def batch_fingerprint(folder: str | Path) -> str:
    """Hasht deterministisch Pfad, Größe, Änderungszeit und Inhalts-Hash aller Originalmedien."""
    batch = assert_safe_batch(folder)
    rows = []
    for item in sorted(batch.rglob('*')):
        if item.is_file() and item.suffix.lower() in IMG | RAW:
            rows.append((item.relative_to(batch).as_posix(), item.stat().st_size, item.stat().st_mtime_ns, sha256(item)))
    return canonical_hash(rows)


def batch_id(folder: str | Path) -> str:
    """Erzeugt die beim Ordnerwechsel unveränderliche source_folder_name_fingerprint8-ID."""
    batch = Path(folder)
    return f'{batch.name}_{batch_fingerprint(batch)[:8]}'


def active_jpgs(folder: str | Path) -> list[Path]:
    """Nur Hauptordner-JPGs sind aktive Endentscheidungen und schützen passende ARWs."""
    return files(folder, IMG)


def arw_bindings(folder: str | Path) -> dict[Path, bool]:
    """Bindet ausschließlich exakt gleiche normalisierte Basenames; Mehrdeutigkeit blockiert Phase 2."""
    batch = assert_safe_batch(folder)
    arws = files(batch / 'ARW', RAW)
    jpgs = active_jpgs(batch)
    active = [image.stem.casefold() for image in jpgs]
    raw_names = [raw.stem.casefold() for raw in arws]
    if len(set(active)) != len(active) or len(set(raw_names)) != len(raw_names):
        raise SafetyError('review_state_invalid:ambiguous_basename')
    return {raw: raw.stem.casefold() in set(active) for raw in arws}


def require_complete_phase1_inventory(folder: str | Path) -> None:
    """Prüft die erforderlichen Unterordner und mindestens ein unterstütztes Bild vor der Phase-1-Mutation."""
    batch = assert_safe_batch(folder)
    if not files(batch, IMG | RAW):
        raise SafetyError('batch_empty')
    if any((batch / name).exists() and not (batch / name).is_dir() for name in REQUIRED_BATCH_DIRS):
        raise SafetyError('batch_reserved_path_conflict')
