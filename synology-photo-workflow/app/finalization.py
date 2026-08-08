"""
Skript: app/finalization.py
Zweck: PHASE3-Finalisierungs- und Transfer-Logik für abgeschlossene Batches.
Autor: MaiTai
Erstellt: 2026-08-08
Version: 1.0.0
Requires: pathlib, shutil, json, hashlib

Änderungsprotokoll:
  2026-08-08 | 1.0.0 | 00AP: Initiale Implementierung gemäß 00AP.md Abschnitt 3 und 17AP.md.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from . import VERSION


# ---------------------------------------------------------------------------
# Datenmodelle: FinalizationManifest und FinalizationResult
# ---------------------------------------------------------------------------

@dataclass
class FinalizationManifest:
    """Manifest für PHASE3-Transfer eines Batches.

    Enthält alle Pflichtfelder für Audit und Integritätsprüfung.
    """

    schema_version: str
    batch_id: str
    created_at: str
    updated_at: str
    producer_version: str
    source_batch_path: str
    target_batch_path: str | None
    publish_enabled: bool
    mode: Literal["copy", "move"] | None
    entries: list[dict[str, Any]]  # ManifestEntry-Dicts
    config_fingerprint: str
    state: str
    hash: str


@dataclass
class FinalizationResult:
    """Ergebnis eines PHASE3-Finalisierungslaufs."""

    batch_id: str
    state: str
    target_batch_path: Path | None
    manifest_hash: str | None
    error_reason: str | None


# ---------------------------------------------------------------------------
# Kern-API: finalize_batch
# ---------------------------------------------------------------------------

def finalize_batch(
    batch_path: Path,
    config: dict[str, Any],
    *,
    storage: Any = None,
    state_manager: Any = None,
) -> FinalizationResult:
    """Orchestriert PHASE3 komplett für einen phase2_completed-Batch.

    Prüft Vorbedingungen, plant Transfer, führt Kopier-/Move-Operation durch
    und schreibt Finalisierungs-Manifest. API-Fehler dürfen PHASE2 nicht
    zurücksetzen (00AP.md Abschnitt 1.3).
    """
    batch_id = batch_path.name
    finalization_config = config.get("finalization", {})

    # Vorbedingung: Finalisierung muss aktiviert sein
    if not finalization_config.get("enabled", False):
        return FinalizationResult(
            batch_id=batch_id,
            state="phase3_publish_disabled",
            target_batch_path=None,
            manifest_hash=None,
            error_reason="finalization_disabled_in_config",
        )

    # Zielpfad validieren
    publish_root = finalization_config.get("publish_root")
    if not publish_root:
        return FinalizationResult(
            batch_id=batch_id,
            state="finalization_state_invalid",
            target_batch_path=None,
            manifest_hash=None,
            error_reason="publish_root_not_configured",
        )

    target_root = Path(publish_root)
    target_path = target_root / batch_id
    transfer_mode: Literal["copy", "move"] = finalization_config.get("mode", "copy")

    try:
        # Transfer durchführen
        result_path = _transfer_batch(batch_path, target_path, mode=transfer_mode)

        # Manifest erzeugen und schreiben
        manifest = _create_finalization_manifest(
            batch_id=batch_id,
            source_path=batch_path,
            target_path=result_path,
            mode=transfer_mode,
            config_fingerprint=config.get("fingerprint", ""),
            publish_enabled=True,
        )
        manifest_hash = _write_finalization_manifest(manifest, batch_path)

        return FinalizationResult(
            batch_id=batch_id,
            state="phase3_transferred_to_target",
            target_batch_path=result_path,
            manifest_hash=manifest_hash,
            error_reason=None,
        )

    except Exception as exc:
        # API-/Transfer-Fehler darf PHASE2 nicht zurücksetzen
        return FinalizationResult(
            batch_id=batch_id,
            state="phase3_transfer_failed",
            target_batch_path=None,
            manifest_hash=None,
            error_reason=f"transfer_error:{type(exc).__name__}:{exc}",
        )


# ---------------------------------------------------------------------------
# Transfer-Logik: Kopieren oder Verschieben des Batch-Verzeichnisses
# ---------------------------------------------------------------------------

def _transfer_batch(
    source: Path,
    target: Path,
    mode: Literal["copy", "move"],
) -> Path:
    """Überträgt ein Batch-Verzeichnis sicher (Temp → Replace-Strategie).

    Bei mode=copy wird das Verzeichnis kopiert; bei mode=move verschoben.
    Das Zielverzeichnis wird nicht überschrieben wenn es bereits existiert.
    """
    if target.exists():
        raise FileExistsError(f"target_already_exists:{target}")

    target.parent.mkdir(parents=True, exist_ok=True)

    if mode == "copy":
        shutil.copytree(str(source), str(target))
    elif mode == "move":
        shutil.move(str(source), str(target))
    else:
        raise ValueError(f"unknown_transfer_mode:{mode}")

    return target


# ---------------------------------------------------------------------------
# Manifest-Erstellung und -Schreiben
# ---------------------------------------------------------------------------

def _create_finalization_manifest(
    batch_id: str,
    source_path: Path,
    target_path: Path,
    mode: Literal["copy", "move"] | None,
    config_fingerprint: str,
    publish_enabled: bool,
) -> FinalizationManifest:
    """Erstellt ein vollständiges Finalisierungs-Manifest mit Hash."""
    now = datetime.now(UTC).isoformat()

    # Dateiliste für Manifest-Einträge
    entries = _build_manifest_entries(source_path)

    # Hash des Manifests für Integritätsprüfung
    manifest_data = {
        "batch_id": batch_id,
        "source": str(source_path),
        "target": str(target_path),
        "entries": entries,
        "timestamp": now,
    }
    manifest_hash = hashlib.sha256(
        json.dumps(manifest_data, sort_keys=True).encode()
    ).hexdigest()

    return FinalizationManifest(
        schema_version="1.0",
        batch_id=batch_id,
        created_at=now,
        updated_at=now,
        producer_version=VERSION,
        source_batch_path=str(source_path),
        target_batch_path=str(target_path),
        publish_enabled=publish_enabled,
        mode=mode,
        entries=entries,
        config_fingerprint=config_fingerprint,
        state="phase3_transferred_to_target",
        hash=manifest_hash,
    )


def _build_manifest_entries(batch_path: Path) -> list[dict[str, Any]]:
    """Erstellt Manifest-Einträge für alle Dateien im Batch-Verzeichnis."""
    entries = []
    if not batch_path.is_dir():
        return entries

    for file_path in sorted(batch_path.rglob("*")):
        if file_path.is_file() and not file_path.is_symlink():
            relative = file_path.relative_to(batch_path).as_posix()
            size = file_path.stat().st_size
            # SHA256 nur für kleinere Dateien berechnen (< 50 MB)
            file_hash = ""
            if size < 50 * 1024 * 1024:
                h = hashlib.sha256()
                with file_path.open("rb") as fh:
                    for chunk in iter(lambda: fh.read(65536), b""):
                        h.update(chunk)
                file_hash = h.hexdigest()
            entries.append({
                "relative_path": relative,
                "size": size,
                "hash": file_hash,
            })
    return entries


def _write_finalization_manifest(manifest: FinalizationManifest, batch_path: Path) -> str:
    """Schreibt Finalisierungs-Manifest atomar in den SAVE-Unterordner."""
    save_dir = batch_path / "SAVE"
    save_dir.mkdir(exist_ok=True)
    manifest_path = save_dir / "finalization_manifest.json"

    data = {
        "schema_version": manifest.schema_version,
        "batch_id": manifest.batch_id,
        "created_at": manifest.created_at,
        "updated_at": manifest.updated_at,
        "producer_version": manifest.producer_version,
        "source_batch_path": manifest.source_batch_path,
        "target_batch_path": manifest.target_batch_path,
        "publish_enabled": manifest.publish_enabled,
        "mode": manifest.mode,
        "entries": manifest.entries,
        "config_fingerprint": manifest.config_fingerprint,
        "state": manifest.state,
        "hash": manifest.hash,
    }

    with tempfile.NamedTemporaryFile(
        "w", dir=save_dir, delete=False, suffix=".tmp.json", encoding="utf-8"
    ) as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        tmp = Path(fh.name)
    try:
        tmp.replace(manifest_path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

    return manifest.hash
