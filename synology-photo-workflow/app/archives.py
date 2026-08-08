"""Projekt: Synology Photo Workflow
Datei: app/archives.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.8.0
Funktion: Unveränderlicher Archivplan, verifizierte Aktivierung, Löschjournal und sichere idempotente Archivwiederaufnahme.
SICHERHEIT: Wiederaufnahme validiert stets das vorhandene Archiv und löscht nur nachweislich archivierte Quellen.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import VERSION
from .inventory import arw_bindings
from .safety import (
    SafetyError,
    atomic_json,
    read_control_json,
    safe_zip,
    sha256,
    utcnow,
    validate_zip,
)


def _next_target(save: Path, stem: str) -> tuple[Path, str | None]:
    """Wählt einen freien Archivnamen; ein bereits vorhandenes Archiv wird niemals überschrieben."""
    primary = save / f'{stem}_SORTARW.zip'
    if not primary.exists():
        return primary, None
    index = 1
    while (save / f'{stem}_SORTARW_EXTRA{index}.zip').exists():
        index += 1
    return save / f'{stem}_SORTARW_EXTRA{index}.zip', primary.name


def _manifest_path(batch: Path) -> Path:
    """Kapselt den kanonischen persistierenden Archivnachweis eines Batches."""
    return batch / 'SAVE' / 'archive_manifest.json'


def _validate_existing_archive(batch: Path, manifest: dict[str, Any]) -> None:
    """Prüft vor jeder Wiederaufnahme Archivpfad, Membermenge, Memberhashes und Gesamthash erneut."""
    relative = manifest.get('archive_path')
    if not relative or Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise SafetyError('recovery_required:archive_path_invalid')
    archive = batch / relative
    if not archive.is_file():
        raise SafetyError('recovery_required:archive_missing')
    try:
        archive_hash = validate_zip(archive, manifest['entry_hashes'])
    except Exception as error:
        raise SafetyError('recovery_required:archive_validation_failed') from error
    if archive_hash != manifest['archive_hash']:
        raise SafetyError('recovery_required:archive_hash_changed')


def _delete_verified_sources(batch: Path, config: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    """Führt nur noch nicht protokollierte Löschungen nach erneuter Archivprüfung einzeln und atomar aus."""
    if not config['phase2']['delete_unneeded_arws_after_verified_archive'] or not manifest.get('archive_hash'):
        return manifest
    _validate_existing_archive(batch, manifest)
    deleted = {item['relative_path'] for item in manifest['deletions']}
    for entry in manifest['entries']:
        relative, expected = entry['relative_path'], entry['sha256']
        if relative in deleted:
            continue
        source = batch / relative
        if not source.exists():
            raise SafetyError('recovery_required:unjournaled_source_missing')
        if sha256(source) != expected:
            raise SafetyError('recovery_required:source_changed_after_archive')
        source.unlink()
        manifest['deletions'].append({'relative_path': relative, 'sha256': expected, 'archive_hash': manifest['archive_hash'], 'deleted_at': utcnow()})
        manifest['updated_at'] = utcnow()
        atomic_json(_manifest_path(batch), manifest, 'batch_id')
    return manifest


def resume_archive(batch: str | Path, config: dict[str, Any]) -> dict[str, Any]:
    """Setzt ausschließlich eine bereits aktivierte Archivtransaktion fort; neues ZIP-Erzeugen ist verboten."""
    batch_path = Path(batch)
    manifest = read_control_json(_manifest_path(batch_path), 'batch_id')
    if manifest['batch_id'] != batch_path.name:
        raise SafetyError('recovery_required:archive_batch_id_mismatch')
    return _delete_verified_sources(batch_path, config, manifest)


def archive_unneeded(batch: str | Path, config: dict[str, Any]) -> dict[str, Any]:
    """Erstellt ein ZIP einmalig, aktiviert sein Manifest und delegiert Löschungen an den gemeinsamen Resume-Pfad."""
    batch_path = Path(batch)
    manifest_file = _manifest_path(batch_path)
    if manifest_file.exists():
        return resume_archive(batch_path, config)
    bindings = arw_bindings(batch_path)
    selected = [path for path, protected in bindings.items() if not protected]
    save = batch_path / 'SAVE'
    save.mkdir(exist_ok=True)
    target, collision = _next_target(save, batch_path.name)
    entries = [{'relative_path': path.relative_to(batch_path).as_posix(), 'sha256': sha256(path), 'size': path.stat().st_size} for path in selected]
    archive_hash: str | None = None
    member_hashes: dict[str, str] = {}
    if selected:
        archive_hash, member_hashes = safe_zip(selected, target, batch_path)
    now = utcnow()
    manifest = {'schema_version': 1, 'batch_id': batch_path.name, 'created_at': now, 'updated_at': now, 'producer_version': VERSION, 'archive_path': target.relative_to(batch_path).as_posix() if archive_hash else None, 'archive_hash': archive_hash, 'entries': entries, 'entry_hashes': member_hashes, 'activation_verified_at': now if archive_hash else None, 'zip_target_collision': collision, 'deletions': []}
    atomic_json(manifest_file, manifest, 'batch_id')
    return _delete_verified_sources(batch_path, config, manifest)
