"""
Skript: app/safety.py
Zweck: Sicherheitsfundament – Validierungen, atomare Schreiboperationen, Hashing und ZIP-Prüfung.
Autor: MaiTai
Erstellt: 2026-07-30
Version: 7.9.0
Requires: hashlib, json, zipfile, tempfile, pathlib, datetime

Änderungsprotokoll:
  2026-08-08 | 7.9.0 | 00AP: sha256, canonical_hash, utcnow, atomic_json,
                               read_control_json, safe_zip, validate_zip ergänzt.
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
# Pflichtfelder gemäß 00AP.md Abschnitt 8.3 für alle JSON-Kontrollartefakte.
# ---------------------------------------------------------------------------
_REQUIRED_SCHEMA_FIELDS: frozenset[str] = frozenset({"schema_version", "producer_version"})
_TIMESTAMP_FIELDS: frozenset[str] = frozenset({"created_at", "updated_at", "timestamp"})


class SafetyError(Exception):
    """Fehler bei Safety-Validierung."""


@dataclass
class SafetyResult:
    """Ergebnis einer Safety-Prüfung mit erlaubter/nicht erlaubter Entscheidung."""

    allowed: bool
    reason: str | None = None


# ---------------------------------------------------------------------------
# Kryptografische Hilfsfunktionen
# ---------------------------------------------------------------------------

def sha256(path: Path) -> str:
    """Berechnet den SHA256-Hash einer Datei als Hex-String.

    Liest die Datei in 64-KiB-Blöcken, um Speicherüberlauf bei großen
    Rohdaten (ARW/JPG) zu vermeiden.
    """
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(rows: list[Any]) -> str:
    """Deterministischer SHA256-Hash serialisierter Datenzeilen.

    Serialisiert die übergebenen Zeilen als JSON-Array (sort_keys=True)
    und gibt den SHA256 zurück. Dient der reproduzierbaren Batch-ID.
    """
    serialized = json.dumps(rows, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


# ---------------------------------------------------------------------------
# Zeitstempel
# ---------------------------------------------------------------------------

def utcnow() -> str:
    """Liefert den aktuellen UTC-Zeitstempel als ISO-8601-String.

    Alle Artefaktzeitstempel verwenden UTC; der Zeitzonensuffix ist immer
    enthalten, damit Parsen außerhalb des Containers eindeutig bleibt.
    """
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Atomare JSON-Operationen (00AP.md Abschnitt 8.3)
# ---------------------------------------------------------------------------

def atomic_json(
    path: Path, data: dict[str, Any], required_field: str | None = None
) -> None:
    """Schreibt eine JSON-Datei atomar und prüft Pflichtfelder vorab.

    Gemäß 00AP.md Abschnitt 8.3 müssen alle JSON-Kontrollartefakte die
    Pflichtfelder schema_version, producer_version und mindestens einen
    Zeitstempel (created_at / updated_at / timestamp) enthalten.
    Fehlen diese Felder, wird SafetyError('control_record:missing_…')
    ausgelöst, bevor die Datei geschrieben wird. Der Schreibvorgang
    erfolgt über eine temporäre Datei auf demselben Dateisystem und wird
    erst nach erfolgreicher Validierung per rename atomar aktiviert.
    """
    # Pflichtfeldprüfung: Schema-Felder
    missing_schema = _REQUIRED_SCHEMA_FIELDS - set(data.keys())
    if missing_schema:
        raise SafetyError(
            f"control_record:missing_required_fields:{','.join(sorted(missing_schema))}"
        )
    # Pflichtfeldprüfung: mindestens ein Zeitstempel
    if not (_TIMESTAMP_FIELDS & set(data.keys())):
        raise SafetyError("control_record:missing_required_timestamp_field")
    # Optionales zusätzliches Pflichtfeld
    if required_field and required_field not in data:
        raise SafetyError(f"control_record:missing:{required_field}")
    # Atomar schreiben: temp → rename
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
    """Liest und validiert eine Control-JSON-Datei.

    Wirft SafetyError bei fehlender Datei, ungültigem JSON oder fehlendem
    Pflichtfeld, damit Aufrufer keine rohen Ausnahmen abfangen müssen.
    """
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
    """Erstellt sicher ein ZIP-Archiv und gibt Archiv- und Member-Hashes zurück.

    Schreibt zuerst in eine temporäre Datei im selben Verzeichnis und
    aktiviert das Archiv erst nach erfolgreicher Prüfung atomar per rename.
    Gibt (archive_sha256, {arcname: member_sha256}) zurück.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=target.parent, delete=False, suffix=".tmp.zip"
    ) as fh:
        tmp = Path(fh.name)
    try:
        member_hashes: dict[str, str] = {}
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for source in sources:
                # Relativer Pfad als Archivname; Traversal ist durch caller-seitige
                # assert_safe_batch-Prüfung bereits ausgeschlossen.
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
    """Prüft ein ZIP-Archiv auf Pfad-Traversal und optionale Member-Hashes.

    Gibt den SHA256 der Archivdatei zurück. Wirft SafetyError bei
    Traversal-Versuch ('zip_path_traversal:…') oder Hash-Abweichung
    ('zip_member_hash_mismatch:…').
    """
    with zipfile.ZipFile(archive, "r") as zf:
        for name in zf.namelist():
            # Traversal-Schutz: '..' in Pfadsegmenten und absolute Pfade ablehnen.
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

