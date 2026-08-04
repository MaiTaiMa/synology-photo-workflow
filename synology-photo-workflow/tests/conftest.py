"""tests/conftest.py — Fixtures, write_config.

Spezifikation v10.2 - AP9
"""
from pathlib import Path
import yaml


def write_config(tmp_path: Path, **overrides) -> Path:
    """Erstellt Test-Konfiguration."""
    cfg = {
        "paths": {
            "basedir": str(tmp_path),
            "temp_sd": "TEMP_SD",
            "temp_images": "TEMP_IMAGES",
            "temp_done": "TEMP_DONE",
            "temp_error": "TEMP_ERROR",
            "workflow_data": "WORKFLOW_DATA",
        },
        "workflow": {"batch_limit": 1},
        "culling": {
            "enabled": True,
            "keep_threshold": 0.65,
            "reject_threshold": 0.35,
            "base_weights": {"sharpness": 0.35, "aesthetic": 0.35, "exposure": 0.2, "reference_score": 0.1},
            "final_component_weights": {"base_score": 0.55, "eye_score": 0.1, "personal_score": 0.2, "family_score": 0.15},
            "star_rating_bands": [{"min": 0, "max": 1, "rating": 5}],
        },
        "phase2": {"delete_unneeded_arws_after_verified_archive": True},
        "metadata": {"write_mode": "disabled"},
        "family_recognition": {"enabled": False, "backend": "opencv_yunet_sface_cpu", "execution_profile": "cpu"},
        "automation": {"mode": "assisted_review"},
        "calibration": {"enabled": True},
    }
    for section, values in overrides.items():
        cfg[section].update(values)
    p = Path(tmp_path) / "config.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p
