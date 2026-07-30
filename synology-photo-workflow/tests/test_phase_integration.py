"""Projekt: Synology Photo Workflow
Datei: tests/test_phase_integration.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Prüft Phase-1-Manifest, kanonisches CSV und sichtbare Review-Ablage mit synthetischen Medien.
SICHERHEIT: Phase 1 mutiert erst nach Inventarprüfung; Phase 2 bleibt freigabegebunden.
"""
from pathlib import Path
from app.phases import phase1


def config(tmp_path):
    return {
        'paths': {
            'basedir': str(tmp_path),
            'temp_sd': str(tmp_path / 'sd'),
            'temp_images': str(tmp_path / 'images'),
            'temp_done': str(tmp_path / 'done'),
            'workflow_data': str(tmp_path / 'data'),
        },
        'workflow': {'batch_limit': 1},
        'culling': {
            'base_weights': {'sharpness': .4, 'aesthetic': .3, 'exposure': .3, 'reference_score': 0},
            'final_component_weights': {'base_score': 1, 'eye_score': 0, 'personal_score': 0, 'family_score': 0},
            'keep_threshold': .9,
            'reject_threshold': .1,
            'star_rating_bands': [{'min': 0, 'max': 1, 'rating': 3}],
        },
        'metadata': {'write_mode': 'disabled', 'verify_after_write': True},
    }


def test_phase1_creates_manifest_and_canonical_csv(tmp_path):
    batch = tmp_path / 'sd' / 'camera'
    batch.mkdir(parents=True)
    (batch / 'IMG_1.jpg').write_bytes(b'not-a-real-jpeg')
    result = phase1(config(tmp_path))
    target = Path(result[0]['path'])
    assert (target / 'SAVE' / 'phase1_manifest.json').is_file()
    assert (target / 'SAVE' / 'culling_scores.csv').is_file()
    assert (target / 'Review' / 'IMG_1.jpg').is_file()
