"""app/phases.py — Phase 1 (Inventur, Copy, Manifest, CSV) und Phase 2.

Spezifikation v10.2 - AP4
"""
from __future__ import annotations
import csv
import shutil
from pathlib import Path
from typing import Any

from .batch_state import write_state, state_path
from .planning import plan_phase1, plan_phase2
from .result_contract import FileManifest
from .safety import SafetyError, sha256, utcnow

_CSV_COLUMNS = [
    "filename", "sharpness", "aesthetic", "exposure", "reference_score",
    "base_score", "eye_score", "personal_score", "family_score",
    "final_score", "star_rating", "predicted_decision",
]


def run_phase1(
    config: dict[str, Any],
    folder: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Phase 1: Inventur, Kopie nach Review/, Manifest, CSV-Stub, State."""
    paths = config.get("paths", {})
    basedir = Path(paths.get("basedir", "."))
    temp_images = basedir / paths.get("temp_images", "TEMP_IMAGES")
    
    batches_plan = plan_phase1(config, folder)
    results: list[dict[str, Any]] = []

    for batch_plan in batches_plan:
        batch_src = Path(batch_plan["path"])
        batch_id_str = batch_plan["batch_id"]

        target = temp_images / batch_id_str
        review_dir = target / "Review"
        save_dir = target / "SAVE"

        target.mkdir(parents=True, exist_ok=True)
        review_dir.mkdir(exist_ok=True)
        save_dir.mkdir(exist_ok=True)

        sp = state_path(basedir, batch_id_str)
        write_state(sp, batch_id_str, "phase1_running")

        src_files = sorted(
            f for f in batch_src.rglob("*")
            if f.is_file() and not f.is_symlink()
        )

        from . import VERSION
        from .result_contract import FileManifest
        manifest = FileManifest(batch_id_str, "phase1")

        for src_file in src_files:
            rel = src_file.relative_to(batch_src)
            dst = review_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src_file), str(dst))
            h = sha256(dst)
            manifest.add(f"Review/{rel.as_posix()}", h, dst.stat().st_size)

        manifest_path = save_dir / "phase1_manifest.json"
        manifest.write(manifest_path)

        csv_path = save_dir / "culling_scores.csv"
        _write_culling_csv_stub(csv_path, src_files, batch_src)

        write_state(sp, batch_id_str, "phase1_completed")

        results.append({
            "batch_id": batch_id_str,
            "path": str(target),
            "status": "completed",
            "batches_pending": max(0, len(batches_plan) - len(results) - 1),
            "phase1_manifest": str(manifest_path),
            "culling_csv": str(csv_path),
            "file_count": len(src_files),
        })

    return results


def _write_culling_csv_stub(
    csv_path: Path,
    src_files: list[Path],
    batch_src: Path,
) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_COLUMNS)
        writer.writeheader()
        for src_file in src_files:
            rel = src_file.relative_to(batch_src)
            writer.writerow({
                "filename": rel.as_posix(),
                "sharpness": 0.0,
                "aesthetic": 0.0,
                "exposure": 0.0,
                "reference_score": 0.0,
                "base_score": 0.0,
                "eye_score": 0.0,
                "personal_score": 0.0,
                "family_score": 0.0,
                "final_score": 0.0,
                "star_rating": 0,
                "predicted_decision": "review",
            })


def run_phase2(
    config: dict[str, Any],
    folder: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Phase 2: Verarbeitet freigegebene Reviews (Stub)."""
    return []


# Aliases fuer Test-Kompatibilitaet
phase1 = run_phase1
phase2 = run_phase2
