"""app/result_contract.py — Result-Vertraege, Manifest, Helper.

Spezifikation v10.2 - AP2
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Iterator

from .safety import atomic_json, utcnow


class FileManifest:
    """Sammelt und schreibt Datei-Manifest-Eintrage atomar."""

    def __init__(self, batch_id: str, phase: str = "phase1") -> None:
        self._batch_id = batch_id
        self._phase = phase
        self._entries: list[dict[str, Any]] = []

    def add(
        self,
        relative_path: str,
        sha256: str,
        size: int,
        extra: dict[str, Any] | None = None,
    ) -> None:
        entry = {
            "relative_path": relative_path,
            "sha256": sha256,
            "size": size,
        }
        if extra:
            entry.update(extra)
        self._entries.append(entry)

    def write(self, path: Path | str) -> None:
        from . import VERSION
        p = Path(path)
        now = utcnow()
        data = {
            "schema_version": 1,
            "created_at": now,
            "updated_at": now,
            "producer_version": VERSION,
            "batch_id": self._batch_id,
            "phase": self._phase,
            "file_count": len(self._entries),
            "entries": self._entries,
        }
        atomic_json(p, data, "batch_id")

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)


def atomic_json_write(path: Path | str, data: dict[str, Any]) -> None:
    """Schreibt beliebige dict-Daten atomar als JSON."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, ensure_ascii=False)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.rename(p)


def decision_counts(images: list[dict[str, Any]], field: str = "predicted_decision") -> dict[str, int]:
    """Zaehlt Entscheidungen (keep/review/reject) aus Images-Liste."""
    counts: dict[str, int] = {"keep": 0, "review": 0, "reject": 0}
    for img in images:
        decision = img.get(field, "review")
        if decision in counts:
            counts[decision] += 1
    return counts


def phase2_result(
    batch_id: str,
    images: list[dict[str, Any]],
    archive: dict[str, Any],
) -> dict[str, Any]:
    """Erstellt Phase-2-Result-Dict mit decision_counts und zip_conflicts."""
    return {
        "batch_id": batch_id,
        "decision_counts": decision_counts(images, "final_decision"),
        "archive_path": archive.get("archive_path"),
        "archive_hash": archive.get("archive_hash"),
        "zip_conflicts": [archive["zip_target_collision"]] if "zip_target_collision" in archive else [],
    }


def status_summary(statuses: list[str]) -> dict[str, int]:
    """Zaehlt Metadata-Write-Statusse (disabled/written/error)."""
    counts: dict[str, int] = {}
    for s in statuses:
        counts[s] = counts.get(s, 0) + 1
    return counts
