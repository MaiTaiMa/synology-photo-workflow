"""Projekt: Synology Photo Workflow
Skript: app/safety.py
Zweck: Sicherheitsfundament – Validierungen, atomare Schreiboperationen, Hashing und ZIP-Pruefung.
Autor: MaiTai
Erstellt: 2026-07-30
Version: 7.9.0
Requires: hashlib, json, zipfile, tempfile, pathlib, datetime

Aenderungsprotokoll:
  2026-08-08 | 7.9.0 | 01AP: SafetyResult, validate_path, is_within_base,
                       block_traversal und rueckgabefaehiges require_within ergaenzt.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .work_units import WorkUnitPlan

# ---------------------------------------------------------------------------
# Pflichtfelder gemaess 00AP.md Abschnitt 8.3 fuer alle JSON-Kontrollartefakte.
# ---------------------------------------------------------------------------
_REQUIRED_SCHEMA_FIELDS: frozenset[str] = frozenset({"schema_version", "producer_version"})
_TIMESTAMP_FIELDS: frozenset[str] = frozenset({"created_at", "updated_at", "timestamp"})


class SafetyError(Exception):
    """Fehler bei Safety-Validierung."""


@dataclass(frozen=True)
class SafetyResult:
    """Explizites Ergebnis fuer Pfadfreigaben statt stiller True/False-Pfade."""

    allowed: bool
    reason: str | None = None


# ---------------------------------------------------------------------------
# Kryptografische Hilfsfunktionen
# ---------------------------------------------------------------------------

def sha256(path: Path) -> str:
    """Berechnet den SHA256-Hash einer Datei als Hex-String.

    Liest die Datei in 64-KiB-Bloecken, um Speicherueberlauf bei grossen
    Rohdaten (ARW/JPG) zu vermeiden.
    """
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(rows: list[Any] | dict[str, Any]) -> str:
    """Deterministischer SHA256-Hash serialisierter Datenstrukturen."""

    serialized = json.dumps(rows, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


# ---------------------------------------------------------------------------
# Zeitstempel
# ---------------------------------------------------------------------------

def utcnow() -> str:
    """Liefert den aktuellen UTC-Zeitstempel als ISO-8601-String."""

    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Atomare JSON-Operationen (00AP.md Abschnitt 8.3)
# ---------------------------------------------------------------------------

def atomic_json(
    path: Path, data: dict[str, Any], required_field: str | None = None
) -> None:
    """Schreibt eine JSON-Datei atomar und prueft Pflichtfelder vorab."""

    missing_schema = _REQUIRED_SCHEMA_FIELDS - set(data.keys())
    if missing_schema:
        raise SafetyError(
            f"control_record:missing_required_fields:{','.join(sorted(missing_schema))}"
        )
    if not (_TIMESTAMP_FIELDS & set(data.keys())):
        raise SafetyError("control_record:missing_required_timestamp_field")
    if required_field and required_field not in data:
        raise SafetyError(f"control_record:missing:{required_field}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", dir=path.parent, delete=False, suffix=".tmp.json", encoding="utf-8"
    ) as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        tmp = Path(fh.name)
    try:
        tmp.replace(path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def read_control_json(path: Path, required_field: str) -> dict[str, Any]:
    """Liest und validiert eine Control-JSON-Datei."""

    if not path.exists():
        raise SafetyError(f"control_record:not_found:{path}")
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SafetyError(f"control_record:unreadable:{path}") from exc
    if required_field not in data:
        raise SafetyError(f"control_record:missing:{required_field}")
    return data


# ---------------------------------------------------------------------------
# ZIP-Archivoperationen
# ---------------------------------------------------------------------------

def safe_zip(
    sources: list[Path], target: Path, base: Path
) -> tuple[str, dict[str, str]]:
    """Erstellt sicher ein ZIP-Archiv und gibt Archiv- und Member-Hashes zurueck."""

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=target.parent, delete=False, suffix=".tmp.zip"
    ) as fh:
        tmp = Path(fh.name)
    try:
        member_hashes: dict[str, str] = {}
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for source in sources:
                arcname = source.relative_to(base).as_posix()
                member_hashes[arcname] = sha256(source)
                zf.write(source, arcname)
        archive_hash = sha256(tmp)
        tmp.replace(target)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return archive_hash, member_hashes


def validate_zip(
    archive: Path, member_hashes: dict[str, str] | None = None
) -> str:
    """Prueft ein ZIP-Archiv auf Pfad-Traversal und optionale Member-Hashes."""

    with zipfile.ZipFile(archive, "r") as zf:
        for name in zf.namelist():
            parts = name.replace("\\", "/").split("/")
            if ".." in parts or name.startswith("/"):
                raise SafetyError(f"zip_path_traversal:{name}")
        if member_hashes is not None:
            for arcname, expected in member_hashes.items():
                with zf.open(arcname) as member:
                    h = hashlib.sha256()
                    for chunk in iter(lambda: member.read(65536), b""):
                        h.update(chunk)
                    actual = h.hexdigest()
                    if actual != expected:
                        raise SafetyError(f"zip_member_hash_mismatch:{arcname}")
    return sha256(archive)


# ---------------------------------------------------------------------------
# Datei- und Pfad-Validierungen
# ---------------------------------------------------------------------------

def block_traversal(path: str) -> SafetyResult:
    """Blockiert ..-Traversal, Null-Bytes und leere Pfadangaben vor jeder Nutzung."""

    if not path:
        return SafetyResult(False, 'empty_path')
    if "\x00" in path:
        return SafetyResult(False, 'null_byte')
    normalized = path.replace("\\", "/")
    parts = [part for part in normalized.split('/') if part not in ('', '.')]
    if '..' in parts:
        return SafetyResult(False, 'path_traversal')
    return SafetyResult(True, None)


def _canonical_path(path: Path) -> Path:
    """Loest existierende Pfadanteile strikt auf und behaelt fehlende Suffixe bei."""

    expanded = path.expanduser()
    try:
        return expanded.resolve(strict=True)
    except FileNotFoundError:
        existing_parent = expanded
        missing_parts: list[str] = []
        while not existing_parent.exists() and existing_parent != existing_parent.parent:
            missing_parts.append(existing_parent.name)
            existing_parent = existing_parent.parent
        resolved_parent = existing_parent.resolve(strict=True)
        suffix = list(reversed(missing_parts))
        return resolved_parent.joinpath(*suffix)


def is_within_base(path: Path, base_dir: Path) -> bool:
    """Prueft kanonisch, ob ein Pfad innerhalb der erlaubten Basis bleibt."""

    try:
        resolved_base = _canonical_path(base_dir)
        resolved_path = _canonical_path(path)
        resolved_path.relative_to(resolved_base)
        return True
    except ValueError:
        return False


def validate_path(path: str, base_dir: str) -> SafetyResult:
    """Prueft, ob ein Pfad innerhalb der erlaubten Basis und traversal-sicher ist."""

    traversal = block_traversal(path)
    if not traversal.allowed:
        return traversal
    base_path = _canonical_path(Path(base_dir))
    candidate_path = Path(path).expanduser()
    if not candidate_path.is_absolute():
        candidate_path = _canonical_path(base_path / candidate_path)
    else:
        candidate_path = _canonical_path(candidate_path)
    if not is_within_base(candidate_path, base_path):
        return SafetyResult(False, 'outside_base')
    return SafetyResult(True, None)


def validate_move_safe(source: Path, dest: Path) -> None:
    """Validiert, dass eine Move-Operation sicher ist."""

    if not source.exists():
        raise SafetyError(f"Source does not exist: {source}")
    if source == dest:
        raise SafetyError(f"Source and dest are identical: {source}")
    if not dest.parent.exists():
        raise SafetyError(f"Destination parent does not exist: {dest.parent}")


def within(base: str | Path, path: str | Path) -> bool:
    """Kompatibilitaetsalias fuer kanonische Basispruefungen."""

    return is_within_base(Path(path), Path(base))


def require_within(base: str | Path, path: str | Path) -> Path:
    """Wirft SafetyError bei Pfaden ausserhalb von basedir und gibt sonst Path zurueck."""

    resolved = Path(path).expanduser().resolve(strict=False)
    if not is_within_base(resolved, Path(base)):
        raise SafetyError(f"path_outside_basedir:{path}")
    return resolved


def validate_work_unit_images(unit: WorkUnitPlan, config: dict[str, Any]) -> None:
    """Validiere alle Images einer WorkUnit vor Verarbeitung."""

    for image_path in unit.image_paths:
        if not image_path.exists():
            raise SafetyError(f"WorkUnit image does not exist: {image_path}")
        if image_path.is_symlink():
            raise SafetyError(f"WorkUnit image is a symlink: {image_path}")
        if not image_path.is_file():
            raise SafetyError(f"WorkUnit image is not a regular file: {image_path}")
        try:
            image_path.relative_to(unit.batch_path)
        except ValueError as exc:
            raise SafetyError(
                f"WorkUnit image is outside batch directory: {image_path}"
            ) from exc
        temp_images = Path(config["paths"]["temp_images"])
        validate_move_safe(image_path, temp_images / image_path.name)
