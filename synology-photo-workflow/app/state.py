"""
Skript: app/state.py
Zweck: Atomare BatchState-Zustandsverwaltung mit Vorwärts-Validierung und Hash-Integrität.
Autor: MaiTai
Erstellt: 2026-08-08
Version: 1.0.0
Requires: json, hashlib, pathlib, datetime

Änderungsprotokoll:
  2026-08-08 | 1.0.0 | 00AP: Initiale Implementierung gemäß 00AP.md Abschnitt 4.1 und 02AP.md.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from . import VERSION

# ---------------------------------------------------------------------------
# Typdefinitionen: Alle gültigen Batch-Zustände gemäß 00AP.md Abschnitt 7
# ---------------------------------------------------------------------------

StateType = Literal[
    "phase1_started", "phase1_moving", "phase1_completed",
    "review_comparison_pending", "review_record_committed",
    "calibration_index_committed", "automatic_handoff",
    "phase2_archiving", "phase2_completed",
    "phase3_finalization_planned", "phase3_transfer_in_progress",
    "phase3_transferred_to_target", "phase3_index_waiting",
    "phase3_item_resolution_pending", "phase3_api_metadata_pending",
    "phase3_api_metadata_completed", "phase3_publish_disabled",
    "review_state_invalid", "phase3_transfer_failed",
    "phase3_indexing_timeout", "phase3_item_resolution_failed",
    "phase3_api_metadata_partial", "phase3_api_metadata_failed",
    "finalization_state_invalid", "paused", "quarantine",
]

# ---------------------------------------------------------------------------
# Vorwärts-Zustandsreihenfolge für Validierung (nur Normalzustände)
# ---------------------------------------------------------------------------

_STATE_ORDER: dict[str, int] = {
    "phase1_started": 0,
    "phase1_moving": 1,
    "phase1_completed": 2,
    "review_comparison_pending": 3,
    "review_record_committed": 4,
    "calibration_index_committed": 5,
    "automatic_handoff": 6,
    "phase2_archiving": 7,
    "phase2_completed": 8,
    "phase3_finalization_planned": 9,
    "phase3_transfer_in_progress": 10,
    "phase3_transferred_to_target": 11,
    "phase3_index_waiting": 12,
    "phase3_item_resolution_pending": 13,
    "phase3_api_metadata_pending": 14,
    "phase3_api_metadata_completed": 15,
}

# Ausnahmezustände erlauben jederzeit einen Übergang (auch rückwärts)
_EXCEPTION_STATES: frozenset[str] = frozenset({
    "paused", "quarantine", "review_state_invalid",
    "phase3_publish_disabled", "phase3_transfer_failed",
    "phase3_indexing_timeout", "phase3_item_resolution_failed",
    "phase3_api_metadata_partial", "phase3_api_metadata_failed",
    "finalization_state_invalid",
})


# ---------------------------------------------------------------------------
# Datenmodell: BatchState (00AP.md Abschnitt 4.1)
# ---------------------------------------------------------------------------

@dataclass
class BatchState:
    """Atomarer Batch-Zustand gemäß 00AP.md Abschnitt 4.1.

    Enthält alle Pflichtfelder für Audit, Recovery und Integritätsprüfung.
    """

    batch_id: str
    state: str
    timestamp: str       # ISO8601
    hash: str            # SHA256 des serialisierten vorherigen Zustands
    producer_version: str
    config_fingerprint: str
    reason: str | None = None


# ---------------------------------------------------------------------------
# Hilfsfunktionen für Hashing und atomares Schreiben
# ---------------------------------------------------------------------------

def _compute_hash(data: dict) -> str:
    """Berechnet SHA256-Hash des JSON-serialisierten Dicts deterministisch."""
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode()).hexdigest()


def _atomic_write(path: Path, data: dict) -> None:
    """Schreibt JSON-Dict atomar auf gleichem Dateisystem (Temp → Replace)."""
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


# ---------------------------------------------------------------------------
# Kern-API: transition_to, load_state, atomic_write
# ---------------------------------------------------------------------------

def transition_to(
    path: Path,
    batch_id: str,
    new_state: str,
    config_fingerprint: str,
    *,
    reason: str | None = None,
) -> BatchState:
    """Führt einen validierten, atomaren Zustandsübergang durch.

    Liest den vorherigen Zustand, prüft die Vorwärts-Reihenfolge und schreibt
    den neuen Zustand atomar. Rückwärts-Übergänge sind nur in Ausnahmezustände
    erlaubt (z. B. quarantine, paused).
    """
    # Vorherigen Zustand laden für Hash-Verkettung
    previous_data: dict = {}
    if path.exists():
        try:
            previous_data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            previous_data = {}

    # Vorwärts-Validierung: Rückwärts-Übergang nur in Ausnahmezustände erlaubt
    prev_state = previous_data.get("state", "")
    if (
        prev_state in _STATE_ORDER
        and new_state in _STATE_ORDER
        and _STATE_ORDER[new_state] < _STATE_ORDER[prev_state]
        and new_state not in _EXCEPTION_STATES
    ):
        raise ValueError(
            f"invalid_backwards_transition:{prev_state}->{new_state}"
        )

    # Hash des vorherigen Zustands als Verkettungsnachweis
    prev_hash = _compute_hash(previous_data) if previous_data else "genesis"

    now = datetime.now(UTC).isoformat()
    state = BatchState(
        batch_id=batch_id,
        state=new_state,
        timestamp=now,
        hash=prev_hash,
        producer_version=VERSION,
        config_fingerprint=config_fingerprint,
        reason=reason,
    )
    atomic_write(path, state)
    return state


def atomic_write(path: Path, state: BatchState) -> None:
    """Schreibt BatchState atomar als JSON mit allen Pflichtfeldern.

    Entspricht dem Artefaktvertrag aus 00AP.md Abschnitt 4.1 und
    98AP_IMPLEMENTATION_RULES.md Abschnitt 8.3.
    """
    data = {
        "schema_version": "1.0",
        "batch_id": state.batch_id,
        "state": state.state,
        "timestamp": state.timestamp,
        "hash": state.hash,
        "producer_version": state.producer_version,
        "config_fingerprint": state.config_fingerprint,
        "reason": state.reason,
    }
    _atomic_write(path, data)


def load_state(path: Path) -> BatchState | None:
    """Lädt BatchState aus JSON-Datei; gibt None zurück wenn Datei fehlt.

    Wirft ValueError bei ungültigem JSON, damit Aufrufer explizit entscheiden.
    """
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid_state_json:{path}") from exc

    # Pflichtfelder prüfen
    required = {"batch_id", "state", "timestamp", "hash", "producer_version", "config_fingerprint"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"missing_state_fields:{missing}")

    return BatchState(
        batch_id=data["batch_id"],
        state=data["state"],
        timestamp=data["timestamp"],
        hash=data["hash"],
        producer_version=data["producer_version"],
        config_fingerprint=data["config_fingerprint"],
        reason=data.get("reason"),
    )