def validate_move_safe(source: Path, dest: Path) -> None:
    """Validiert, dass eine Move-Operation sicher ist.

    Prüft: Existenz der Quelle, Ungleichheit von Quelle und Ziel sowie
    Existenz des Zielverzeichnisses. Wirft SafetyError bei Verletzung.
    """
    if not source.exists():
        raise SafetyError(f"Source does not exist: {source}")
    if source == dest:
        raise SafetyError(f"Source and dest are identical: {source}")
    if not dest.parent.exists():
        raise SafetyError(f"Destination parent does not exist: {dest.parent}")


def within(base: str | Path, path: str | Path) -> bool:
    """Prüft kanonisch, ob 'path' innerhalb von 'base' liegt.

    Beide Pfade werden mit resolve() normalisiert, bevor der Vergleich
    stattfindet. Symlinks werden dadurch aufgelöst; '..' wird eliminiert.
    """
    return is_within_base(Path(path), Path(base))


def is_within_base(path: Path, base_dir: Path) -> bool:
    """Prüft kanonisch, ob ein Pfad innerhalb der erlaubten Basis liegt."""
    try:
        path.resolve(strict=False).relative_to(base_dir.resolve(strict=False))
        return True
    except ValueError:
        return False


def block_traversal(path: str) -> SafetyResult:
    """Blockiert unsichere Pfadangaben wie '..'-Traversal und Nullbytes."""
    if not path or path.strip() == "":
        return SafetyResult(False, "path_empty")
    normalized = path.replace("\\", "/")
    if "\x00" in normalized:
        return SafetyResult(False, "path_nullbyte")
    if ".." in [segment for segment in normalized.split("/") if segment]:
        return SafetyResult(False, "path_traversal")
    if ".." in Path(normalized).parts:
        return SafetyResult(False, "path_traversal")
    return SafetyResult(True, None)


def validate_path(path: str, base_dir: str) -> SafetyResult:
    """Validiert einen Pfad inklusive Basisgrenze und Symlink-Ausbruchsschutz."""
    traversal = block_traversal(path)
    if not traversal.allowed:
        return traversal

    base = Path(base_dir).expanduser().resolve(strict=False)
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = base / candidate

    resolved = candidate.resolve(strict=False)
    if not is_within_base(resolved, base):
        return SafetyResult(False, "path_outside_base")

    if candidate.exists() and candidate.is_symlink() and not is_within_base(candidate.resolve(), base):
        return SafetyResult(False, "symlink_outside_base")
    return SafetyResult(True, None)


def require_within(base: str | Path, path: str | Path) -> None:
    """Wirft SafetyError, wenn 'path' nicht innerhalb von 'base' liegt.

    Verbindliche Schranke für alle produktiven Pfadoperationen: kein
    Zugriff außerhalb des deklarierten basedir.
    """
    if not within(base, path):
        raise SafetyError(f"path_outside_basedir:{path}")


def validate_work_unit_images(unit: WorkUnitPlan, config: dict[str, Any]) -> None:
    """Validiere alle Images einer WorkUnit vor Verarbeitung.
    
    Paket 3: Safety-Validierung fuer WorkUnit-Images.
    - Alle Image-Pfade muessen existieren
    - Alle Images muessen im Batch-Verzeichnis sein
    - Keine symlinks oder spezielle Dateien
    """
    for image_path in unit.image_paths:
        # Existenz-Check
        if not image_path.exists():
            raise SafetyError(f"WorkUnit image does not exist: {image_path}")
        
        # Kein Symlink
        if image_path.is_symlink():
            raise SafetyError(f"WorkUnit image is a symlink: {image_path}")
        
        # Regulare Datei
        if not image_path.is_file():
            raise SafetyError(f"WorkUnit image is not a regular file: {image_path}")
        
        # Im Batch-Verzeichnis
        try:
            image_path.relative_to(unit.batch_path)
        except ValueError:
            raise SafetyError(f"WorkUnit image is outside batch directory: {image_path}")
        
        # Move-Validierung (Vorbereitung)
        temp_images = Path(config["paths"]["temp_images"])
        validate_move_safe(image_path, temp_images / image_path.name)
