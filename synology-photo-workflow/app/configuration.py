"""app/configuration.py — Konfigurations-Loader, Validierung.

Spezifikation v10.2 - AP5
"""
from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any


def load_config(config_path: Path | str) -> dict[str, Any]:
    """Laedt und validiert Konfiguration."""
    p = Path(config_path)
    config = yaml.safe_load(p.read_text(encoding="utf-8"))
    
    # Pflichtfelder pruefen
    required = ["paths", "workflow", "culling"]
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"config_missing:{sorted(missing)}")
    
    # Alias-Konflikte pruefen
    if "decision_mode" in config.get("culling", {}):
        raise ValueError("culling.decision_mode conflicts with new structure")
    
    # Automation-Gates pruefen
    automation = config.get("automation", {})
    if automation.get("mode") == "automatic_phase2" and not automation.get("automatic_phase2_enabled"):
        raise ValueError("automatic_phase2 gates not all explicit")
    
    return config
