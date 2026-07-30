"""Projekt: Synology Photo Workflow
Datei: tests/test_contracts.py
Mitentwickler: MaiTai
Erstellt: 2026-07-29
Projektversion: 7.7.0
Funktion: Synthetische Vertragstests für Score-Renormierung und Metrik-Margenpflicht.
"""
from app.culling import final_score
from app.face_backend import MatchMetric, match_valid


def test_score_renormalizes_missing_components():
    assert final_score({'base_score': .8, 'eye_score': None}, {'base_score': .5, 'eye_score': .5}) == .8


def test_lower_metric_margin():
    assert match_valid(.1, .2, MatchMetric('distance', 'lower_is_better', .15, .05))
