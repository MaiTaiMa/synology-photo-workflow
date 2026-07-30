"""Projekt: Synology Photo Workflow
Datei: tests/test_culling_metadata_v77.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Prüft Renormierung, unbekannte Scores, Seriennachvollziehbarkeit und sichere Metadatentags.
SICHERHEIT: Bildanalyse ist optional, lokal und darf keine Originale verändern.
"""
from app.culling import apply_series, final_score, stars
from app.metadata import build_tags


def test_missing_optional_score_is_renormalized_not_zero():
    score = final_score({'base_score': 0.8, 'eye_score': None}, {'base_score': 0.5, 'eye_score': 0.5})
    assert score == 0.8


def test_unknown_score_has_no_star_rating():
    assert stars(None, [{'min': 0, 'max': 1, 'rating': 5}]) is None


def test_series_fields_are_deterministic_and_explainable():
    records = apply_series([{'relative_path': 'trip_1.jpg', 'final_score': .4}, {'relative_path': 'trip_2.jpg', 'final_score': .8}])
    best = next(item for item in records if item['series_best'])
    assert best['series_rank'] == 1 and best['series_size'] == 2


def test_metadata_does_not_tag_unknown_people():
    tags = build_tags({'predicted_decision': 'keep', 'star_rating': 4, 'family_match': False, 'person_slug': 'unknown'})
    assert not any('person-' in tag for tag in tags['keywords'])
