"""Projekt: Synology Photo Workflow
Datei: tests/test_face_adapter_yunet_sface_cpu_v77.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Prüft den optionalen YuNet/SFace-CPU-Adapter auf defensive Diagnose und deaktivierten Standardzustand.
SICHERHEIT: Ohne Modelle oder OpenCV-Face-Module darf das Backend nicht als bereit gelten.
"""
from pathlib import Path

from app.face_adapter_yunet_sface_cpu import YuNetSFaceCPUAdapter


def test_optional_adapter_reports_missing_models(tmp_path):
    adapter = YuNetSFaceCPUAdapter(str(tmp_path / 'yunet.onnx'), str(tmp_path / 'sface.onnx'))
    diagnosis = adapter.diagnose()
    assert diagnosis.ready is False
    assert 'model_file_missing' in diagnosis.message or diagnosis.message == 'opencv_not_installed'


def test_placeholder_directories_are_documented():
    root = Path(__file__).parents[1]
    assert (root / 'legacy' / 'README.md').is_file()
    assert (root / 'scripts' / 'README.md').is_file()
