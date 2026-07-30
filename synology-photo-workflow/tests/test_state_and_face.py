"""Projekt: Synology Photo Workflow
Datei: tests/test_state_and_face.py
Mitentwickler: MaiTai
Erstellt: 2026-07-29
Projektversion: 7.7.0
Funktion: Prüfung des vorwärtigen Zustandsautomaten und Face-Metrikvertrags.
"""
import pytest
from app.batch_state import write_state
from app.face_backend import MatchMetric, match_valid, diagnose


def test_state_transition_cannot_move_backward(tmp_path):
    p = tmp_path / 'batch.json'
    write_state(p, 'x', 'phase2_archiving')
    with pytest.raises(ValueError, match='backwards'):
        write_state(p, 'x', 'phase1_completed')


def test_higher_metric_requires_threshold_and_margin():
    m = MatchMetric('cosine', 'higher_is_better', .95, .03)
    assert match_valid(.98, .94, m)
    assert not match_valid(.96, .94, m)


def test_cuda_without_cuda_profile_is_not_ready():
    assert not diagnose('onnx_face_cuda', 'cpu').ready
