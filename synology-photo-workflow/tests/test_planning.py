"""Projekt: Synology Photo Workflow
Datei: tests/test_planning_v77.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Prüft, dass Dry-Run plant ohne Batchordner oder Steuerdateien anzulegen.
SICHERHEIT: Planung ist strikt lesend; produktive Batch-Schritte sind gelockt und zeitbudgetiert.
"""
from app.planning import plan_phase1


def test_phase1_planner_does_not_mutate_batch(tmp_path):
    batch = tmp_path/'sd'/'camera'; batch.mkdir(parents=True); (batch/'IMG.jpg').write_bytes(b'jpg')
    config = {'paths': {'temp_sd': str(tmp_path/'sd'), 'temp_images': str(tmp_path/'images')}, 'workflow': {'batch_limit': 1}}
    result = plan_phase1(config)
    assert result[0]['status'] == 'ready'
    assert not (batch/'ARW').exists() and not (batch/'SAVE').exists()
