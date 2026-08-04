"""app/batch_state.py — Batch-Zustandsautomat, State-Dateien.

Spezifikation v10.2 - AP2
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from .safety import atomic_json, utcnow, SafetyError


_PHASE_ORDER = [
    "phase1_running",
    "phase1_completed",
    "phase2_reviewing",
    "phase2_archiving",
    "phase2_completed",
]


def state_path(basedir: Path | str, batch_id: str) -> Path:
    """State-Pfad: basedir/batch_id.state.json"""
    return Path(basedir) / f"{batch_id}.state.json"


def write_state(
    path: Path | str,
    batch_id: str,
    phase: str,
    status: str = "running",
    pause_reason: str | None = None,
) -> None:
    """Schreibt State atomar. Nur Vorwaerts-Transitionen erlaubt."""
    p = Path(path)
    
    # Bestehenden State lesen (falls vorhanden)
    if p.exists():
        try:
            existing = json.loads(p.read_text(encoding="utf-8"))
            old_phase = existing.get("phase", "")
            if old_phase in _PHASE_ORDER and phase in _PHASE_ORDER:
                if _PHASE_ORDER.index(phase) < _PHASE_ORDER.index(old_phase):
                    raise ValueError(f"state_backwards:{old_phase} -> {phase}")
        except (json.JSONDecodeError, OSError):
            pass
    
    now = utcnow()
    data = {
        "schema_version": 1,
        "created_at": now,
        "updated_at": now,
        "producer_version": "7.8.0",
        "batch_id": batch_id,
        "phase": phase,
        "status": status,
    }
    if pause_reason:
        data["pause_reason"] = pause_reason
    
    atomic_json(p, data, "batch_id")


def read_state(path: Path | str) -> dict[str, Any]:
    """Liest State-Datei."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
