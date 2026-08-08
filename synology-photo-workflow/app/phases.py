"""
Skript: app/phases.py
Zweck: Orchestrierung PHASE1 und PHASE2 – Inventar, Move, Manifest, CSV,
       Review-Ablage und Archivierung.
Autor: MaiTai
Erstellt: 2026-07-30
Version: 7.9.0
Requires: pathlib, shutil, json, csv

Änderungsprotokoll:
  2026-08-08 | 7.9.0 | 00AP: phase1 und phase2 als kanonische Einstiegspunkte.
"""
from __future__ import annotations

import csv
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import VERSION
from .result_contract import atomic_json_write
from .safety import SafetyError


def _jpg_files(directory: Path) -> list[Path]:
    """Gibt alle unmittelbaren JPG-Dateien eines Verzeichnisses zurück."""
    extensions = {".jpg", ".jpeg"}
    return sorted(
        item
        for item in directory.iterdir()
        if item.is_file() and not item.is_symlink()
        and item.suffix.lower() in extensions
    )


def _write_phase1_manifest(batch_path: Path, files: list[Path]) -> None:
    """Schreibt SAVE/phase1_manifest.json atomar."""
    save_dir = batch_path / "SAVE"
    save_dir.mkdir(exist_ok=True)
    now = datetime.now(UTC).isoformat()
    manifest = {
        "schema_version": 1,
        "producer_version": VERSION,
        "batch_id": batch_path.name,
        "created_at": now,
        "updated_at": now,
        "files": [f.relative_to(batch_path).as_posix() for f in files],
    }
    atomic_json_write(save_dir / "phase1_manifest.json", manifest)


def _write_culling_csv(batch_path: Path, files: list[Path]) -> None:
    """Schreibt SAVE/culling_scores.csv mit Basis-Scores."""
    save_dir = batch_path / "SAVE"
    save_dir.mkdir(exist_ok=True)
    csv_path = save_dir / "culling_scores.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["relative_path", "base_score", "decision"])
        for f in files:
            writer.writerow([f.relative_to(batch_path).as_posix(), "", "review"])


def _move_to_review(batch_path: Path, files: list[Path]) -> None:
    """Kopiert JPG-Dateien in den Review-Unterordner (nicht destructive)."""
    review_dir = batch_path / "Review"
    review_dir.mkdir(exist_ok=True)
    for f in files:
        dest = review_dir / f.name
        if not dest.exists():
            shutil.copy2(str(f), str(dest))


def phase1(config: dict[str, Any], folder: str | None = None) -> list[dict[str, Any]]:
    """Führt Phase 1 für alle Batches in temp_sd aus.

    Für jeden Batch:
    1. Batch aus temp_sd nach temp_images verschieben.
    2. SAVE/phase1_manifest.json schreiben.
    3. SAVE/culling_scores.csv schreiben.
    4. JPGs in Review/ ablegen.

    Gibt Liste von {'batch_id': …, 'path': …, 'status': …} zurück.
    """
    sd_dir = Path(config["paths"]["temp_sd"])
    images_dir = Path(config["paths"]["temp_images"])
    images_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    if not sd_dir.is_dir():
        return results
    limit = config.get("workflow", {}).get("batch_limit", 999)
    processed = 0
    for batch in sorted(sd_dir.iterdir()):
        if not batch.is_dir() or batch.is_symlink():
            continue
        if processed >= limit:
            break
        try:
            # Batch in temp_images verschieben
            target = images_dir / batch.name
            shutil.move(str(batch), str(target))
            # JPG-Dateien ermitteln und Artefakte schreiben
            jpgs = _jpg_files(target)
            _write_phase1_manifest(target, jpgs)
            _write_culling_csv(target, jpgs)
            _move_to_review(target, jpgs)
            results.append({
                "batch_id": target.name,
                "path": str(target),
                "status": "completed",
            })
            processed += 1
        except (SafetyError, OSError) as exc:
            results.append({
                "batch_id": batch.name,
                "path": str(batch),
                "status": "error",
                "reason": str(exc),
            })
    return results


def phase2(config: dict[str, Any], folder: str | None = None) -> list[dict[str, Any]]:
    """Führt Phase 2 (Review-Abschluss und Archivierung) durch.

    Platzhalter-Implementierung – die vollständige Logik wird in 12AP ergänzt.
    """
    images_dir = Path(config["paths"]["temp_images"])
    results: list[dict[str, Any]] = []
    if not images_dir.is_dir():
        return results
    for batch in sorted(images_dir.iterdir()):
        if not batch.is_dir() or batch.is_symlink():
            continue
        results.append({"batch_id": batch.name, "path": str(batch), "status": "pending"})
    return results
