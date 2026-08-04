"""tests/test_face_adapter_yunet_sface_cpu.py

Spezifikation v10.2 - AP6
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
