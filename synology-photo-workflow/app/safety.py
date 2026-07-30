"""Projekt: Synology Photo Workflow
Datei: app/safety.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Zentrale Integritätsgrenzen: Hashes, atomare JSON-Aktivierung, Schema-Grundvertrag und ZIP-Prüfung.
SICHERHEIT: Originale werden nur durch verifizierte Transaktionen verändert.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


class SafetyError(RuntimeError):
    """Signalisiert eine Sicherheits- oder Integritätsverletzung."""


REQUIRED_CONTROL_FIELDS = {'schema_version', 'created_at', 'updated_at', 'producer_version'}
MAX_ZIP_MEMBER_BYTES = 4 * 1024 * 1024 * 1024
MAX_ZIP_TOTAL_BYTES = 32 * 1024 * 1024 * 1024


def utcnow() -> str:
    """Liefert einen UTC-Zeitstempel im normierten ISO-8601-Z-Format."""
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def sha256(path: str | Path) -> str:
    """Berechnet den vollständigen SHA-256 einer regulären Datei."""
    file_path = Path(path)
    if not file_path.is_file() or file_path.is_symlink():
        raise SafetyError(f'hash_requires_regular_file:{file_path}')
    digest = hashlib.sha256()
    with file_path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    """Hasht JSON-deterministisch serialisierbare Steuerwerte."""
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def within(base: str | Path, path: str | Path) -> bool:
    """Prüft nach Normalisierung, ob path innerhalb von base liegt."""
    try:
        Path(path).resolve().relative_to(Path(base).resolve())
        return True
    except ValueError:
        return False


def require_within(base: str | Path, path: str | Path) -> Path:
    """Normalisiert einen produktiven Pfad oder verweigert einen Pfadausbruch."""
    resolved = Path(path).resolve()
    if not within(base, resolved):
        raise SafetyError(f'path_outside_basedir:{path}')
    return resolved


def validate_control_record(payload: Mapping[str, Any], scope_key: str | None = None) -> None:
    """Validiert die gemeinsamen Mindestfelder aller Steuerdateien vor Aktivierung/Nutzung."""
    missing = REQUIRED_CONTROL_FIELDS - set(payload)
    if missing:
        raise SafetyError(f'control_record_missing:{sorted(missing)}')
    if not isinstance(payload['schema_version'], int) or payload['schema_version'] <= 0:
        raise SafetyError('control_record_schema_version')
    if payload['producer_version'] != '7.7.0':
        raise SafetyError('control_record_producer_version')
    for field in ('created_at', 'updated_at'):
        if not isinstance(payload[field], str) or not payload[field].endswith('Z'):
            raise SafetyError(f'control_record_timestamp:{field}')
    if scope_key and not payload.get(scope_key):
        raise SafetyError(f'control_record_scope_missing:{scope_key}')


def read_control_json(path: str | Path, scope_key: str | None = None) -> dict[str, Any]:
    """Liest und validiert eine Steuerdatei; nie stillschweigend reparieren."""
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SafetyError(f'control_record_unreadable:{Path(path).name}') from error
    if not isinstance(payload, dict):
        raise SafetyError('control_record_not_object')
    validate_control_record(payload, scope_key)
    return payload


def atomic_json(path: str | Path, payload: Mapping[str, Any], scope_key: str | None = None) -> None:
    """Schreibt validiertes JSON per Tempdatei, fsync und atomarem Replace auf demselben Dateisystem."""
    validate_control_record(payload, scope_key)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix='.', suffix='.tmp', dir=destination.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
            handle.flush()
            os.fsync(handle.fileno())
        read_control_json(temporary_name, scope_key)
        os.replace(temporary_name, destination)
        directory_fd = os.open(destination.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def validate_zip(path: str | Path, expected: Mapping[str, str] | None = None) -> str:
    """Prüft ZIP-Lesbarkeit, sichere relative Membernamen, Größen und optionale Entry-Hashes."""
    archive = Path(path)
    total_size = 0
    with zipfile.ZipFile(archive) as bundle:
        seen: set[str] = set()
        for info in bundle.infolist():
            member = info.filename
            member_path = Path(member)
            if member in seen or member.startswith('/') or '..' in member_path.parts:
                raise SafetyError('zip_path_traversal')
            seen.add(member)
            if info.file_size > MAX_ZIP_MEMBER_BYTES:
                raise SafetyError('zip_member_too_large')
            total_size += info.file_size
            if total_size > MAX_ZIP_TOTAL_BYTES:
                raise SafetyError('zip_total_too_large')
            if info.file_size and info.compress_size and info.file_size / info.compress_size > 100:
                raise SafetyError('zip_compression_ratio')
            member_bytes = bundle.read(info)
            if expected is not None:
                if member not in expected or hashlib.sha256(member_bytes).hexdigest() != expected[member]:
                    raise SafetyError('zip_member_hash_mismatch')
        if expected is not None and set(expected) != seen:
            raise SafetyError('zip_member_set_mismatch')
    return sha256(archive)


def safe_zip(sources: list[Path], target: str | Path, relative_to: str | Path) -> tuple[str, dict[str, str]]:
    """Erstellt und aktiviert ein ZIP erst nach vollständiger Hash-/Lesbarkeitsprüfung."""
    destination = Path(target)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + '.tmp')
    hashes: dict[str, str] = {}
    with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for source in sources:
            member = source.relative_to(relative_to).as_posix()
            hashes[member] = sha256(source)
            bundle.write(source, member)
    archive_hash = validate_zip(temporary, hashes)
    os.replace(temporary, destination)
    return archive_hash, hashes
