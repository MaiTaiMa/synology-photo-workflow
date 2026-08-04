"""app/safety.py — Sicherheitsprimitive, atomare JSON- und ZIP-Transaktionen.

Spezifikation v10.2 - AP1
"""
from __future__ import annotations
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SafetyError(Exception):
    """Sicherheitsrelevante Ausnahme (z.B. Hash-Mismatch, Pfad-Traversal)."""
    pass


def sha256(path: Path | str) -> str:
    """Berechnet SHA256-Hash einer Datei."""
    h = hashlib.sha256()
    p = Path(path)
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def utcnow() -> str:
    """Aktueller UTC-Zeitstempel im ISO-8601-Format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def atomic_json(path: Path | str, data: dict[str, Any], id_key: str | None = None) -> None:
    """Schreibt dict als JSON atomar (write-renamepattern).

    Pflichtfelder: schema_version, created_at, updated_at, producer_version
    id_key: optionales Schlusselfeld (z.B. "batch_id") fuer Fehlermeldungen.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    
    # Pflichtfelder pruefen
    required = ["schema_version", "created_at", "updated_at", "producer_version"]
    missing = [k for k in required if k not in data]
    if missing:
        raise SafetyError(f"missing:{sorted(missing)}")
    
    content = json.dumps(data, indent=2, ensure_ascii=False)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.rename(p)


def read_control_json(path: Path | str, id_key: str) -> dict[str, Any]:
    """Liest JSON und validiert auf Pflichtfelder.

    Fehler: 'unreadable:<path>' wenn nicht lesbar oder JSON-invalid.
    """
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
        data = json.loads(text)
        if not isinstance(data, dict):
            raise SafetyError(f"unreadable:{p}")
        return data
    except (OSError, json.JSONDecodeError):
        raise SafetyError(f"unreadable:{p}")


def validate_zip(path: Path | str, entry_hashes: dict[str, str] | None = None) -> None:
    """Validiert ZIP auf Pfad-Traversal und (optional) Hashes.

    entry_hashes: {"relative/path": "sha256", ...} oder None (nur Traversal-Check).
    """
    p = Path(path)
    with zipfile.ZipFile(p, "r") as z:
        for name in z.namelist():
            # Pfad-Traversal verhindern
            if ".." in name.split("/") or name.startswith("/") or name.startswith("\\"):
                raise SafetyError(f"zip_path_traversal:{name}")
            
            # Optional: Hash-Validierung
            if entry_hashes and name in entry_hashes:
                expected = entry_hashes[name]
                actual = sha256(Path(z.extract(name)))  # Extract temp, hash, cleanup
                if expected != actual:
                    raise SafetyError(f"zip_hash_mismatch:{name}")
